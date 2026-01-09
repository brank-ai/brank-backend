"""Unit tests for extractors."""

import pytest
from extractors.brand_extractor import extract_brands
from extractors.citation_extractor import extract_citations
from extractors.sentiment_analyzer import analyze_sentiment


def test_extract_brands_known_brands(mock_logger):
    """Test extraction of known brands."""
    text = "I recommend Samsung Galaxy or Apple iPhone for best results."
    brands = extract_brands(text, mock_logger)

    assert "Samsung" in brands
    assert "Apple" in brands


def test_extract_brands_order(mock_logger):
    """Test that brands are returned in order of appearance."""
    text = "Apple is good, but Samsung is better. Google is also great."
    brands = extract_brands(text, mock_logger)

    # Check order
    apple_idx = brands.index("Apple")
    samsung_idx = brands.index("Samsung")
    google_idx = brands.index("Google")

    assert apple_idx < samsung_idx < google_idx


def test_extract_brands_deduplication(mock_logger):
    """Test that duplicate brands are not repeated."""
    text = "Samsung is great. Samsung Galaxy is amazing. Samsung phones rock."
    brands = extract_brands(text, mock_logger)

    # Samsung should appear only once
    samsung_count = sum(1 for b in brands if "samsung" in b.lower())
    assert samsung_count == 1


def test_extract_citations_basic(mock_logger):
    """Test basic URL extraction."""
    text = "Visit https://example.com for more info or check https://test.com"
    urls = extract_citations(text, mock_logger)

    assert len(urls) == 2
    assert any("example.com" in url for url in urls)
    assert any("test.com" in url for url in urls)


def test_extract_citations_deduplication(mock_logger):
    """Test that duplicate URLs are deduplicated."""
    text = "Visit https://example.com and also https://example.com again"
    urls = extract_citations(text, mock_logger)

    assert len(urls) == 1
    assert "example.com" in urls[0]


def test_extract_citations_canonicalization(mock_logger):
    """Test URL canonicalization."""
    text = "Check https://Example.com/ and https://example.com"
    urls = extract_citations(text, mock_logger)

    # Should be deduplicated after canonicalization
    assert len(urls) == 1


def test_analyze_sentiment_positive(mock_logger):
    """Test positive sentiment detection."""
    text = "Samsung makes great phones with excellent quality and amazing features!"
    score = analyze_sentiment(text, "Samsung", mock_logger)

    # Should be > 50 (positive)
    assert score > 50


def test_analyze_sentiment_negative(mock_logger):
    """Test negative sentiment detection."""
    text = "Samsung phones are terrible, bad quality, and disappointing."
    score = analyze_sentiment(text, "Samsung", mock_logger)

    # Should be < 50 (negative)
    assert score < 50


def test_analyze_sentiment_neutral(mock_logger):
    """Test neutral sentiment (brand mentioned without sentiment words)."""
    text = "Samsung is a company that makes phones."
    score = analyze_sentiment(text, "Samsung", mock_logger)

    # Should be around 50 (neutral)
    assert 40 <= score <= 60


def test_analyze_sentiment_brand_not_mentioned(mock_logger):
    """Test sentiment when brand is not mentioned."""
    text = "Apple makes great phones."
    score = analyze_sentiment(text, "Samsung", mock_logger)

    # Should return 50 (neutral) if brand not mentioned
    assert score == 50.0

