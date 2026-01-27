"""SQLAlchemy database models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from db import Base


class Brand(Base):
    """Brand entity."""

    __tablename__ = "brands"

    brand_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    website = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    prompts = relationship("Prompt", back_populates="brand", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="brand", cascade="all, delete-orphan")
    time_profiles = relationship("TimeProfile", back_populates="brand", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Brand(brand_id={self.brand_id}, name={self.name}, website={self.website})>"


class Prompt(Base):
    """User prompt/question for a brand."""

    __tablename__ = "prompts"

    prompt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.brand_id"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    brand = relationship("Brand", back_populates="prompts")
    responses = relationship("Response", back_populates="prompt", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Prompt(prompt_id={self.prompt_id}, brand_id={self.brand_id})>"


class Response(Base):
    """LLM response to a prompt."""

    __tablename__ = "responses"

    response_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompts.prompt_id"), nullable=False)
    llm_name = Column(
        String(50), nullable=False
    )  # 'chatgpt', 'gemini', 'grok', 'perplexity'
    answer = Column(Text, nullable=False)
    brands_list = Column(JSON, nullable=False)  # Ordered array of brand names
    citation_list = Column(JSON, nullable=False)  # Array of URLs
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    prompt = relationship("Prompt", back_populates="responses")

    # Indexes
    __table_args__ = (
        Index("ix_responses_prompt_llm", "prompt_id", "llm_name"),
        Index("ix_responses_llm_name", "llm_name"),
    )

    def __repr__(self) -> str:
        return f"<Response(response_id={self.response_id}, prompt_id={self.prompt_id}, llm_name={self.llm_name})>"


class Metric(Base):
    """Calculated metrics for a brand per LLM."""

    __tablename__ = "metrics"

    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.brand_id"), nullable=False)
    llm_name = Column(
        String(50), nullable=False
    )  # 'chatgpt', 'gemini', 'grok', 'perplexity'
    mention_rate = Column(Float, nullable=False)  # 0.0 to 1.0
    citations_list = Column(
        JSON, nullable=False
    )  # Array of {url, percentage} (top 5)
    sentiment_score = Column(Float, nullable=False)  # 0.0 to 100.0
    brand_rank = Column(Float, nullable=True)  # Average rank, null if never appears
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    brand = relationship("Brand", back_populates="metrics")

    # Indexes
    __table_args__ = (
        Index("ix_metrics_brand_llm", "brand_id", "llm_name", unique=True),
        Index("ix_metrics_brand_updated", "brand_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<Metric(metric_id={self.metric_id}, brand_id={self.brand_id}, llm_name={self.llm_name})>"


class TimeProfile(Base):
    """Performance timing for each request."""

    __tablename__ = "time_profiling"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.brand_id"), nullable=False, index=True)
    request_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    prompt_generation_time = Column(Float, nullable=False)  # seconds
    fetching_llm_response_time = Column(Float, nullable=False)  # seconds
    processing_response_time = Column(Float, nullable=False)  # seconds
    metrics_calculation_time = Column(Float, nullable=False)  # seconds
    aggregation_time = Column(Float, nullable=False, default=0.0)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    brand = relationship("Brand", back_populates="time_profiles")

    def __repr__(self) -> str:
        return f"<TimeProfile(profile_id={self.profile_id}, brand_id={self.brand_id}, request_id={self.request_id})>"


class BrandInsightRequest(Base):
    """Brand insight request from the landing page modal."""

    __tablename__ = "brand_insight_requests"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<BrandInsightRequest(request_id={self.request_id}, brand_name={self.brand_name}, email={self.email})>"

