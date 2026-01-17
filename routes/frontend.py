import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Challenge, Competition, Submission, SubmissionFile
from forms import SubmissionForm

frontend_bp = Blueprint('frontend', __name__)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


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
    challenges = Challenge.query.filter_by(competition_id=competition_id, is_active=True).all()
    
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
    if not competition.is_running():
        flash('This competition is not currently active.', 'warning')
        return redirect(url_for('frontend.competition_detail', competition_id=competition.id))
    
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
        # Double-check countdown hasn't expired during form submission
        remaining_time = competition.get_remaining_time()
        if remaining_time is not None and remaining_time <= 0:
            competition.status = 'paused'
            db.session.commit()
            flash('The competition countdown has expired. Your submission cannot be accepted.', 'warning')
            return redirect(url_for('frontend.competition_detail', competition_id=competition.id))
        
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
        
        # Trigger external hook if enabled
        if current_app.config['EXTERNAL_HOOK_ENABLED']:
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


@frontend_bp.route('/leaderboard/<int:competition_id>')
def leaderboard(competition_id):
    """Competition leaderboard"""
    competition = Competition.query.get_or_404(competition_id)
    
    # Calculate scores for all users
    # Strategy: For each user-challenge pair, only count the highest score
    from sqlalchemy import func
    
    # Subquery to get max score per user per challenge
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
    
    # Sum the max scores per user
    scores = db.session.query(
        max_scores_subquery.c.user_id,
        func.sum(max_scores_subquery.c.max_points).label('total_points')
    ).group_by(
        max_scores_subquery.c.user_id
    ).subquery()
    
    # Get last solve time for each user
    last_solve_subquery = db.session.query(
        Submission.user_id,
        func.max(Submission.reviewed_at).label('last_solve_time')
    ).join(Challenge).filter(
        Challenge.competition_id == competition_id,
        Submission.status == 'approved'
    ).group_by(Submission.user_id).subquery()
    
    # Join to get final leaderboard with ranking
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
    
    # Get user details
    from models import User
    leaderboard_data = []
    for rank, (user_id, total_points, last_solve_time) in enumerate(results, 1):
        user = User.query.get(user_id)
        leaderboard_data.append({
            'rank': rank,
            'user': user,
            'total_points': int(total_points or 0),
            'last_solve_time': last_solve_time
        })
    
    return render_template('frontend/leaderboard.html', 
                         competition=competition,
                         leaderboard=leaderboard_data)


@frontend_bp.route('/my-submissions')
@login_required
def my_submissions():
    """User's submission history"""
    submissions = Submission.query.filter_by(user_id=current_user.id).order_by(
        Submission.submitted_at.desc()
    ).all()
    
    return render_template('frontend/my_submissions.html', submissions=submissions)
