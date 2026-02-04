"""API routes."""

import logging
from flask import Blueprint, request, jsonify, g, current_app

from services import get_or_compute_metrics, get_landing_page_mention_rates, send_slack_notification
from db.models import BrandInsightRequest
from db.repositories.prompt_repository import PromptRepository
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


@api_bp.route("/brand-insight-request", methods=["POST"])
def create_brand_insight_request():
    """Record a brand insight request from the landing page modal.

    Request Body (JSON):
        brand_name (str): Name of the brand (required)
        email (str): User's email address (required)

    Returns:
        JSON response with success message and request_id

    Status Codes:
        201: Created successfully
        400: Missing required fields
        500: Internal server error
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    brand_name = data.get("brand_name")
    email = data.get("email")

    if not brand_name:
        return jsonify({"error": "brand_name is required"}), 400
    if not email:
        return jsonify({"error": "email is required"}), 400

    try:
        db_session = g.db_session
        settings = current_app.config["SETTINGS"]

        insight_request = BrandInsightRequest(
            brand_name=brand_name,
            email=email,
        )
        db_session.add(insight_request)
        db_session.commit()

        logger.info(f"Brand insight request recorded for {brand_name} ({email})")

        # Send Slack notification (fire-and-forget, don't fail request if Slack fails)
        send_slack_notification(
            webhook_url=settings.slack_webhook_url,
            brand_name=brand_name,
            email=email,
            logger=logger,
        )

        return jsonify({
            "message": "Brand insight request recorded successfully",
            "request_id": str(insight_request.request_id),
        }), 201

    except Exception as e:
        logger.exception(f"Failed to record brand insight request: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/metric/prompts", methods=["GET"])
def get_prompts():
    """Get prompts for a brand with pagination.

    Query Parameters:
        brand_name (str): Brand name (optional, takes precedence over website, case-insensitive)
        website (str): Brand website (optional, case-insensitive)
        page (int): Page number, 1-indexed (optional, default=1)
        per_page (int): Items per page (optional, default=10, max=100)

    Note: At least one of brand_name or website is required.
    If both are provided, brand_name takes precedence.

    Returns:
        JSON response with prompts list and pagination metadata

    Status Codes:
        200: Success
        400: Missing required parameters or invalid input
        404: Brand not found
        500: Internal server error
    """
    # Get query parameters
    brand_name = request.args.get("brand_name")
    website = request.args.get("website")
    page_str = request.args.get("page", "1")
    per_page_str = request.args.get("per_page", "10")

    # Validate at least one identifier is provided
    if not brand_name and not website:
        return jsonify({"error": "Either brand_name or website parameter is required"}), 400

    # Validate and parse pagination parameters
    try:
        page = int(page_str)
        if page < 1:
            return jsonify({"error": "page must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "page must be a valid integer"}), 400

    try:
        per_page = int(per_page_str)
        if per_page < 1:
            return jsonify({"error": "per_page must be a positive integer"}), 400
        if per_page > 100:
            per_page = 100  # Cap at 100
    except ValueError:
        return jsonify({"error": "per_page must be a valid integer"}), 400

    try:
        db_session = g.db_session

        # Resolve brand_id (brand_name takes precedence over website)
        brand_id = None

        if brand_name:
            # Look up by brand name (case-insensitive)
            brand_id = PromptRepository.get_brand_id_by_name(db_session, brand_name)
            if not brand_id:
                return jsonify({"error": f"Brand not found for name: {brand_name}"}), 404
        elif website:
            # Look up by website (case-insensitive)
            brand_id = PromptRepository.get_brand_id_by_website(db_session, website)
            if not brand_id:
                return jsonify({"error": f"Brand not found for website: {website}"}), 404

        # Get paginated prompts
        prompts, total = PromptRepository.get_prompts_paginated(
            db_session=db_session,
            brand_id=brand_id,
            page=page,
            per_page=per_page,
        )

        # Calculate pagination metadata
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1

        return jsonify({
            "prompts": [
                {
                    "prompt_id": str(p.prompt_id),
                    "prompt": p.prompt,
                }
                for p in prompts
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            },
        }), 200

    except Exception as e:
        logger.exception(f"Failed to fetch prompts: {e}")
        return jsonify({"error": "Internal server error"}), 500

