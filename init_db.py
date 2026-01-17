#!/usr/bin/env python3
"""
Initialize the CTF Platform
This script sets up the database and creates the default admin user
"""

import os
import sys
from app import create_app, db
from models import User, PlatformSettings

def init_database():
    """Initialize database"""
    app = create_app('production')
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Create default admin if not exists
        admin_email = app.config['ADMIN_EMAIL']
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            print(f"\nCreating default admin user...")
            admin = User(
                username='admin',
                email=admin_email,
                is_admin=True
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin user created: {admin_email}")
            print(f"   Default password: {app.config['ADMIN_PASSWORD']}")
            print("   ⚠️  Please change this password after first login!")
        else:
            print(f"\n⚠️  Admin user already exists: {admin_email}")
        
        # Create default platform settings
        print("\nCreating default platform settings...")
        settings = {
            'platform_name': app.config['PLATFORM_NAME'],
            'platform_logo': app.config['PLATFORM_LOGO']
        }
        
        for key, value in settings.items():
            setting = PlatformSettings.query.filter_by(key=key).first()
            if not setting:
                setting = PlatformSettings(key=key, value=value)
                db.session.add(setting)
        
        db.session.commit()
        print("✅ Platform settings created!")
        
        print("\n" + "="*50)
        print("✅ CTF Platform initialization completed!")
        print("="*50)
        print("\nYou can now start the application:")
        print("  Development: python app.py")
        print("  Production: gunicorn --bind 0.0.0.0:5000 app:app")
        print("\nOr use Docker:")
        print("  docker compose up -d")
        print()

if __name__ == '__main__':
    init_database()
