#!/usr/bin/env python3
"""
Migration script to add reviewed_by_name column to submissions table
Run this script to update your existing database
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://ctf_user:ctf_password@localhost:5432/ctf_platform')

def main():
    print("Adding reviewed_by_name column to submissions table...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='submissions' AND column_name='reviewed_by_name';
            """))
            
            if result.fetchone():
                print("✓ Column 'reviewed_by_name' already exists. Skipping.")
                return
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE submissions 
                ADD COLUMN reviewed_by_name VARCHAR(100);
            """))
            conn.commit()
            
            print("✓ Successfully added 'reviewed_by_name' column to submissions table.")
            
            # Optional: Migrate existing data
            print("\nMigrating existing reviewer data...")
            result = conn.execute(text("""
                UPDATE submissions 
                SET reviewed_by_name = users.username 
                FROM users 
                WHERE submissions.reviewed_by_id = users.id 
                AND submissions.reviewed_by_name IS NULL;
            """))
            conn.commit()
            
            rows_updated = result.rowcount
            print(f"✓ Updated {rows_updated} existing submissions with reviewer names.")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
