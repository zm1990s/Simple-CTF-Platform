import os
import requests
from celery import Celery

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
    """Trigger external hook for submission validation"""
    from app import create_app
    from models import Submission, Challenge, User
    
    app = create_app()
    with app.app_context():
        submission = Submission.query.get(submission_id)
        if not submission:
            return {'error': 'Submission not found'}
        
        challenge = Challenge.query.get(submission.challenge_id)
        user = User.query.get(submission.user_id)
        
        # Prepare payload
        payload = {
            'submission_id': submission.id,
            'user_id': user.id,
            'username': user.username,
            'challenge_id': challenge.id,
            'challenge_title': challenge.title,
            'answer_text': submission.answer_text,
            'submitted_at': submission.submitted_at.isoformat()
        }
        
        # Send POST request to external hook
        try:
            hook_url = app.config['EXTERNAL_HOOK_URL']
            response = requests.post(hook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.headers.get('content-type') == 'application/json' else response.text
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
