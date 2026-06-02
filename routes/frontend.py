import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Challenge, Competition, Submission, SubmissionFile, CompetitionAccess, Team, TeamMember
from forms import SubmissionForm

frontend_bp = Blueprint('frontend', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def has_pin_access(user_id, competition_id):
    """Return True if the user has already unlocked this competition via PIN."""
    return CompetitionAccess.query.filter_by(
        user_id=user_id,
        competition_id=competition_id
    ).first() is not None


@frontend_bp.route('/')
def index():
    """Homepage - show running and paused competitions"""
    competitions = Competition.query.filter(Competition.status.in_(['running', 'paused'])).order_by(Competition.created_at.desc()).all()
    return render_template('frontend/index.html', competitions=competitions)


@frontend_bp.route('/competition/<int:competition_id>')
@login_required
def competition_detail(competition_id):
    """Competition detail page with challenges"""
    competition = Competition.query.get_or_404(competition_id)
    # Check if competition is accessible (unless user is admin)
    if competition.status not in ['running', 'paused'] and not current_user.is_admin:
        flash('This competition is not available.', 'warning')
        return redirect(url_for('frontend.index'))
    if competition.status == 'paused' and not current_user.is_admin:
        flash('This competition is currently paused.', 'warning')
        return redirect(url_for('frontend.index'))
    # Check PIN access (skip for admins)
    if not current_user.is_admin and not has_pin_access(current_user.id, competition_id):
        return redirect(url_for('frontend.pin_entry', competition_id=competition_id))
    challenges = Challenge.query.filter_by(competition_id=competition_id, is_active=True).order_by(Challenge.order_index.asc(), Challenge.id.asc()).all()
    
    # Get user's submissions for this competition
    user_submissions = {}
    for challenge in challenges:
        submission = Submission.query.filter_by(
            user_id=current_user.id,
            challenge_id=challenge.id
        ).order_by(Submission.submitted_at.desc()).first()
        if submission:
            user_submissions[challenge.id] = submission
    
    return render_template('frontend/competition.html', 
                         competition=competition, 
                         challenges=challenges,
                         user_submissions=user_submissions)


@frontend_bp.route('/challenge/<int:challenge_id>', methods=['GET', 'POST'])
@login_required
def challenge_detail(challenge_id):
    """Challenge detail page with submission form"""
    challenge = Challenge.query.get_or_404(challenge_id)
    competition = challenge.competition

    # Check if competition is running
    if not competition.is_running() and not current_user.is_admin:
        flash('This competition is not currently active.', 'warning')
        return redirect(url_for('frontend.competition_detail', competition_id=competition.id))
    # Check PIN access (skip for admins)
    if not current_user.is_admin and not has_pin_access(current_user.id, competition.id):
        return redirect(url_for('frontend.pin_entry', competition_id=competition.id))

    # Check if countdown has expired
    remaining_time = competition.get_remaining_time()
    if remaining_time is not None and remaining_time <= 0:
        # Auto-pause the competition
        competition.status = 'paused'
        db.session.commit()
        flash('The competition countdown has expired. Submissions are no longer accepted.', 'warning')
        return redirect(url_for('frontend.competition_detail', competition_id=competition.id))

    form = SubmissionForm()

    if form.validate_on_submit():
        
        # Create submission
        submission = Submission(
            user_id=current_user.id,
            challenge_id=challenge_id,
            answer_text=form.answer_text.data,
            status='pending'
        )
        db.session.add(submission)
        db.session.flush()  # Get submission ID
        
        # Handle file uploads
        files = request.files.getlist('files')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create unique filename
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{submission.id}_{timestamp}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(filepath)
                
                # Save file record
                submission_file = SubmissionFile(
                    submission_id=submission.id,
                    filename=filename,
                    filepath=unique_filename
                )
                db.session.add(submission_file)
        
        db.session.commit()
        
        # Trigger external hook if enabled globally or for this challenge.
        has_challenge_dify = bool(challenge.dify_config and challenge.dify_config.enabled)
        if current_app.config['EXTERNAL_HOOK_ENABLED'] or has_challenge_dify:
            from tasks import trigger_external_hook
            trigger_external_hook.delay(submission.id)
        
        flash('Your submission has been received and is pending review.', 'success')
        return redirect(url_for('frontend.challenge_detail', challenge_id=challenge_id))
    
    # Get user's previous submissions
    submissions = Submission.query.filter_by(
        user_id=current_user.id,
        challenge_id=challenge_id
    ).order_by(Submission.submitted_at.desc()).all()
    
    return render_template('frontend/challenge.html', 
                         challenge=challenge, 
                         competition=competition,
                         form=form,
                         submissions=submissions)


@frontend_bp.route('/competition/<int:competition_id>/pin', methods=['GET', 'POST'])
@login_required
def pin_entry(competition_id):
    """PIN entry page for a competition"""
    competition = Competition.query.get_or_404(competition_id)

    if competition.status not in ['running', 'paused'] and not current_user.is_admin:
        flash('This competition is not available.', 'warning')
        return redirect(url_for('frontend.index'))

    # Already has access – skip PIN page
    if current_user.is_admin or has_pin_access(current_user.id, competition_id):
        return redirect(url_for('frontend.competition_detail', competition_id=competition_id))

    if request.method == 'POST':
        entered_pin = request.form.get('pin', '').strip()
        if entered_pin == competition.pin:
            access = CompetitionAccess(
                user_id=current_user.id,
                competition_id=competition_id
            )
            db.session.add(access)
            db.session.commit()
            flash('Access granted! Welcome to the competition.', 'success')
            return redirect(url_for('frontend.competition_detail', competition_id=competition_id))
        else:
            flash('Incorrect PIN. Please try again.', 'danger')

    return render_template('frontend/pin_entry.html', competition=competition)


@frontend_bp.route('/leaderboard/<int:competition_id>')
def leaderboard(competition_id):
    """Competition leaderboard — individual and team views."""
    competition = Competition.query.get_or_404(competition_id)

    # ── Individual leaderboard ──────────────────────────────────────────────
    from sqlalchemy import func
    from collections import defaultdict

    max_scores_subquery = db.session.query(
        Submission.user_id,
        Submission.challenge_id,
        func.max(Submission.points_awarded).label('max_points')
    ).join(Challenge).filter(
        Challenge.competition_id == competition_id,
        Submission.status == 'approved'
    ).group_by(
        Submission.user_id,
        Submission.challenge_id
    ).subquery()

    scores = db.session.query(
        max_scores_subquery.c.user_id,
        func.sum(max_scores_subquery.c.max_points).label('total_points')
    ).group_by(
        max_scores_subquery.c.user_id
    ).subquery()

    last_solve_subquery = db.session.query(
        Submission.user_id,
        func.max(Submission.reviewed_at).label('last_solve_time')
    ).join(Challenge).filter(
        Challenge.competition_id == competition_id,
        Submission.status == 'approved'
    ).group_by(Submission.user_id).subquery()

    results = db.session.query(
        scores.c.user_id,
        scores.c.total_points,
        last_solve_subquery.c.last_solve_time
    ).join(
        last_solve_subquery,
        scores.c.user_id == last_solve_subquery.c.user_id
    ).order_by(
        scores.c.total_points.desc(),
        last_solve_subquery.c.last_solve_time.asc()
    ).all()

    from models import User
    # Build a map: user_id → team
    all_memberships = TeamMember.query.all()
    user_to_team = {m.user_id: m.team for m in all_memberships}
    team_user_ids = set(user_to_team.keys())

    leaderboard_data = []
    rank = 1
    for (user_id, total_points, last_solve_time) in results:
        if user_id in team_user_ids:
            continue  # skip users who are in a team
        user = User.query.get(user_id)
        leaderboard_data.append({
            'rank': rank,
            'user': user,
            'total_points': int(total_points or 0),
            'last_solve_time': last_solve_time,
            'team': None,
        })
        rank += 1

    # ── Team leaderboard ────────────────────────────────────────────────────
    # Per team per challenge: take the best score from any member (deduplication).
    team_challenge_rows = db.session.query(
        TeamMember.team_id,
        Submission.challenge_id,
        func.max(Submission.points_awarded).label('max_points'),
        func.max(Submission.reviewed_at).label('last_solve')
    ).join(
        Submission, Submission.user_id == TeamMember.user_id
    ).join(
        Challenge, Challenge.id == Submission.challenge_id
    ).filter(
        Challenge.competition_id == competition_id,
        Submission.status == 'approved'
    ).group_by(
        TeamMember.team_id,
        Submission.challenge_id
    ).all()

    team_totals = defaultdict(int)
    team_last_solve = defaultdict(lambda: None)
    for row in team_challenge_rows:
        team_totals[row.team_id] += row.max_points
        if team_last_solve[row.team_id] is None or (
            row.last_solve and row.last_solve > team_last_solve[row.team_id]
        ):
            team_last_solve[row.team_id] = row.last_solve

    team_leaderboard = []
    for team_id, total_points in sorted(
        team_totals.items(),
        key=lambda x: (-x[1], team_last_solve[x[0]] or datetime.min)
    ):
        team = Team.query.get(team_id)
        if team:
            team_leaderboard.append({
                'team': team,
                'total_points': total_points,
                'last_solve_time': team_last_solve[team_id],
                'member_count': team.members.count(),
            })

    for i, entry in enumerate(team_leaderboard, 1):
        entry['rank'] = i

    return render_template('frontend/leaderboard.html',
                           competition=competition,
                           leaderboard=leaderboard_data,
                           team_leaderboard=team_leaderboard)


@frontend_bp.route('/leaderboard/<int:competition_id>/team/<int:team_id>')
def team_leaderboard_detail(competition_id, team_id):
    """Team breakdown in leaderboard context."""
    competition = Competition.query.get_or_404(competition_id)
    team = Team.query.get_or_404(team_id)

    from sqlalchemy import func
    from collections import defaultdict

    members = TeamMember.query.filter_by(team_id=team_id).order_by(TeamMember.joined_at).all()

    # Per team per challenge: best score (for team total calculation)
    challenge_best = defaultdict(int)
    team_challenge_rows = db.session.query(
        Submission.challenge_id,
        func.max(Submission.points_awarded).label('max_points')
    ).join(
        TeamMember, TeamMember.user_id == Submission.user_id
    ).join(
        Challenge, Challenge.id == Submission.challenge_id
    ).filter(
        TeamMember.team_id == team_id,
        Challenge.competition_id == competition_id,
        Submission.status == 'approved'
    ).group_by(Submission.challenge_id).all()

    for row in team_challenge_rows:
        challenge_best[row.challenge_id] = row.max_points

    team_total = sum(challenge_best.values())

    # Per-member individual stats
    member_data = []
    for membership in members:
        user = membership.user
        user_rows = db.session.query(
            Submission.challenge_id,
            Challenge.title,
            func.max(Submission.points_awarded).label('max_points')
        ).join(
            Challenge, Challenge.id == Submission.challenge_id
        ).filter(
            Challenge.competition_id == competition_id,
            Submission.status == 'approved',
            Submission.user_id == user.id
        ).group_by(Submission.challenge_id, Challenge.title).all()

        individual_total = sum(r.max_points for r in user_rows)
        member_data.append({
            'user': user,
            'individual_total': individual_total,
            'challenges': [{'challenge_id': r.challenge_id,
                            'title': r.title,
                            'points': r.max_points} for r in user_rows],
            'is_captain': (user.id == team.captain_id),
        })

    member_data.sort(key=lambda x: -x['individual_total'])

    return render_template('frontend/team_leaderboard_detail.html',
                           competition=competition,
                           team=team,
                           members=member_data,
                           team_total=team_total)


@frontend_bp.route('/my-submissions')
@login_required
def my_submissions():
    """User's submission history"""
    submissions = Submission.query.filter_by(user_id=current_user.id).order_by(
        Submission.submitted_at.desc()
    ).all()
    
    return render_template('frontend/my_submissions.html', submissions=submissions)


@frontend_bp.route('/my-submissions/<int:submission_id>')
@login_required
def my_submission_detail(submission_id):
    """User's submission detail view"""
    submission = Submission.query.get_or_404(submission_id)
    if submission.user_id != current_user.id:
        abort(403)
    return render_template('frontend/my_submission_detail.html', submission=submission)
