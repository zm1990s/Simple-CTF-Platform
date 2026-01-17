import os
import json
import zipfile
from io import BytesIO
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_file, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Challenge, Competition, Submission, PlatformSettings
from forms import ChallengeForm, CompetitionForm, ReviewForm, PlatformSettingsForm, ResetPasswordForm

admin_bp = Blueprint('admin', __name__)

# Load translations
def _(text):
    """Get translated text based on current locale"""
    try:
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        with open(os.path.join(basedir, 'translations.json'), 'r', encoding='utf-8') as f:
            translations = json.load(f)
        locale = session.get('locale', 'en')
        if text in translations and locale in translations[text]:
            return translations[text][locale]
    except:
        pass
    return text


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('frontend.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    stats = {
        'total_users': User.query.count(),
        'total_competitions': Competition.query.count(),
        'total_challenges': Challenge.query.count(),
        'pending_submissions': Submission.query.filter_by(status='pending').count()
    }
    return render_template('admin/dashboard.html', stats=stats)


# Platform Settings
@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Platform settings"""
    form = PlatformSettingsForm()
    
    if form.validate_on_submit():
        # Update platform name
        setting = PlatformSettings.query.filter_by(key='platform_name').first()
        if setting:
            setting.value = form.platform_name.data
        else:
            setting = PlatformSettings(key='platform_name', value=form.platform_name.data)
            db.session.add(setting)
        
        # Handle logo upload
        if form.platform_logo.data:
            file = form.platform_logo.data
            filename = secure_filename(file.filename)
            # Save to static folder so it can be served directly
            static_folder = os.path.join(current_app.root_path, 'static')
            filepath = os.path.join(static_folder, filename)
            file.save(filepath)
            
            logo_setting = PlatformSettings.query.filter_by(key='platform_logo').first()
            if logo_setting:
                logo_setting.value = filename
            else:
                logo_setting = PlatformSettings(key='platform_logo', value=filename)
                db.session.add(logo_setting)
        
        # Update footer text
        if form.footer_text.data:
            footer_setting = PlatformSettings.query.filter_by(key='footer_text').first()
            if footer_setting:
                footer_setting.value = form.footer_text.data
            else:
                footer_setting = PlatformSettings(key='footer_text', value=form.footer_text.data)
                db.session.add(footer_setting)
        
        db.session.commit()
        flash('Platform settings updated successfully.', 'success')
        return redirect(url_for('admin.settings'))
    
    # Load current settings
    platform_name = PlatformSettings.query.filter_by(key='platform_name').first()
    platform_logo = PlatformSettings.query.filter_by(key='platform_logo').first()
    footer_text = PlatformSettings.query.filter_by(key='footer_text').first()
    
    if platform_name:
        form.platform_name.data = platform_name.value
    
    if footer_text:
        form.footer_text.data = footer_text.value
    
    return render_template('admin/settings.html', 
                         form=form,
                         current_platform_name=platform_name.value if platform_name else None,
                         current_logo=platform_logo.value if platform_logo else None,
                         current_footer_text=footer_text.value if footer_text else None)


# Competition Management
@admin_bp.route('/competitions')
@admin_required
def competitions():
    """List all competitions"""
    competitions = Competition.query.order_by(Competition.created_at.desc()).all()
    return render_template('admin/competitions.html', competitions=competitions)


@admin_bp.route('/competitions/new', methods=['GET', 'POST'])
@admin_required
def competition_new():
    """Create new competition"""
    form = CompetitionForm()
    
    if form.validate_on_submit():
        competition = Competition(
            name=form.name.data,
            description=form.description.data,
            countdown_minutes=form.countdown_minutes.data or 0,
            status='draft'
        )
        db.session.add(competition)
        db.session.commit()
        
        flash('Competition created successfully.', 'success')
        return redirect(url_for('admin.competitions'))
    
    return render_template('admin/competition_form.html', form=form, title=_('New Competition'))


@admin_bp.route('/competitions/<int:competition_id>/edit', methods=['GET', 'POST'])
@admin_required
def competition_edit(competition_id):
    """Edit competition"""
    competition = Competition.query.get_or_404(competition_id)
    form = CompetitionForm(obj=competition)
    
    if form.validate_on_submit():
        competition.name = form.name.data
        competition.description = form.description.data
        competition.countdown_minutes = form.countdown_minutes.data or 0
        
        db.session.commit()
        flash('Competition updated successfully.', 'success')
        return redirect(url_for('admin.competitions'))
    
    return render_template('admin/competition_form.html', form=form, title=_('Edit Competition'))


@admin_bp.route('/competitions/<int:competition_id>/delete', methods=['POST'])
@admin_required
def competition_delete(competition_id):
    """Delete competition"""
    competition = Competition.query.get_or_404(competition_id)
    db.session.delete(competition)
    db.session.commit()
    
    flash('Competition deleted successfully.', 'success')
    return redirect(url_for('admin.competitions'))


@admin_bp.route('/competitions/<int:competition_id>/start', methods=['POST'])
@admin_required
def competition_start(competition_id):
    """Start competition"""
    competition = Competition.query.get_or_404(competition_id)
    competition.status = 'running'
    if competition.countdown_minutes > 0:
        competition.countdown_started_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Competition "{competition.name}" started successfully.', 'success')
    return redirect(url_for('admin.competitions'))


@admin_bp.route('/competitions/<int:competition_id>/pause', methods=['POST'])
@admin_required
def competition_pause(competition_id):
    """Pause competition"""
    competition = Competition.query.get_or_404(competition_id)
    if competition.status == 'running':
        competition.status = 'paused'
        flash(f'Competition "{competition.name}" paused.', 'warning')
    elif competition.status == 'paused':
        competition.status = 'running'
        flash(f'Competition "{competition.name}" resumed.', 'success')
    db.session.commit()
    return redirect(url_for('admin.competitions'))


@admin_bp.route('/competitions/<int:competition_id>/stop', methods=['POST'])
@admin_required
def competition_stop(competition_id):
    """Stop competition"""
    competition = Competition.query.get_or_404(competition_id)
    competition.status = 'stopped'
    db.session.commit()
    
    flash(f'Competition "{competition.name}" stopped.', 'info')
    return redirect(url_for('admin.competitions'))


@admin_bp.route('/competitions/<int:competition_id>/reset', methods=['POST'])
@admin_required
def competition_reset(competition_id):
    """Reset competition - archive all submissions to history and set status to draft"""
    competition = Competition.query.get_or_404(competition_id)
    
    # Archive all submissions for this competition's challenges
    challenge_ids = [c.id for c in competition.challenges]
    if challenge_ids:
        from models import SubmissionFile, SubmissionHistory, SubmissionFileHistory
        submissions = Submission.query.filter(Submission.challenge_id.in_(challenge_ids)).all()
        
        archived_count = 0
        for submission in submissions:
            # Create history record
            history = SubmissionHistory(
                original_submission_id=submission.id,
                answer_text=submission.answer_text,
                status=submission.status,
                points_awarded=submission.points_awarded,
                submitted_at=submission.submitted_at,
                reviewed_at=submission.reviewed_at,
                user_id=submission.user_id,
                challenge_id=submission.challenge_id,
                competition_id=competition_id,
                reviewed_by_id=submission.reviewed_by_id
            )
            db.session.add(history)
            db.session.flush()  # Get history ID
            
            # Archive associated files
            for file in submission.files:
                file_history = SubmissionFileHistory(
                    original_file_id=file.id,
                    filename=file.filename,
                    filepath=file.filepath,
                    uploaded_at=file.uploaded_at,
                    submission_history_id=history.id
                )
                db.session.add(file_history)
                db.session.delete(file)
            
            db.session.delete(submission)
            archived_count += 1
    
    # Reset competition status
    competition.status = 'draft'
    competition.countdown_started_at = None
    
    db.session.commit()
    flash(f'Competition "{competition.name}" has been reset. {archived_count} submissions archived to history.', 'success')
    return redirect(url_for('admin.competitions'))


@admin_bp.route('/competitions/<int:competition_id>/duplicate', methods=['POST'])
@admin_required
def competition_duplicate(competition_id):
    """Duplicate competition with all challenges"""
    original = Competition.query.get_or_404(competition_id)
    
    # Create new competition
    new_competition = Competition(
        name=f"{original.name} (Copy)",
        description=original.description,
        countdown_minutes=original.countdown_minutes,
        status='draft'
    )
    db.session.add(new_competition)
    db.session.flush()  # Get new competition ID
    
    # Duplicate all challenges
    for challenge in original.challenges:
        new_challenge = Challenge(
            title=challenge.title,
            description=challenge.description,
            points=challenge.points,
            category=challenge.category,
            competition_id=new_competition.id,
            is_active=challenge.is_active
        )
        db.session.add(new_challenge)
    
    db.session.commit()
    flash(f'Competition duplicated as "{new_competition.name}".', 'success')
    return redirect(url_for('admin.competitions'))


@admin_bp.route('/competitions/<int:competition_id>/export')
@admin_required
def competition_export(competition_id):
    """Export competition with all challenges as JSON/ZIP"""
    competition = Competition.query.get_or_404(competition_id)
    
    # Prepare competition data
    competition_data = {
        'name': competition.name,
        'description': competition.description,
        'countdown_minutes': competition.countdown_minutes,
        'export_date': datetime.utcnow().isoformat(),
        'challenges': []
    }
    
    # Add all challenges
    for challenge in competition.challenges:
        challenge_data = {
            'title': challenge.title,
            'description': challenge.description,
            'points': challenge.points,
            'category': challenge.category,
            'is_active': challenge.is_active
        }
        competition_data['challenges'].append(challenge_data)
    
    # Create JSON file
    json_data = json.dumps(competition_data, indent=2, ensure_ascii=False)
    
    # Create a BytesIO object to hold the file
    buffer = BytesIO()
    buffer.write(json_data.encode('utf-8'))
    buffer.seek(0)
    
    # Generate filename
    filename = f"{secure_filename(competition.name)}_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )


@admin_bp.route('/competitions/import', methods=['GET', 'POST'])
@admin_required
def competition_import():
    """Import competition from JSON file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded.', 'danger')
            return redirect(url_for('admin.competition_import'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('admin.competition_import'))
        
        if not file.filename.endswith('.json'):
            flash('Please upload a JSON file.', 'danger')
            return redirect(url_for('admin.competition_import'))
        
        try:
            # Read and parse JSON
            data = json.load(file)
            
            # Validate required fields
            if 'name' not in data or 'challenges' not in data:
                flash('Invalid import file format.', 'danger')
                return redirect(url_for('admin.competition_import'))
            
            # Create competition
            competition = Competition(
                name=data['name'],
                description=data.get('description', ''),
                countdown_minutes=data.get('countdown_minutes', 0),
                status='draft'
            )
            db.session.add(competition)
            db.session.flush()  # Get competition ID
            
            # Create challenges
            challenge_count = 0
            for challenge_data in data['challenges']:
                challenge = Challenge(
                    title=challenge_data['title'],
                    description=challenge_data['description'],
                    points=challenge_data.get('points', 100),
                    category=challenge_data.get('category', ''),
                    competition_id=competition.id,
                    is_active=challenge_data.get('is_active', True)
                )
                db.session.add(challenge)
                challenge_count += 1
            
            db.session.commit()
            flash(f'Competition "{competition.name}" imported successfully with {challenge_count} challenges.', 'success')
            return redirect(url_for('admin.competitions'))
            
        except json.JSONDecodeError:
            flash('Invalid JSON file.', 'danger')
            return redirect(url_for('admin.competition_import'))
        except Exception as e:
            db.session.rollback()
            flash(f'Import failed: {str(e)}', 'danger')
            return redirect(url_for('admin.competition_import'))
    
    return render_template('admin/competition_import.html')


@admin_bp.route('/challenges/<int:challenge_id>/export')
@admin_required
def challenge_export(challenge_id):
    """Export single challenge as JSON"""
    challenge = Challenge.query.get_or_404(challenge_id)
    
    challenge_data = {
        'title': challenge.title,
        'description': challenge.description,
        'points': challenge.points,
        'category': challenge.category,
        'is_active': challenge.is_active,
        'competition_name': challenge.competition.name,
        'export_date': datetime.utcnow().isoformat()
    }
    
    # Create JSON file
    json_data = json.dumps(challenge_data, indent=2, ensure_ascii=False)
    buffer = BytesIO()
    buffer.write(json_data.encode('utf-8'))
    buffer.seek(0)
    
    filename = f"{secure_filename(challenge.title)}_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )


@admin_bp.route('/competitions/export-all')
@admin_required
def competitions_export_all():
    """Export all competitions as a ZIP file"""
    competitions = Competition.query.all()
    
    if not competitions:
        flash('No competitions to export.', 'warning')
        return redirect(url_for('admin.competitions'))
    
    # Create a ZIP file in memory
    buffer = BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for competition in competitions:
            # Prepare competition data
            competition_data = {
                'name': competition.name,
                'description': competition.description,
                'countdown_minutes': competition.countdown_minutes,
                'export_date': datetime.utcnow().isoformat(),
                'challenges': []
            }
            
            # Add all challenges
            for challenge in competition.challenges:
                challenge_data = {
                    'title': challenge.title,
                    'description': challenge.description,
                    'points': challenge.points,
                    'category': challenge.category,
                    'is_active': challenge.is_active
                }
                competition_data['challenges'].append(challenge_data)
            
            # Add to ZIP
            json_data = json.dumps(competition_data, indent=2, ensure_ascii=False)
            filename = f"{secure_filename(competition.name)}.json"
            zipf.writestr(filename, json_data)
    
    buffer.seek(0)
    filename = f"all_competitions_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/zip'
    )


# Challenge Management
@admin_bp.route('/challenges')
@admin_required
def challenges():
    """List all challenges"""
    challenges = Challenge.query.order_by(Challenge.created_at.desc()).all()
    return render_template('admin/challenges.html', challenges=challenges)


@admin_bp.route('/challenges/new', methods=['GET', 'POST'])
@admin_required
def challenge_new():
    """Create new challenge"""
    form = ChallengeForm()
    form.competition_id.choices = [(c.id, c.name) for c in Competition.query.all()]
    
    if form.validate_on_submit():
        challenge = Challenge(
            title=form.title.data,
            description=form.description.data,
            points=form.points.data,
            category=form.category.data,
            competition_id=form.competition_id.data
        )
        db.session.add(challenge)
        db.session.commit()
        
        flash('Challenge created successfully.', 'success')
        return redirect(url_for('admin.challenges'))
    
    return render_template('admin/challenge_form.html', form=form, title=_('New Challenge'))


@admin_bp.route('/challenges/<int:challenge_id>/edit', methods=['GET', 'POST'])
@admin_required
def challenge_edit(challenge_id):
    """Edit challenge"""
    challenge = Challenge.query.get_or_404(challenge_id)
    form = ChallengeForm(obj=challenge)
    form.competition_id.choices = [(c.id, c.name) for c in Competition.query.all()]
    
    if form.validate_on_submit():
        challenge.title = form.title.data
        challenge.description = form.description.data
        challenge.points = form.points.data
        challenge.category = form.category.data
        challenge.competition_id = form.competition_id.data
        
        db.session.commit()
        flash('Challenge updated successfully.', 'success')
        return redirect(url_for('admin.challenges'))
    
    return render_template('admin/challenge_form.html', form=form, title=_('Edit Challenge'), challenge=challenge)


@admin_bp.route('/challenges/<int:challenge_id>/delete', methods=['POST'])
@admin_required
def challenge_delete(challenge_id):
    """Delete challenge"""
    challenge = Challenge.query.get_or_404(challenge_id)
    db.session.delete(challenge)
    db.session.commit()
    
    flash('Challenge deleted successfully.', 'success')
    return redirect(url_for('admin.challenges'))


@admin_bp.route('/challenges/<int:challenge_id>/toggle', methods=['POST'])
@admin_required
def challenge_toggle(challenge_id):
    """Toggle challenge active status"""
    challenge = Challenge.query.get_or_404(challenge_id)
    challenge.is_active = not challenge.is_active
    db.session.commit()
    
    status = 'activated' if challenge.is_active else 'deactivated'
    flash(f'Challenge {status} successfully.', 'success')
    return redirect(url_for('admin.challenges'))


@admin_bp.route('/challenges/<int:challenge_id>/copy', methods=['POST'])
@admin_required
def challenge_copy(challenge_id):
    """Copy/duplicate a challenge"""
    original = Challenge.query.get_or_404(challenge_id)
    
    # Create a copy with a modified title
    copy_number = 1
    new_title = f"{original.title} (Copy {copy_number})"
    
    # Check if a copy with this title already exists, increment number if needed
    while Challenge.query.filter_by(title=new_title).first():
        copy_number += 1
        new_title = f"{original.title} (Copy {copy_number})"
    
    new_challenge = Challenge(
        title=new_title,
        description=original.description,
        points=original.points,
        category=original.category,
        competition_id=original.competition_id,
        is_active=False  # Set copied challenges as inactive by default
    )
    
    db.session.add(new_challenge)
    db.session.commit()
    
    flash(f'Challenge copied successfully as "{new_title}".', 'success')
    return redirect(url_for('admin.challenges'))


# Image upload for markdown editor
@admin_bp.route('/upload-image', methods=['POST'])
@admin_required
def upload_image():
    """Upload image for markdown editor"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and '.' in file.filename and \
       file.filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}:
        filename = secure_filename(file.filename)
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"challenge_{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(filepath)
        
        # Return URL for markdown insertion
        file_url = url_for('uploaded_file', filename=unique_filename)
        return jsonify({'url': file_url})
    
    return jsonify({'error': 'Invalid file type'}), 400


# Submission Review
@admin_bp.route('/submissions')
@admin_required
def submissions():
    """List all submissions"""
    status_filter = request.args.get('status', 'pending')
    
    query = Submission.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    submissions = query.order_by(Submission.submitted_at.desc()).all()
    return render_template('admin/submissions.html', submissions=submissions, status_filter=status_filter)


@admin_bp.route('/submissions/<int:submission_id>/review', methods=['GET', 'POST'])
@admin_required
def submission_review(submission_id):
    """Review submission"""
    submission = Submission.query.get_or_404(submission_id)
    form = ReviewForm()
    
    if form.validate_on_submit():
        from datetime import datetime
        
        submission.status = form.status.data
        submission.reviewed_at = datetime.utcnow()
        submission.reviewed_by_id = current_user.id
        
        if form.status.data == 'approved':
            # Award points
            points = form.points_awarded.data or submission.challenge.points
            submission.points_awarded = points
        else:
            submission.points_awarded = 0
        
        db.session.commit()
        flash('Submission reviewed successfully.', 'success')
        return redirect(url_for('admin.submissions'))
    
    # Set default points
    form.points_awarded.data = submission.challenge.points
    
    return render_template('admin/submission_review.html', submission=submission, form=form)


# User Management
@admin_bp.route('/users')
@admin_required
def users():
    """List all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def user_toggle_admin(user_id):
    """Toggle user admin status"""
    user = User.query.get_or_404(user_id)
    
    # Prevent removing own admin status
    if user.id == current_user.id:
        flash('You cannot modify your own admin status.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    status = 'granted' if user.is_admin else 'revoked'
    flash(f'Admin privileges {status} for user {user.username}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@admin_required
def user_reset_password(user_id):
    """Reset user password"""
    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        
        flash(f'Password reset successfully for user {user.username}.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/reset_password.html', user=user, form=form)


@admin_bp.route('/submission-history')
@admin_required
def submission_history():
    """View archived submissions from competition resets"""
    from models import SubmissionHistory
    
    # Get filter parameters
    competition_id = request.args.get('competition_id', type=int)
    user_id = request.args.get('user_id', type=int)
    
    # Build query
    query = SubmissionHistory.query
    
    if competition_id:
        query = query.filter_by(competition_id=competition_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    # Order by archived date, newest first
    history = query.order_by(SubmissionHistory.archived_at.desc()).all()
    
    # Get all competitions for filter dropdown
    competitions = Competition.query.order_by(Competition.name).all()
    
    return render_template('admin/submission_history.html', 
                         history=history, 
                         competitions=competitions,
                         selected_competition=competition_id)


@admin_bp.route('/submission-history/<int:history_id>')
@admin_required
def submission_history_detail(history_id):
    """View details of an archived submission"""
    from models import SubmissionHistory
    
    history = SubmissionHistory.query.get_or_404(history_id)
    return render_template('admin/submission_history_detail.html', submission=history)
