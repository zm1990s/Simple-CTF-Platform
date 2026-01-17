#!/usr/bin/env python3
"""
Migration script to add order_index column to challenges table
Run this script to update your existing database
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment or use default
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://ctf_user:ctf_password@localhost:5432/ctf_platform')

def main():
    print("Adding order_index column to challenges table...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='challenges' AND column_name='order_index';
            """))
            
            if result.fetchone():
                print("✓ Column 'order_index' already exists. Skipping.")
                return
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE challenges 
                ADD COLUMN order_index INTEGER DEFAULT 0;
            """))
            conn.commit()
            
            print("✓ Successfully added 'order_index' column to challenges table.")
            
            # Set order_index based on existing challenges
            # Group by competition and set order based on id
            print("\nInitializing order_index for existing challenges...")
            conn.execute(text("""
                WITH ranked_challenges AS (
                    SELECT 
                        id,
                        ROW_NUMBER() OVER (PARTITION BY competition_id ORDER BY id) - 1 AS row_num
                    FROM challenges
                )
                UPDATE challenges 
                SET order_index = ranked_challenges.row_num 
                FROM ranked_challenges 
                WHERE challenges.id = ranked_challenges.id;
            """))
            conn.commit()
            
            result = conn.execute(text("SELECT COUNT(*) FROM challenges;"))
            challenge_count = result.fetchone()[0]
            print(f"✓ Initialized order_index for {challenge_count} challenges.")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
