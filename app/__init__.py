from flask import Flask
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlalchemy import event

from app.config import Config
from app.extensions import db, login_manager
from app.routes import register_blueprints

load_dotenv()

migrate = Migrate()


def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure SQLite for concurrent access.

    - WAL mode: writers don't block readers and vice versa.
    - busy_timeout: wait up to 5 s instead of failing immediately when a
      lock is held.
    - foreign_keys: enforce FK constraints (normally off by default in
      SQLite).
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA busy_timeout=5000')
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()
    except Exception:
        # Not a SQLite connection — ignore.
        pass


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # SQLite-specific engine options: ``check_same_thread`` allows the
    # connection to be used across threads (needed for gunicorn), and WAL
    # pragmas improve concurrent read/write performance.
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url.startswith('sqlite'):
        app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {})
        app.config['SQLALCHEMY_ENGINE_OPTIONS'].setdefault('connect_args', {})
        app.config['SQLALCHEMY_ENGINE_OPTIONS']['connect_args']['check_same_thread'] = False

    # ProxyFix: trust reverse proxy layers
    proxy_trust = app.config.get('PROXY_TRUST', 2)
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=proxy_trust, x_proto=proxy_trust,
        x_host=1, x_prefix=1
    )

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录~'
    login_manager.remember_cookie_duration = 365 * 24 * 60 * 60  # 1 year
    migrate.init_app(app, db)

    # Apply SQLite pragmas on every new database connection.
    if db_url.startswith('sqlite'):
        event.listen(Engine, 'connect', _set_sqlite_pragma)

    # User loader
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    register_blueprints(app)

    return app
