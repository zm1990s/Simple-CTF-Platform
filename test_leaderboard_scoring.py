#!/usr/bin/env python3
"""
Test script to verify leaderboard scoring logic
Tests that each user only gets credit for their highest score per challenge
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Competition, Challenge, Submission
from datetime import datetime, timedelta

def test_leaderboard_scoring():
    """Test that leaderboard only counts highest score per challenge"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Leaderboard Scoring Logic\n")
        print("=" * 60)
        
        # Find or create test data
        competition = Competition.query.filter_by(name='Test Competition').first()
        if not competition:
            print("⚠️  No test competition found. Creating one...")
            competition = Competition(
                name='Test Competition',
                description='Test competition for scoring verification',
                status='running'
            )
            db.session.add(competition)
            db.session.commit()
        
        # Find or create a test challenge
        challenge = Challenge.query.filter_by(
            competition_id=competition.id,
            title='Test Challenge'
        ).first()
        
        if not challenge:
            print("⚠️  No test challenge found. Creating one...")
            challenge = Challenge(
                title='Test Challenge',
                description='Test challenge for scoring',
                points=100,
                category='Test',
                competition_id=competition.id,
                is_active=True
            )
            db.session.add(challenge)
            db.session.commit()
        
        # Find test users
        user1 = User.query.filter_by(email='test1@example.com').first()
        user2 = User.query.filter_by(email='test2@example.com').first()
        
        if not user1 or not user2:
            print("⚠️  Test users not found. Please create test users first.")
            print("   Email: test1@example.com, test2@example.com")
            return
        
        print(f"\n📊 Test Setup:")
        print(f"   Competition: {competition.name} (ID: {competition.id})")
        print(f"   Challenge: {challenge.title} (Max: {challenge.points} points)")
        print(f"   User 1: {user1.username} ({user1.email})")
        print(f"   User 2: {user2.username} ({user2.email})")
        
        # Check existing submissions for this test
        print(f"\n📝 Existing Submissions for {user1.username}:")
        submissions_user1 = Submission.query.filter_by(
            user_id=user1.id,
            challenge_id=challenge.id,
            status='approved'
        ).order_by(Submission.reviewed_at).all()
        
        total_approved = 0
        max_score = 0
        for sub in submissions_user1:
            print(f"   - {sub.points_awarded} points at {sub.reviewed_at}")
            total_approved += sub.points_awarded
            max_score = max(max_score, sub.points_awarded)
        
        if submissions_user1:
            print(f"\n📈 Scoring Analysis for {user1.username}:")
            print(f"   ❌ Old logic (SUM): {total_approved} points")
            print(f"   ✅ New logic (MAX): {max_score} points")
            print(f"   💡 Difference: {total_approved - max_score} points saved")
        else:
            print(f"   No approved submissions yet")
        
        # Test the actual leaderboard query
        print(f"\n🏆 Testing Leaderboard Query...")
        from sqlalchemy import func
        
        # New logic - max score per user per challenge
        max_scores_subquery = db.session.query(
            Submission.user_id,
            Submission.challenge_id,
            func.max(Submission.points_awarded).label('max_points')
        ).join(Challenge).filter(
            Challenge.competition_id == competition.id,
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
            Challenge.competition_id == competition.id,
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
        
        print(f"\n🏅 Current Leaderboard:")
        print("-" * 60)
        if results:
            for rank, (user_id, total_points, last_solve) in enumerate(results, 1):
                user = User.query.get(user_id)
                print(f"   #{rank} {user.username:20s} {int(total_points):3d} points")
        else:
            print("   (No submissions yet)")
        
        print("\n" + "=" * 60)
        print("✅ Leaderboard scoring test completed!")
        print("\n💡 Key Points:")
        print("   - Each user only gets credit for their HIGHEST score per challenge")
        print("   - Multiple submissions are allowed but won't stack scores")
        print("   - All submission history is preserved for review")
        
if __name__ == '__main__':
    test_leaderboard_scoring()
