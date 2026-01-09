"""Pytest fixtures for testing."""

import pytest
from unittest.mock import Mock
import logging

from db.models import Response


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return Mock(spec=logging.Logger)


@pytest.fixture
def sample_responses():
    """Sample responses for testing metrics calculations."""
    return [
        Response(
            response_id="uuid1",
            prompt_id="prompt1",
            llm_name="chatgpt",
            answer="I recommend Samsung Galaxy and Apple iPhone",
            brands_list=["Samsung", "Apple", "Google"],
            citation_list=["https://samsung.com", "https://apple.com"],
        ),
        Response(
            response_id="uuid2",
            prompt_id="prompt2",
            llm_name="chatgpt",
            answer="Samsung makes great phones",
            brands_list=["Samsung", "Google"],
            citation_list=["https://samsung.com", "https://gsmarena.com"],
        ),
        Response(
            response_id="uuid3",
            prompt_id="prompt3",
            llm_name="chatgpt",
            answer="Apple and Google are also good",
            brands_list=["Apple", "Google"],
            citation_list=["https://apple.com"],
        ),
    ]

