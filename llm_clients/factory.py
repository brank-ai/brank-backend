"""Factory for creating LLM clients."""

import logging
from typing import Dict
from config import Settings
from llm_clients.chatgpt import ChatGPTClient
from llm_clients.gemini import GeminiClient
from llm_clients.grok import GrokClient
from llm_clients.perplexity import PerplexityClient
from llm_clients.base import LLMClient


def create_llm_clients(settings: Settings, logger: logging.Logger) -> Dict[str, LLMClient]:
    """Create LLM clients only for available API keys.

    Args:
        settings: Application settings with API keys
        logger: Logger instance

    Returns:
        Dictionary mapping LLM names to client instances (only for available keys)

    Example:
        clients = create_llm_clients(settings, logger)
        response = clients['chatgpt'].query("What is Python?")
    """
    clients = {}

    # Only create clients for non-empty API keys
    if settings.chatgpt_api_key and settings.chatgpt_api_key.strip():
        clients["chatgpt"] = ChatGPTClient(
            api_key=settings.chatgpt_api_key, logger=logger
        )
        logger.info("✓ ChatGPT client created")
    else:
        logger.warning("⊗ ChatGPT client skipped (no API key)")

    if settings.gemini_api_key and settings.gemini_api_key.strip():
        clients["gemini"] = GeminiClient(
            api_key=settings.gemini_api_key, logger=logger
        )
        logger.info("✓ Gemini client created")
    else:
        logger.warning("⊗ Gemini client skipped (no API key)")

    # Grok and Perplexity disabled — not actively used
    logger.info("⊗ Grok client disabled")
    logger.info("⊗ Perplexity client disabled")

    logger.info(f"Created {len(clients)}/{4} LLM clients: {list(clients.keys())}")
    return clients

