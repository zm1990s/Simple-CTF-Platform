#!/usr/bin/env python3
"""
Migration script to add is_disabled column to the users table.
Run this script to update your existing database.
"""
import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://ctf_user:ctf_password@localhost:5432/ctf_platform')


def main():
    print("Running is_disabled migration...")

    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='is_disabled';
            """))

            if result.fetchone():
                print("✓ Column 'is_disabled' already exists. Skipping.")
                return

            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN is_disabled BOOLEAN NOT NULL DEFAULT FALSE;
            """))
            conn.commit()
            print("✓ Added 'is_disabled' column to users table.")

        print("\nMigration completed successfully.")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
