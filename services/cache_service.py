"""Cache management service."""

import logging
import uuid
from typing import Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session

from db.repositories import MetricsRepository


def check_cache(
    db_session: Session,
    brand_id: uuid.UUID,
    active_llm_names: List[str],
    hours: int,
    logger: logging.Logger,
) -> Optional[Dict]:
    """Check if brand has fresh cached metrics.
    
    Args:
        db_session: Database session
        brand_id: Brand UUID
        active_llm_names: List of currently active LLM names to check
        hours: Number of hours to consider "fresh" (typically 24)
        logger: Logger instance
        
    Returns:
        Dictionary with metrics per LLM if cache is fresh, None otherwise
    """
    logger.info(
        f"Checking cache for brand {brand_id} (active LLMs: {active_llm_names})"
    )

    # Fetch all metrics for the brand (regardless of age)
    metrics = MetricsRepository.get_by_brand(db_session, brand_id)

    # Check if all active LLMs have metrics
    llm_names = {m.llm_name for m in metrics}
    required_llms = set(active_llm_names)

    if not required_llms.issubset(llm_names):
        logger.info("Cache miss - some LLMs missing metrics, need to recompute")
        return None

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

