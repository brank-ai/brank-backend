"""Unit tests for metrics calculator."""

import pytest
from services.metrics_calculator import (
    calculate_brand_rank,
    calculate_citations_list,
    calculate_mention_rate,
)


def test_calculate_brand_rank_found(sample_responses, mock_logger):
    """Test brand rank calculation when brand is found."""
    # Samsung appears at positions: [1, 1] in first two responses
    # Average: (1 + 1) / 2 = 1.0
    rank = calculate_brand_rank("Samsung", sample_responses, mock_logger)
    assert rank == 1.0


def test_calculate_brand_rank_different_positions(sample_responses, mock_logger):
    """Test brand rank with different positions."""
    # Apple appears at positions: [2, 1] in first and third responses
    # Average: (2 + 1) / 2 = 1.5
    rank = calculate_brand_rank("Apple", sample_responses, mock_logger)
    assert rank == 1.5


def test_calculate_brand_rank_not_found(sample_responses, mock_logger):
    """Test brand rank when brand never appears."""
    rank = calculate_brand_rank("Microsoft", sample_responses, mock_logger)
    assert rank is None


def test_calculate_citations_list(sample_responses, mock_logger):
    """Test citations list calculation."""
    citations = calculate_citations_list(sample_responses, mock_logger)

    # samsung.com appears in 2/3 = 66.7%
    # apple.com appears in 2/3 = 66.7%
    # gsmarena.com appears in 1/3 = 33.3%

    assert len(citations) <= 5  # Top 5
    assert all("url" in c and "percentage" in c for c in citations)

    # Check samsung.com
    samsung_citation = next((c for c in citations if "samsung" in c["url"]), None)
    assert samsung_citation is not None
    assert samsung_citation["percentage"] == pytest.approx(66.7, abs=0.1)


def test_calculate_mention_rate(sample_responses, mock_logger):
    """Test mention rate calculation."""
    # Samsung appears in 2 out of 3 responses
    rate = calculate_mention_rate("Samsung", sample_responses, mock_logger)
    assert rate == pytest.approx(0.667, abs=0.01)

    # Apple appears in 2 out of 3 responses
    rate = calculate_mention_rate("Apple", sample_responses, mock_logger)
    assert rate == pytest.approx(0.667, abs=0.01)

    # Microsoft appears in 0 out of 3 responses
    rate = calculate_mention_rate("Microsoft", sample_responses, mock_logger)
    assert rate == 0.0


def test_calculate_mention_rate_case_insensitive(sample_responses, mock_logger):
    """Test that mention rate is case-insensitive."""
    rate1 = calculate_mention_rate("samsung", sample_responses, mock_logger)
    rate2 = calculate_mention_rate("SAMSUNG", sample_responses, mock_logger)
    rate3 = calculate_mention_rate("Samsung", sample_responses, mock_logger)

    assert rate1 == rate2 == rate3

