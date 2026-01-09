"""Repository for Metric model operations."""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from db.models import Metric


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
        db_session: Session, brand_id: uuid.UUID, hours: int = 24
    ) -> bool:
        """Check if brand has fresh metrics for all 4 LLMs.
        
        Args:
            db_session: Database session
            brand_id: Brand UUID
            hours: Number of hours to consider "fresh"
            
        Returns:
            True if all 4 LLMs have fresh metrics
        """
        fresh_metrics = MetricsRepository.get_fresh_metrics(db_session, brand_id, hours)
        llm_names = {m.llm_name for m in fresh_metrics}
        required_llms = {"chatgpt", "gemini", "grok", "perplexity"}
        return required_llms.issubset(llm_names)

