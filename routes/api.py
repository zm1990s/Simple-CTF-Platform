from flask import Blueprint, jsonify
from models import Competition, Challenge, Submission
from sqlalchemy import func
from models import db

api_bp = Blueprint('api', __name__)


@api_bp.route('/leaderboard/<int:competition_id>')
def leaderboard_api(competition_id):
    """API endpoint for real-time leaderboard"""
    competition = Competition.query.get_or_404(competition_id)
    
    # Calculate scores - only count highest score per user per challenge
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
    
    from models import User
    leaderboard_data = []
    for rank, (user_id, total_points, last_solve_time) in enumerate(results, 1):
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
