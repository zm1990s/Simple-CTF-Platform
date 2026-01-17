from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', foreign_keys='Submission.user_id', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set hashed password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Competition(db.Model):
    """Competition model"""
    __tablename__ = 'competitions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime)  # Optional: for reference only
    end_time = db.Column(db.DateTime)    # Optional: for reference only
    status = db.Column(db.String(20), default='draft')  # draft, running, paused, stopped
    countdown_minutes = db.Column(db.Integer, default=0)  # Countdown duration in minutes
    countdown_started_at = db.Column(db.DateTime)  # When countdown was started
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    challenges = db.relationship('Challenge', backref='competition', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_running(self):
        """Check if competition is currently running"""
        return self.status == 'running'
    
    def is_visible(self):
        """Check if competition is visible to users"""
        return self.status in ['running', 'paused']
    
    def get_remaining_time(self):
        """Get remaining time in seconds, None if no countdown"""
        if not self.countdown_started_at or self.countdown_minutes <= 0:
            return None
        elapsed = (datetime.utcnow() - self.countdown_started_at).total_seconds()
        remaining = (self.countdown_minutes * 60) - elapsed
        return max(0, int(remaining))
    
    def __repr__(self):
        return f'<Competition {self.name}>'


class Challenge(db.Model):
    """Challenge model"""
    __tablename__ = 'challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)  # Markdown content
    points = db.Column(db.Integer, nullable=False, default=100)
    category = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    
    # Relationships
    submissions = db.relationship('Submission', backref='challenge', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Challenge {self.title}>'


class Submission(db.Model):
    """Submission model"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    answer_text = db.Column(db.Text)  # Text answer
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    points_awarded = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    
    # Relationships
    files = db.relationship('SubmissionFile', backref='submission', lazy='dynamic', cascade='all, delete-orphan')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id])
    
    def __repr__(self):
        return f'<Submission {self.id} by User {self.user_id}>'


class SubmissionFile(db.Model):
    """Submission file model for image uploads"""
    __tablename__ = 'submission_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    
    def __repr__(self):
        return f'<SubmissionFile {self.filename}>'


class PlatformSettings(db.Model):
    """Platform settings model"""
    __tablename__ = 'platform_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PlatformSettings {self.key}>'


class SubmissionHistory(db.Model):
    """Submission history model - archived submissions from competition resets"""
    __tablename__ = 'submission_history'
    
    id = db.Column(db.Integer, primary_key=True)
    original_submission_id = db.Column(db.Integer, nullable=False)
    answer_text = db.Column(db.Text)
    status = db.Column(db.String(20))  # pending, approved, rejected
    points_awarded = db.Column(db.Integer, default=0)
    submitted_at = db.Column(db.DateTime)
    reviewed_at = db.Column(db.DateTime)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id'), nullable=False)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    challenge = db.relationship('Challenge')
    competition = db.relationship('Competition')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_id])
    files = db.relationship('SubmissionFileHistory', backref='submission_history', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SubmissionHistory {self.id} (original: {self.original_submission_id})>'


class SubmissionFileHistory(db.Model):
    """Submission file history model - archived files from competition resets"""
    __tablename__ = 'submission_file_history'
    
    id = db.Column(db.Integer, primary_key=True)
    original_file_id = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime)
    archived_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    submission_history_id = db.Column(db.Integer, db.ForeignKey('submission_history.id'), nullable=False)
    
    def __repr__(self):
        return f'<SubmissionFileHistory {self.filename}>'
