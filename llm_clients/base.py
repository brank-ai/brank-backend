"""Base LLM client protocol and exceptions."""

from typing import Protocol
from abc import abstractmethod


class LLMError(Exception):
    """Base exception for LLM errors."""

    pass


class LLMTimeoutError(LLMError):
    """Exception raised when LLM request times out."""

    pass


class LLMAPIError(LLMError):
    """Exception raised when LLM API returns an error."""

    pass


class LLMRateLimitError(LLMError):
    """Exception raised when LLM API rate limit is hit."""

    pass


class LLMClient(Protocol):
    """Protocol for LLM client implementations.
    
    All LLM clients must implement this interface for consistency.
    """

    @abstractmethod
    def query(self, prompt: str, timeout: int = 30) -> str:
        """Send prompt to LLM and return response text.
        
        Args:
            prompt: Question/prompt to send to LLM
            timeout: Maximum seconds to wait for response
            
        Returns:
            Response text from LLM
            
        Raises:
            LLMTimeoutError: If request times out
            LLMAPIError: If API returns an error
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Return LLM name.
        
        Returns:
            One of: 'chatgpt', 'gemini', 'grok', 'perplexity'
        """
        ...

