# Database Migrations

This directory will be created automatically when you initialize Flask-Migrate.

## Initial Setup

If using local development, initialize migrations:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Using init_db.py (Recommended)

The easier way is to use the provided initialization script:
```bash
python init_db.py
```

This will:
1. Create all database tables
2. Create the default admin user
3. Set up default platform settings

## Docker Deployment

When using Docker Compose, the database is initialized automatically on first run.

## Database Schema Changes

If you modify models.py, create a new migration:
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Note

The migrations directory is included in .gitignore. Each environment should manage its own migrations.
