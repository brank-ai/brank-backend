"""Integration tests for API endpoints."""

import pytest
from unittest.mock import Mock, patch
from app import create_app
from config import Settings


@pytest.fixture
def app():
    """Create Flask app for testing."""
    # Create test settings with fake API keys that pass validation
    test_settings = Settings(
        chatgpt_api_key="sk-proj-abcdef1234567890abcdef1234567890",
        gemini_api_key="AIzaSyAbCdEf1234567890AbCdEf1234567890",
        grok_api_key="xai-1234567890abcdefghijklmnopqrstuvwxyz",
        perplexity_api_key="pplx-1234567890abcdefghijklmnopqrstuvwxyz",
        database_url="sqlite:///:memory:",  # In-memory SQLite for testing
        prompts_n=2,
        min_llm_count=2,
        flask_env="testing",
        secret_key="test_secret",
        debug=True,
    )

    app = create_app(test_settings)
    app.config["TESTING"] = True

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_metric_endpoint_missing_website(client):
    """Test /metric endpoint without website parameter."""
    response = client.get("/metric")
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "website" in data["error"].lower()


@patch("api.routes.get_or_compute_metrics")
@patch("api.routes.create_llm_clients")
def test_metric_endpoint_success(mock_create_clients, mock_get_metrics, client):
    """Test successful /metric endpoint call."""
    # Mock LLM clients
    mock_create_clients.return_value = {
        "chatgpt": Mock(),
        "gemini": Mock(),
        "grok": Mock(),
        "perplexity": Mock(),
    }

    # Mock metrics result with new aggregated structure
    mock_get_metrics.return_value = {
        "brand_id": "test-uuid",
        "website": "samsung.com",
        "cached": False,
        "averageMentionRate": 0.8,
        "citations": 0.6,
        "averageSentiment": 75.0,
        "averageRanking": 2,
        "mentionRateByLLM": {
            "chatgpt": 0.8,
            "gemini": 0.75,
            "grok": 0.85,
            "perplexity": 0.8,
        },
        "citationsByLLM": {
            "chatgpt": 0.6,
            "gemini": 0.55,
            "grok": 0.65,
            "perplexity": 0.6,
        },
        "citationOverview": {
            "chatgpt": [{"url": "https://samsung.com", "percentage": 80.0}],
            "gemini": [{"url": "https://samsung.com", "percentage": 75.0}],
            "grok": [{"url": "https://samsung.com", "percentage": 85.0}],
            "perplexity": [{"url": "https://samsung.com", "percentage": 80.0}],
        },
        "rankingOverview": {
            "topBrands": [
                {"brand": "samsung", "rank": 1.5},
                {"brand": "apple", "rank": 2.0},
            ],
            "currentBrand": {"brand": "Samsung", "rank": 1.5},
        },
        "rankByLLMs": {
            "chatgpt": 1.5,
            "gemini": 2.0,
            "grok": 1.3,
            "perplexity": 1.2,
        },
        "computed_at": "2026-01-09T12:00:00Z",
    }

    response = client.get("/metric?website=samsung.com")
    assert response.status_code == 200

    data = response.get_json()
    assert data["brand_id"] == "test-uuid"
    assert data["website"] == "samsung.com"
    assert data["cached"] is False
    assert data["averageMentionRate"] == 0.8
    assert data["citations"] == 0.6
    assert data["averageSentiment"] == 75.0
    assert data["averageRanking"] == 2
    assert "mentionRateByLLM" in data
    assert "chatgpt" in data["mentionRateByLLM"]
    assert "citationsByLLM" in data
    assert "citationOverview" in data
    assert "rankingOverview" in data
    assert "rankByLLMs" in data

