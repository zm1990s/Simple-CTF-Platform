#!/usr/bin/env python3
"""
Migration script to add PIN support to competitions.
- Adds `pin` column to the `competitions` table
- Creates the `competition_access` table
Run this script to update your existing database.
"""
import os
import sys
import random
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://ctf_user:ctf_password@localhost:5432/ctf_platform')


def main():
    print("Running PIN migration...")

    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # ── 1. Add `pin` column to competitions ──────────────────────────
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='competitions' AND column_name='pin';
            """))

            if result.fetchone():
                print("✓ Column 'pin' already exists on competitions. Skipping.")
            else:
                conn.execute(text("""
                    ALTER TABLE competitions
                    ADD COLUMN pin VARCHAR(6);
                """))
                conn.commit()
                print("✓ Added 'pin' column to competitions.")

                # Backfill existing rows with random 6-digit PINs
                rows = conn.execute(text("SELECT id FROM competitions;")).fetchall()
                for (comp_id,) in rows:
                    pin = str(random.randint(100000, 999999))
                    conn.execute(
                        text("UPDATE competitions SET pin = :pin WHERE id = :id;"),
                        {"pin": pin, "id": comp_id}
                    )
                conn.commit()

                # Now enforce NOT NULL
                conn.execute(text("""
                    ALTER TABLE competitions
                    ALTER COLUMN pin SET NOT NULL;
                """))
                conn.commit()
                print(f"✓ Backfilled PINs for {len(rows)} existing competition(s).")

            # ── 2. Create competition_access table ────────────────────────────
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name='competition_access';
            """))

            if result.fetchone():
                print("✓ Table 'competition_access' already exists. Skipping.")
            else:
                conn.execute(text("""
                    CREATE TABLE competition_access (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        competition_id INTEGER NOT NULL REFERENCES competitions(id) ON DELETE CASCADE,
                        joined_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
                        CONSTRAINT uq_user_competition UNIQUE (user_id, competition_id)
                    );
                """))
                conn.commit()
                print("✓ Created 'competition_access' table.")

        print("\nMigration completed successfully.")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
