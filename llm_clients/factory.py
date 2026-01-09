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
    """Create all LLM clients with configuration.
    
    Args:
        settings: Application settings with API keys
        logger: Logger instance
        
    Returns:
        Dictionary mapping LLM names to client instances
        
    Example:
        clients = create_llm_clients(settings, logger)
        response = clients['chatgpt'].query("What is Python?")
    """
    clients = {
        "chatgpt": ChatGPTClient(
            api_key=settings.chatgpt_api_key, logger=logger
        ),
        "gemini": GeminiClient(
            api_key=settings.gemini_api_key, logger=logger
        ),
        "grok": GrokClient(api_key=settings.grok_api_key, logger=logger),
        "perplexity": PerplexityClient(
            api_key=settings.perplexity_api_key, logger=logger
        ),
    }

    logger.info(f"Created {len(clients)} LLM clients: {list(clients.keys())}")
    return clients

