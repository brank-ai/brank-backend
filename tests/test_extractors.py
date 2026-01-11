"""Unit tests for sentiment analyzer."""

import pytest
from extractors.sentiment_analyzer import analyze_sentiment


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

