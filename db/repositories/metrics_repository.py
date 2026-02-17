"""Repository for Metric model operations."""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy import func
from sqlalchemy.orm import Session

from db.models import Metric, Brand


class MetricsRepository:
    """Data access layer for Metric model."""

    @staticmethod
    def create(
        db_session: Session,
        brand_id: uuid.UUID,
        llm_name: str,
        mention_rate: float,
        citations_list: List[Dict[str, float]],
        sentiment_score: float,
        brand_rank: Optional[float],
    ) -> Metric:
        """Create new metric.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            llm_name: LLM name
            mention_rate: 0.0 to 1.0
            citations_list: Top 5 URLs with percentages
            sentiment_score: 0.0 to 100.0
            brand_rank: Average rank or None
            
        Returns:
            Created Metric instance
        """
        metric = Metric(
            brand_id=brand_id,
            llm_name=llm_name,
            mention_rate=mention_rate,
            citations_list=citations_list,
            sentiment_score=sentiment_score,
            brand_rank=brand_rank,
        )
        db_session.add(metric)
        db_session.flush()
        return metric

    @staticmethod
    def upsert(
        db_session: Session,
        brand_id: uuid.UUID,
        llm_name: str,
        mention_rate: float,
        citations_list: List[Dict[str, float]],
        sentiment_score: float,
        brand_rank: Optional[float],
    ) -> Metric:
        """Create or update metric.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            llm_name: LLM name
            mention_rate: 0.0 to 1.0
            citations_list: Top 5 URLs with percentages
            sentiment_score: 0.0 to 100.0
            brand_rank: Average rank or None
            
        Returns:
            Metric instance (created or updated)
        """
        metric = (
            db_session.query(Metric)
            .filter(Metric.brand_id == brand_id, Metric.llm_name == llm_name)
            .first()
        )

        if metric is None:
            # Create new
            metric = MetricsRepository.create(
                db_session,
                brand_id,
                llm_name,
                mention_rate,
                citations_list,
                sentiment_score,
                brand_rank,
            )
        else:
            # Update existing
            metric.mention_rate = mention_rate
            metric.citations_list = citations_list
            metric.sentiment_score = sentiment_score
            metric.brand_rank = brand_rank
            metric.updated_at = datetime.utcnow()
            db_session.flush()

        return metric

    @staticmethod
    def get_by_brand(db_session: Session, brand_id: uuid.UUID) -> List[Metric]:
        """Get all metrics for a brand.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            
        Returns:
            List of Metric instances
        """
        return db_session.query(Metric).filter(Metric.brand_id == brand_id).all()

    @staticmethod
    def get_fresh_metrics(
        db_session: Session, brand_id: uuid.UUID, hours: int = 24
    ) -> List[Metric]:
        """Get metrics updated within specified hours.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            hours: Number of hours to consider "fresh"
            
        Returns:
            List of Metric instances updated within timeframe
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return (
            db_session.query(Metric)
            .filter(Metric.brand_id == brand_id, Metric.updated_at > cutoff)
            .all()
        )

    @staticmethod
    def has_fresh_cache(
        db_session: Session,
        brand_id: uuid.UUID,
        active_llm_names: List[str],
        hours: int = 24,
    ) -> bool:
        """Check if brand has fresh metrics for all active LLMs.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            active_llm_names: List of currently active LLM names to check
            hours: Number of hours to consider "fresh"
            
        Returns:
            True if all active LLMs have fresh metrics
        """
        fresh_metrics = MetricsRepository.get_fresh_metrics(db_session, brand_id, hours)
        llm_names = {m.llm_name for m in fresh_metrics}
        required_llms = set(active_llm_names)
        return required_llms.issubset(llm_names)

    @staticmethod
    def get_avg_metrics_by_brand_names(
        db_session: Session, brand_names: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Get average mention rates and sentiment scores for brands by name.

        Args:
            db_session: Database session
            brand_names: List of brand names to lookup (case-insensitive)

        Returns:
            Dictionary mapping lowercase brand name to
            {"mention_rate": 0.0-1.0, "sentiment_score": 0.0-100.0}
        """
        if not brand_names:
            return {}

        lowercase_names = [name.lower() for name in brand_names]

        results = (
            db_session.query(
                func.lower(Brand.name).label("brand_name"),
                func.avg(Metric.mention_rate).label("avg_mention_rate"),
                func.avg(Metric.sentiment_score).label("avg_sentiment_score"),
            )
            .join(Metric, Brand.brand_id == Metric.brand_id)
            .filter(func.lower(Brand.name).in_(lowercase_names))
            .group_by(func.lower(Brand.name))
            .all()
        )

        return {
            row.brand_name: {
                "mention_rate": float(row.avg_mention_rate),
                "sentiment_score": float(row.avg_sentiment_score),
            }
            for row in results
        }

