"""Service for landing page metrics."""

import logging
from typing import Dict
from sqlalchemy.orm import Session

from db.repositories import MetricsRepository


# Fixed list of brands for landing page
LANDING_PAGE_BRANDS = [
    "decathlon",
    "leetcode",
    "basics",
    "zerodha",
    "coinbase",
    "nothing",
    "cult.fit",
]

# Default mention rate percentage when no data is available
DEFAULT_MENTION_RATE_PERCENT = 71.0


def get_landing_page_mention_rates(
    db_session: Session, logger: logging.Logger
) -> Dict[str, float]:
    """Get average mention rates for landing page brands.
    
    Queries the database for average mention rates across all LLMs for a fixed
    list of brands. Returns percentages (0-100). If a brand has no data in the
    database, returns the default value of 71.0.
    
    Args:
        db_session: Database session
        logger: Logger instance
        
    Returns:
        Dictionary mapping brand name (lowercase) to mention rate percentage (0-100)
        
    Example:
        {
            "decathlon": 71.0,
            "leetcode": 23.5,
            "basics": 45.2,
            ...
        }
    """
    logger.info(
        f"Fetching landing page mention rates for {len(LANDING_PAGE_BRANDS)} brands"
    )

    # Get average mention rates from database (returns 0.0-1.0 scale)
    db_results = MetricsRepository.get_avg_mention_rates_by_brand_names(
        db_session, LANDING_PAGE_BRANDS
    )

    logger.info(f"Found data for {len(db_results)} brands in database")

    # Build result dictionary with defaults for missing brands
    result = {}
    for brand_name in LANDING_PAGE_BRANDS:
        brand_lower = brand_name.lower()
        if brand_lower in db_results:
            # Convert from 0.0-1.0 to 0-100 percentage
            result[brand_lower] = db_results[brand_lower] * 100.0
            logger.debug(
                f"Brand '{brand_name}': {result[brand_lower]:.2f}% (from DB)"
            )
        else:
            # Use default value
            result[brand_lower] = DEFAULT_MENTION_RATE_PERCENT
            logger.debug(
                f"Brand '{brand_name}': {DEFAULT_MENTION_RATE_PERCENT}% (default)"
            )

    return result

