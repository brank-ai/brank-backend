"""API routes."""

import logging
from flask import Blueprint, request, jsonify, g, current_app

from services import get_or_compute_metrics, get_landing_page_mention_rates
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


@api_bp.route("/metrics/landingPage", methods=["GET"])
def get_landing_page_metrics():
    """Get average mention rates for landing page brands.
    
    Returns average mention rate percentages (0-100) for a fixed list of brands:
    decathlon, leetcode, asics, zerodha, coinbase, nothing, cult.fit
    
    Returns:
        JSON response with brand name to percentage mapping
        
    Status Codes:
        200: Success
        500: Internal server error
    """
    try:
        # Get dependencies from app context
        db_session = g.db_session

        # Call service
        result = get_landing_page_mention_rates(
            db_session=db_session,
            logger=logger,
        )

        return jsonify(result), 200

    except Exception as e:
        logger.exception(f"Failed to fetch landing page metrics: {e}")
        return jsonify({"error": "Internal server error"}), 500

