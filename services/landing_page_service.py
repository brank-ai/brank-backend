"""Service for landing page metrics."""

import logging
from typing import Dict
from sqlalchemy.orm import Session

from db.repositories import MetricsRepository


# Fixed list of brands for landing page
LANDING_PAGE_BRANDS = [
    "decathlon",
    "leetcode",
    "asics",
    "zerodha",
    "coinbase",
    "nothing",
    "cult.fit",
]

# Default values when no data is available
DEFAULT_MENTION_RATE_PERCENT = 71.0
DEFAULT_SENTIMENT_SCORE = 71.0


def get_landing_page_metrics(
    db_session: Session, logger: logging.Logger
) -> Dict[str, Dict[str, float]]:
    """Get average mention rates and sentiment scores for landing page brands.

    Args:
        db_session: Database session
        logger: Logger instance

    Returns:
        Dictionary mapping brand name to {"mentions": 0-100, "sentiment": 0-100}
    """
    logger.info(
        f"Fetching landing page metrics for {len(LANDING_PAGE_BRANDS)} brands"
    )

    db_results = MetricsRepository.get_avg_metrics_by_brand_names(
        db_session, LANDING_PAGE_BRANDS
    )

    logger.info(f"Found data for {len(db_results)} brands in database")

    result: Dict[str, Dict[str, float]] = {}
    for brand_name in LANDING_PAGE_BRANDS:
        brand_lower = brand_name.lower()
        if brand_lower in db_results:
            data = db_results[brand_lower]
            result[brand_lower] = {
                "mentions": round(data["mention_rate"] * 100.0, 1),
                "sentiment": round(data["sentiment_score"], 1),
            }
        else:
            result[brand_lower] = {
                "mentions": DEFAULT_MENTION_RATE_PERCENT,
                "sentiment": DEFAULT_SENTIMENT_SCORE,
            }

    return result
