import os
import sys
import json
import requests
from celery import Celery
from datetime import datetime
from dify_secrets import reveal_api_key

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Initialize Celery
celery = Celery('ctf_platform')

# Configure Celery to use Redis
celery.conf.update(
    broker_url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


def _build_hook_url(challenge, app):
    """Return challenge-specific hook URL if enabled, otherwise global hook URL."""
    challenge_cfg = getattr(challenge, 'dify_config', None)
    if challenge_cfg and challenge_cfg.enabled and (challenge_cfg.base_url or '').strip():
        return challenge_cfg.base_url.strip()

    return (app.config.get('EXTERNAL_HOOK_URL') or '').strip()


def _resolve_api_key(challenge, app):
    """Resolve API key with challenge-level override and global fallback."""
    global_api_key = app.config.get('DIFY_API_KEY', '')
    challenge_cfg = getattr(challenge, 'dify_config', None)
    challenge_credential = getattr(challenge, 'dify_credential', None)

    if challenge_cfg and challenge_cfg.enabled and challenge_credential and (challenge_credential.api_key_token or '').strip():
        revealed = reveal_api_key(challenge_credential.api_key_token, app.config.get('SECRET_KEY', ''))
        if revealed:
            return revealed

    return global_api_key


@celery.task
def trigger_external_hook(submission_id):
    """Trigger Dify workflow for automated submission review and scoring"""
    from app import create_app
    from models import Submission, Challenge, User, SubmissionFile, SubmissionDifyLog, db
    
    app = create_app()
    with app.app_context():
        submission = Submission.query.get(submission_id)
        if not submission:
            return {'error': 'Submission not found'}
        
        challenge = Challenge.query.get(submission.challenge_id)
        user = User.query.get(submission.user_id)
        
        # Prepare files list for Dify
        files = []
        upload_url_prefix = app.config.get('UPLOAD_URL_PREFIX', 'http://localhost:5000/uploads')
        
        for file in submission.files:
            # Determine file type based on extension
            file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
            file_type = 'image' if file_ext in ['png', 'jpg', 'jpeg', 'gif'] else 'file'
            
            files.append({
                'type': file_type,
                'transfer_method': 'remote_url',
                'url': f"{upload_url_prefix}/{file.filepath}"
            })
        
        # Prepare Dify API payload
        payload = {
            'inputs': {},
            'query': submission.answer_text or '评分',
            'response_mode': 'blocking',
            'conversation_id': '',
            'user': f"user-{user.id}",
            'files': files
        }
        
        # Send POST request to Dify API
        try:
            hook_url = _build_hook_url(challenge, app)
            api_key = _resolve_api_key(challenge, app)

            if not hook_url:
                return {
                    'success': False,
                    'error': 'No Dify hook URL configured (neither challenge-specific nor global).'
                }
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(hook_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse Dify response
            dify_response = response.json()
            
            # Extract answer field and parse it as JSON
            answer_text = dify_response.get('answer', '')
            
            try:
                # Strip markdown code fences if Dify wraps the response in ```json ... ```
                stripped = answer_text.strip()
                if stripped.startswith('```'):
                    # Remove opening fence (```json or ```)
                    stripped = stripped.split('\n', 1)[1] if '\n' in stripped else stripped[3:]
                    # Remove closing fence
                    if stripped.rstrip().endswith('```'):
                        stripped = stripped.rstrip()[:-3].rstrip()
                    answer_text = stripped

                # Parse the answer JSON string
                answer_data = json.loads(answer_text)

                # Persist feedback/score for admin secondary review reference.
                dify_log = submission.dify_log
                if not dify_log:
                    dify_log = SubmissionDifyLog(submission_id=submission.id)
                    db.session.add(dify_log)
                dify_log.feedback = answer_data.get('feedback', '')
                score_value = answer_data.get('score')
                try:
                    dify_log.score = int(score_value) if score_value is not None else None
                except (TypeError, ValueError):
                    dify_log.score = None
                
                # Update submission based on Dify response
                # Auto-approve/reject if auto_approved is True
                if answer_data.get('auto_approved'):
                    # Determine status based on success flag
                    if answer_data.get('success'):
                        submission.status = 'approved'
                        submission.points_awarded = answer_data.get('score', 0)
                    else:
                        submission.status = 'rejected'
                        submission.points_awarded = 0
                    
                    submission.reviewed_at = datetime.utcnow()
                    submission.reviewed_by_name = 'AI'  # Mark as AI-reviewed
                    # Note: reviewed_by_id remains None to indicate auto-approval
                    
                    db.session.commit()
                    
                    return {
                        'success': True,
                        'auto_approved': True,
                        'auto_status': submission.status,
                        'score': submission.points_awarded,
                        'feedback': answer_data.get('feedback', ''),
                        'dify_response': dify_response
                    }
                else:
                    # Keep as pending for manual review
                    return {
                        'success': True,
                        'auto_approved': False,
                        'feedback': answer_data.get('feedback', ''),
                        'dify_response': dify_response
                    }
                    
            except json.JSONDecodeError as e:
                # If answer is not valid JSON, log and keep pending
                return {
                    'success': False,
                    'error': 'Failed to parse Dify answer as JSON',
                    'answer_text': answer_text,
                    'parse_error': str(e)
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
