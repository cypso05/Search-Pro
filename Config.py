import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # SMART DATABASE CONFIGURATION
    # Detect if running on PythonAnywhere
    if 'PYTHONANYWHERE_DOMAIN' in os.environ:
        # PythonAnywhere free tier: Use SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///job_search.db'
        print("🔧 PythonAnywhere detected - Using SQLite database")
        
        # PythonAnywhere optimizations
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 280,  # PythonAnywhere connection timeout
        }
        
        # PythonAnywhere doesn't support Redis in free tier
        SESSION_TYPE = 'filesystem'
        SESSION_FILE_DIR = '/tmp/flask_sessions'  # PythonAnywhere allows /tmp
        SESSION_PERMANENT = False
        SESSION_USE_SIGNER = True
        
        # Disable Celery on PythonAnywhere free tier
        CELERY_ENABLED = False
        
        # PythonAnywhere email restrictions
        MAIL_SUPPRESS_SEND = True  # Disable email sending on free tier
        
    else:
        # Local development: Use PostgreSQL from .env
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/jobsearch')
        print("💻 Local development - Using PostgreSQL database")
        
        # Local/Production settings
        SESSION_TYPE = 'redis'
        SESSION_PERMANENT = False
        SESSION_USE_SIGNER = True
        CELERY_ENABLED = True
        MAIL_SUPPRESS_SEND = False
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API
    RAPID_API_KEY = os.getenv('RAPID_API_KEY')
    RAPID_API_HOST = os.getenv('RAPID_API_HOST', 'real-time-web-search.p.rapidapi.com')
    
    # Pagination
    RESULTS_PER_PAGE = int(os.getenv('RESULTS_PER_PAGE', 10))
    MAX_RESULTS = int(os.getenv('MAX_RESULTS', 100))
    
    # Security
    BCRYPT_LOG_ROUNDS = 12
    
    # Caching (in seconds) - Simple in-memory cache for PythonAnywhere
    CACHE_DEFAULT_TIMEOUT = 300
    if 'PYTHONANYWHERE_DOMAIN' in os.environ:
        CACHE_TYPE = 'simple'  # Simple in-memory cache
    else:
        CACHE_TYPE = 'redis'   # Redis cache for local/production
    
    # Rate limiting - Use in-memory for PythonAnywhere
    RATELIMIT_DEFAULT = "100 per hour"
    if 'PYTHONANYWHERE_DOMAIN' in os.environ:
        RATELIMIT_STORAGE_URI = 'memory://'
    else:
        RATELIMIT_STORAGE_URI = 'redis://localhost:6379/0'
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Celery (only for local/production)
    if 'PYTHONANYWHERE_DOMAIN' not in os.environ:
        CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    else:
        CELERY_BROKER_URL = None
        CELERY_RESULT_BACKEND = None
    
    # Job Search APIs (multiple sources for redundancy)
    JOB_SEARCH_APIS = {
        'rapidapi': {
            'url': 'https://real-time-web-search.p.rapidapi.com/search',
            'key': RAPID_API_KEY,
            'host': RAPID_API_HOST
        },
        'serpapi': {
            'url': 'https://serpapi.com/search',
            'key': os.getenv('SERPAPI_KEY')
        }
    }
    
    # PythonAnywhere specific file paths
    if 'PYTHONANYWHERE_DOMAIN' in os.environ:
        UPLOAD_FOLDER = '/tmp/uploads'  # PythonAnywhere allows /tmp
        LOG_FOLDER = '/tmp/logs'
    else:
        UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
        LOG_FOLDER = os.path.join(os.path.dirname(__file__), 'logs')
    
    # Logging configuration
    LOG_LEVEL = 'INFO'
    if 'PYTHONANYWHERE_DOMAIN' in os.environ:
        LOG_TO_STDOUT = True  # PythonAnywhere captures stdout
    else:
        LOG_TO_STDOUT = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # Development overrides
    if 'PYTHONANYWHERE_DOMAIN' not in os.environ:
        SESSION_COOKIE_SECURE = False  # Not secure in development
        SESSION_COOKIE_HTTPONLY = False  # For easier debugging


class ProductionConfig(Config):
    DEBUG = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production database settings (only for PostgreSQL)
    if 'PYTHONANYWHERE_DOMAIN' not in os.environ:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 300,
            'pool_pre_ping': True,
            'max_overflow': 20,
        }
    
    # Production logging
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True


# Helper function to check environment
def is_pythonanywhere():
    return 'PYTHONANYWHERE_DOMAIN' in os.environ


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}