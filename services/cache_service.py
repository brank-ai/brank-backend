"""Cache management service."""

import logging
import uuid
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from db.repositories import MetricsRepository


def check_cache(
    db_session: Session, brand_id: uuid.UUID, hours: int, logger: logging.Logger
) -> Optional[Dict]:
    """Check if brand has fresh cached metrics.
    
    Args:
        db_session: Database session
        brand_id: Brand UUID
        hours: Number of hours to consider "fresh" (typically 24)
        logger: Logger instance
        
    Returns:
        Dictionary with metrics per LLM if cache is fresh, None otherwise
    """
    logger.info(f"Checking cache for brand {brand_id} (freshness: {hours}h)")

    # Check if all 4 LLMs have fresh metrics
    if not MetricsRepository.has_fresh_cache(db_session, brand_id, hours):
        logger.info("Cache miss or stale - need to recompute")
        return None

    # Fetch fresh metrics
    metrics = MetricsRepository.get_fresh_metrics(db_session, brand_id, hours)

    # Convert to response format
    result = {}
    for metric in metrics:
        result[metric.llm_name] = {
            "brandRank": metric.brand_rank,
            "citationsList": metric.citations_list,
            "mentionRate": metric.mention_rate,
            "sentimentScore": metric.sentiment_score,
        }

    # Get the oldest updated_at for computed_at
    oldest_update = min(m.updated_at for m in metrics)

    logger.info(f"Cache hit! Last computed: {oldest_update}")
    return {"metrics": result, "computed_at": oldest_update.isoformat(), "cached": True}

