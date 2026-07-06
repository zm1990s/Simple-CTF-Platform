from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from models import db, User
from forms import LoginForm, RegisterForm, ChangePasswordForm


def is_safe_redirect(target):
    """Allow only same-host relative redirects."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('frontend.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if username exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Check if email exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('frontend.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if user.is_disabled:
                flash('This account has been disabled. Please contact an administrator.', 'danger')
                return render_template('auth/login.html', form=form)
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page and is_safe_redirect(next_page):
                return redirect(next_page)
            return redirect(url_for('frontend.index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('frontend.index'))


@auth_bp.route('/set-locale/<locale>')
def set_locale(locale):
    """Set user locale"""
    if locale in ['en', 'zh']:
        session['locale'] = locale
    referrer = request.referrer
    if referrer and is_safe_redirect(referrer):
        return redirect(referrer)
    return redirect(url_for('frontend.index'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/change_password.html', form=form)
        
        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('frontend.index'))
    
    return render_template('auth/change_password.html', form=form)
