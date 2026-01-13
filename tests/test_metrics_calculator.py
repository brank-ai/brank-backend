"""Unit tests for metrics calculator."""

import pytest
from services.metrics_calculator import (
    calculate_brand_rank,
    calculate_citations_list,
    calculate_mention_rate,
    calculate_brand_domain_citation_rate,
    calculate_all_brands_ranking,
    aggregate_metrics_across_llms,
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


def test_calculate_brand_domain_citation_rate(sample_responses, mock_logger):
    """Test brand domain citation rate calculation."""
    # samsung.com appears in 2 out of 3 responses
    rate = calculate_brand_domain_citation_rate("samsung.com", sample_responses, mock_logger)
    assert rate == pytest.approx(0.667, abs=0.01)

    # apple.com appears in 2 out of 3 responses
    rate = calculate_brand_domain_citation_rate("apple.com", sample_responses, mock_logger)
    assert rate == pytest.approx(0.667, abs=0.01)

    # google.com doesn't appear in citations
    rate = calculate_brand_domain_citation_rate("google.com", sample_responses, mock_logger)
    assert rate == 0.0


def test_calculate_all_brands_ranking(sample_responses, mock_logger):
    """Test all brands ranking calculation."""
    rankings = calculate_all_brands_ranking(sample_responses, mock_logger)

    # Should have rankings for all brands that appear
    assert "samsung" in rankings
    assert "apple" in rankings
    assert "google" in rankings

    # Samsung appears at position 1 in 2 responses: avg = 1.0
    assert rankings["samsung"] == 1.0

    # Apple appears at positions 2 and 1: avg = 1.5
    assert rankings["apple"] == 1.5

    # Google appears at positions 3, 2, 2: avg = 2.33
    assert rankings["google"] == pytest.approx(2.33, abs=0.01)

    # Rankings should be sorted by rank (ascending)
    brands_list = list(rankings.keys())
    ranks_list = list(rankings.values())
    assert ranks_list == sorted(ranks_list)  # Should be in ascending order


def test_aggregate_metrics_across_llms(mock_logger):
    """Test metrics aggregation across LLMs."""
    per_llm_metrics = {
        "chatgpt": {
            "brandRank": 1.5,
            "citationsList": [{"url": "https://samsung.com", "percentage": 80.0}],
            "mentionRate": 0.8,
            "sentimentScore": 75.0,
            "brandDomainCitationRate": 0.6,
        },
        "gemini": {
            "brandRank": 2.0,
            "citationsList": [{"url": "https://samsung.com", "percentage": 70.0}],
            "mentionRate": 0.7,
            "sentimentScore": 72.0,
            "brandDomainCitationRate": 0.55,
        },
        "grok": {
            "brandRank": 1.3,
            "citationsList": [{"url": "https://samsung.com", "percentage": 85.0}],
            "mentionRate": 0.85,
            "sentimentScore": 80.0,
            "brandDomainCitationRate": 0.65,
        },
        "perplexity": {
            "error": "Failed to query",
            "status": "failed",
        },
    }

    all_brands_ranking = {
        "samsung": 1.6,
        "apple": 2.0,
        "google": 2.5,
    }

    result = aggregate_metrics_across_llms(
        per_llm_metrics, all_brands_ranking, "Samsung", mock_logger
    )

    # Check averages (only from successful LLMs: chatgpt, gemini, grok)
    assert result["averageMentionRate"] == pytest.approx(0.783, abs=0.01)  # (0.8+0.7+0.85)/3
    assert result["citations"] == pytest.approx(0.6, abs=0.01)  # (0.6+0.55+0.65)/3
    assert result["averageSentiment"] == pytest.approx(75.7, abs=0.1)  # (75+72+80)/3
    assert result["averageRanking"] == 2  # ceil((1.5+2.0+1.3)/3) = ceil(1.6) = 2

    # Check per-LLM dicts
    assert len(result["mentionRateByLLM"]) == 4  # Includes failed LLM
    assert result["mentionRateByLLM"]["chatgpt"] == 0.8
    assert result["mentionRateByLLM"]["gemini"] == 0.7
    assert result["mentionRateByLLM"]["grok"] == 0.85
    assert result["mentionRateByLLM"]["perplexity"] == 0.0  # Default for failed

    assert len(result["citationsByLLM"]) == 4
    assert result["citationsByLLM"]["chatgpt"] == 0.6

    assert len(result["citationOverview"]) == 4
    assert result["citationOverview"]["chatgpt"][0]["url"] == "https://samsung.com"

    # Check ranking overview
    assert len(result["rankingOverview"]["topBrands"]) == 3
    assert result["rankingOverview"]["topBrands"][0]["brand"] == "samsung"
    assert result["rankingOverview"]["topBrands"][0]["rank"] == 1.6
    assert result["rankingOverview"]["currentBrand"]["brand"] == "Samsung"
    assert result["rankingOverview"]["currentBrand"]["rank"] == 1.6

    # Check rank by LLMs (only successful ones)
    assert len(result["rankByLLMs"]) == 3  # Excludes failed LLM
    assert result["rankByLLMs"]["chatgpt"] == 1.5
    assert result["rankByLLMs"]["gemini"] == 2.0
    assert result["rankByLLMs"]["grok"] == 1.3


def test_aggregate_metrics_all_llms_failed(mock_logger):
    """Test aggregation when all LLMs fail."""
    per_llm_metrics = {
        "chatgpt": {"error": "Failed", "status": "failed"},
        "gemini": {"error": "Failed", "status": "failed"},
    }

    all_brands_ranking = {}

    result = aggregate_metrics_across_llms(
        per_llm_metrics, all_brands_ranking, "Samsung", mock_logger
    )

    assert "error" in result
    assert result["error"] == "All LLM requests failed"

