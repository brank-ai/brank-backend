"""Flask application factory."""

import logging
from flask import Flask, g
from sqlalchemy.orm import scoped_session, sessionmaker

from config import Settings, get_settings
from db import create_engine_from_url


def create_app(settings: Settings | None = None) -> Flask:
    """Create and configure Flask application.
    
    Args:
        settings: Optional settings instance (for testing). If None, loads from environment.
        
    Returns:
        Configured Flask application
        
    Raises:
        ValueError: If configuration is invalid
    """
    app = Flask(__name__)

    # Load settings
    if settings is None:
        settings = get_settings()

    app.config["SETTINGS"] = settings
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Setup database
    engine = create_engine_from_url(settings.database_url)
    session_factory = sessionmaker(bind=engine)
    app.config["DB_SESSION"] = scoped_session(session_factory)

    # Setup request context for DB session
    @app.before_request
    def before_request():
        """Create DB session for each request."""
        g.db_session = app.config["DB_SESSION"]()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Remove DB session after request."""
        db_session = getattr(g, "db_session", None)
        if db_session is not None:
            if exception:
                db_session.rollback()
            else:
                db_session.commit()
            db_session.close()
        app.config["DB_SESSION"].remove()

    # Register blueprints
    from api.routes import api_bp

    app.register_blueprint(api_bp)

    # Register error handlers
    from api.errors import register_error_handlers

    register_error_handlers(app)

    # Health check endpoint
    @app.route("/health")
    def health():
        """Health check endpoint."""
        return {"status": "healthy"}, 200

    return app


app = create_app()


if __name__ == "__main__":
    app = create_app()
    settings = app.config["SETTINGS"]
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=settings.debug,
    )

