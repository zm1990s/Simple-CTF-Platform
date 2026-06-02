#!/usr/bin/env python3
"""
测试 order_index 功能
Test order_index functionality after fixing clone/import/export
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from models import Competition, Challenge


def test_order_index():
    """Test order_index in various scenarios"""
    app = create_app('production')

    with app.app_context():
        print("=" * 70)
        print("测试 order_index 功能 / Testing order_index functionality")
        print("=" * 70)

        # Test 1: Check existing challenges
        print("\n📊 Test 1: 检查现有 Challenges 的 order_index")
        competitions = Competition.query.all()

        for comp in competitions:
            print(f"\n🏆 Competition: {comp.name} (ID: {comp.id})")
            challenges = Challenge.query.filter_by(
                competition_id=comp.id
            ).order_by(Challenge.order_index.asc(), Challenge.id.asc()).all()

            if challenges:
                print(f"   {'ID':<6} {'order_index':<12} {'Title'}")
                print(f"   {'-' * 60}")
                for c in challenges:
                    print(f"   {c.id:<6} {c.order_index:<12} {c.title}")
            else:
                print("   (无题目 / No challenges)")

        # Test 2: Verify order_index column exists
        print("\n📊 Test 2: 验证 order_index 字段是否存在")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('challenges')]

        if 'order_index' in columns:
            print("   ✅ order_index 字段存在")
        else:
            print("   ❌ order_index 字段不存在 - 需要运行迁移脚本！")
            print("   运行: docker exec ctf_web python add_challenge_order.py")

        print("\n" + "=" * 70)
        print("测试完成 / Test completed")
        print("=" * 70)


if __name__ == '__main__':
    test_order_index()