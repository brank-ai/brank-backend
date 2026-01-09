"""API routes."""

import logging
from flask import Blueprint, request, jsonify, g, current_app

from services import get_or_compute_metrics
from llm_clients import create_llm_clients
from utils.logger import get_logger

api_bp = Blueprint("api", __name__)
logger = get_logger(__name__)


@api_bp.route("/metric", methods=["GET"])
def get_metrics():
    """Get brand metrics across 4 LLMs.
    
    Query Parameters:
        website (str): Brand website (required)
        
    Returns:
        JSON response with metrics per LLM
        
    Status Codes:
        200: Success (includes partial failures)
        400: Missing or invalid website parameter
        500: Internal server error
    """
    # Validate input
    website = request.args.get("website")
    if not website:
        return jsonify({"error": "website parameter is required"}), 400

    try:
        # Get dependencies from app context
        db_session = g.db_session
        settings = current_app.config["SETTINGS"]

        # Create LLM clients
        llm_clients = create_llm_clients(settings, logger)

        # Call service
        result = get_or_compute_metrics(
            website=website,
            db_session=db_session,
            llm_clients=llm_clients,
            settings=settings,
            logger=logger,
        )

        return jsonify(result), 200

    except Exception as e:
        logger.exception(f"Failed to compute metrics for {website}: {e}")
        return jsonify({"error": "Internal server error"}), 500

