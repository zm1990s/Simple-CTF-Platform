from flask import Blueprint, jsonify
from models import Competition, Challenge, Submission
from sqlalchemy import func
from models import db

api_bp = Blueprint('api', __name__)


@api_bp.route('/leaderboard/<int:competition_id>')
def leaderboard_api(competition_id):
    """API endpoint for real-time leaderboard"""
    competition = Competition.query.get_or_404(competition_id)
    
    # Calculate scores
    scores = db.session.query(
        Submission.user_id,
        func.sum(Submission.points_awarded).label('total_points'),
        func.max(Submission.reviewed_at).label('last_solve_time')
    ).join(Challenge).filter(
        Challenge.competition_id == competition_id,
        Submission.status == 'approved'
    ).group_by(Submission.user_id).order_by(
        func.sum(Submission.points_awarded).desc(),
        func.max(Submission.reviewed_at).asc()
    ).all()
    
    from models import User
    leaderboard_data = []
    for rank, (user_id, total_points, last_solve_time) in enumerate(scores, 1):
        user = User.query.get(user_id)
        leaderboard_data.append({
            'rank': rank,
            'username': user.username,
            'total_points': int(total_points or 0),
            'last_solve_time': last_solve_time.isoformat() if last_solve_time else None
        })
    
    return jsonify({
        'competition': {
            'id': competition.id,
            'name': competition.name,
            'is_running': competition.is_running()
        },
        'leaderboard': leaderboard_data
    })


@api_bp.route('/competitions/<int:competition_id>/stats')
def competition_stats(competition_id):
    """API endpoint for competition statistics"""
    competition = Competition.query.get_or_404(competition_id)
    
    challenges_count = Challenge.query.filter_by(competition_id=competition_id, is_active=True).count()
    submissions_count = db.session.query(func.count(Submission.id)).join(Challenge).filter(
        Challenge.competition_id == competition_id
    ).scalar()
    
    return jsonify({
        'competition_id': competition.id,
        'challenges_count': challenges_count,
        'submissions_count': submissions_count,
        'is_running': competition.is_running()
    })
