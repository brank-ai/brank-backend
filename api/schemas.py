"""Pydantic schemas for API request/response validation."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    """Citation with percentage."""

    url: str
    percentage: float


class LLMMetrics(BaseModel):
    """Metrics for a single LLM."""

    brandRank: Optional[float] = Field(None, description="Average brand rank (1-based)")
    citationsList: List[CitationItem] = Field(default_factory=list, description="Top 5 URLs")
    mentionRate: float = Field(..., ge=0.0, le=1.0, description="Fraction 0-1")
    sentimentScore: float = Field(..., ge=0.0, le=100.0, description="Score 0-100")


class LLMError(BaseModel):
    """Error response for LLM failure."""

    error: str
    status: str = "failed"


class MetricsResponse(BaseModel):
    """Response from /metric endpoint."""

    brand_id: str
    website: str
    cached: bool
    metrics: Dict[str, LLMMetrics | LLMError]
    computed_at: str


class ErrorResponse(BaseModel):
    """Generic error response."""

    error: str

