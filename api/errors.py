"""Error handlers for Flask app."""

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """Register error handlers with Flask app.
    
    Args:
        app: Flask application instance
    """

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request."""
        return jsonify({"error": "Bad request", "details": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found."""
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        app.logger.error(f"Internal error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable."""
        return jsonify({"error": "Service temporarily unavailable"}), 503

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all HTTP exceptions."""
        return jsonify({"error": error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        app.logger.exception("Unexpected error")
        return jsonify({"error": "An unexpected error occurred"}), 500

