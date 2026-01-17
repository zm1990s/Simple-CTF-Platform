from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, IntegerField, DateTimeField, FileField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError
from flask_wtf.file import FileAllowed
import re


def flexible_email(form, field):
    """Flexible email validator that accepts .local and other non-standard TLDs"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, field.data):
        raise ValidationError('Invalid email address.')


class LoginForm(FlaskForm):
    """Login form"""
    email = StringField('Email', validators=[DataRequired(), flexible_email])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')


class RegisterForm(FlaskForm):
    """Registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), flexible_email])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])


class ChangePasswordForm(FlaskForm):
    """Change password form"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                    validators=[DataRequired(), EqualTo('new_password')])


class ResetPasswordForm(FlaskForm):
    """Admin reset password form"""
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                    validators=[DataRequired(), EqualTo('new_password')])


class ChallengeForm(FlaskForm):
    """Challenge creation/edit form"""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description (Markdown)', validators=[DataRequired()])
    points = IntegerField('Points', validators=[DataRequired(), NumberRange(min=1)])
    category = StringField('Category', validators=[Length(max=100)])
    competition_id = SelectField('Competition', coerce=int, validators=[DataRequired()])


class CompetitionForm(FlaskForm):
    """Competition creation/edit form"""
    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    countdown_minutes = IntegerField('Countdown (minutes)', validators=[Optional(), NumberRange(min=0)], default=0)


class SubmissionForm(FlaskForm):
    """Submission form"""
    answer_text = TextAreaField('Answer')
    files = FileField('Upload Images (multiple)', 
                     validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])


class ReviewForm(FlaskForm):
    """Submission review form"""
    status = SelectField('Status', choices=[('approved', 'Approved'), ('rejected', 'Rejected')], 
                        validators=[DataRequired()])
    points_awarded = IntegerField('Points Awarded', validators=[Optional(), NumberRange(min=0)])


class PlatformSettingsForm(FlaskForm):
    """Platform settings form"""
    platform_name = StringField('Platform Name', validators=[DataRequired(), Length(max=200)])
    platform_logo = FileField('Platform Logo', 
                             validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    footer_text = StringField('Footer Text', validators=[Optional(), Length(max=500)])
