import os
import json
from flask import Flask, session
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_babel import Babel
from config import config
from models import db, User

migrate = Migrate()
login_manager = LoginManager()
babel = Babel()

# Load translations
translations = {}
try:
    basedir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(basedir, 'translations.json'), 'r', encoding='utf-8') as f:
        translations = json.load(f)
except Exception as e:
    print(f"Warning: Could not load translations.json: {e}")


def create_app(config_name='default'):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Babel locale selector
    def get_locale():
        from flask import request, session
        # Try to get from session first
        locale = session.get('locale')
        if locale in app.config['BABEL_SUPPORTED_LOCALES']:
            return locale
        # Fall back to best match
        return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES'])
    
    babel.init_app(app, locale_selector=get_locale)
    
    # Add translation function to Jinja2
    @app.context_processor
    def inject_translations():
        def _(text):
            # Get current locale from session
            locale = session.get('locale', 'en')
            # Return translated text or fallback to original
            if text in translations and locale in translations[text]:
                return translations[text][locale]
            return text
        return dict(_=_)
    
    @app.context_processor
    def inject_platform_settings():
        """Inject platform settings into all templates"""
        from models import PlatformSettings
        settings = {}
        platform_name = PlatformSettings.query.filter_by(key='platform_name').first()
        platform_logo = PlatformSettings.query.filter_by(key='platform_logo').first()
        footer_text = PlatformSettings.query.filter_by(key='footer_text').first()
        
        settings['PLATFORM_NAME'] = platform_name.value if platform_name else 'CTF Platform'
        settings['PLATFORM_LOGO'] = platform_logo.value if platform_logo else None
        settings['FOOTER_TEXT'] = footer_text.value if footer_text else '100% Written by AI · Made with ♥ by Matt'
        
        return dict(config=settings)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.frontend import frontend_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(frontend_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Serve uploaded files
    from flask import send_from_directory
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files"""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Create admin user if not exists
    with app.app_context():
        db.create_all()
        create_default_admin(app)
        create_default_settings(app)
    
    return app


def create_default_admin(app):
    """Create default admin user"""
    admin = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
    if not admin:
        admin = User(
            username='admin',
            email=app.config['ADMIN_EMAIL'],
            is_admin=True
        )
        admin.set_password(app.config['ADMIN_PASSWORD'])
        db.session.add(admin)
        db.session.commit()
        print(f"Default admin created: {app.config['ADMIN_EMAIL']}")


def create_default_settings(app):
    """Create default platform settings"""
    from models import PlatformSettings
    
    defaults = {
        'platform_name': app.config['PLATFORM_NAME'],
        'platform_logo': app.config['PLATFORM_LOGO']
    }
    
    for key, value in defaults.items():
        setting = PlatformSettings.query.filter_by(key=key).first()
        if not setting:
            setting = PlatformSettings(key=key, value=value)
            db.session.add(setting)
    
    db.session.commit()


if __name__ == '__main__':
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=5000)
