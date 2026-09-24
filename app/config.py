import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(DATA_DIR, exist_ok=True)

    default_db = f'sqlite:///{os.path.join(DATA_DIR, "names.db")}'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', default_db)

    # Engine options common to all database backends.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        # Echo SQL for debugging (disable in production via env).
        'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true',
    }

    PROXY_TRUST = int(os.getenv('PROXY_TRUST', 2))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
