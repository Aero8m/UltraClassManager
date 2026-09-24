from app.routes.auth import auth_bp
from app.routes.group import group_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(group_bp)
