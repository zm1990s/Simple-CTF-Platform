import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://ctf_user:ctf_password@localhost:5432/ctf_platform'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(basedir, os.environ.get('UPLOAD_FOLDER', 'uploads'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt', 'pdf', 'zip'}
    
    # Platform configuration
    PLATFORM_NAME = os.environ.get('PLATFORM_NAME', 'CTF Platform')
    PLATFORM_LOGO = os.environ.get('PLATFORM_LOGO', 'logo.png')
    FOOTER_TEXT = os.environ.get('FOOTER_TEXT', '100% Written by AI · Made with ♥ by Matt')
    
    # Babel configuration
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_SUPPORTED_LOCALES = ['en', 'zh']
    
    # Redis and Celery
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # External hook
    EXTERNAL_HOOK_ENABLED = os.environ.get('EXTERNAL_HOOK_ENABLED', 'false').lower() == 'true'
    EXTERNAL_HOOK_URL = os.environ.get('EXTERNAL_HOOK_URL', '')
    
    # Admin defaults
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@ctf.local')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
