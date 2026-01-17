import os
import sys
import json
import requests
from celery import Celery
from datetime import datetime

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


@celery.task
def trigger_external_hook(submission_id):
    """Trigger Dify workflow for automated submission review and scoring"""
    from app import create_app
    from models import Submission, Challenge, User, SubmissionFile, db
    
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
            hook_url = app.config['EXTERNAL_HOOK_URL']
            api_key = app.config.get('DIFY_API_KEY', '')
            
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
                # Parse the answer JSON string
                answer_data = json.loads(answer_text)
                
                # Update submission based on Dify response
                if answer_data.get('success') and answer_data.get('auto_approved'):
                    submission.status = 'approved'
                    submission.points_awarded = answer_data.get('score', 0)
                    submission.reviewed_at = datetime.utcnow()
                    submission.reviewed_by_name = 'AI'  # Mark as AI-reviewed
                    # Note: reviewed_by_id remains None to indicate auto-approval
                    
                    db.session.commit()
                    
                    return {
                        'success': True,
                        'auto_approved': True,
                        'score': answer_data.get('score', 0),
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
