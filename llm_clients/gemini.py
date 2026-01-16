"""Gemini (Google) client implementation."""

import logging
import time
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from llm_clients.base import LLMError, LLMTimeoutError, LLMAPIError, LLMRateLimitError
from utils.retry import retry_with_backoff


class GeminiClient:
    """Gemini client using Google Generative AI API."""

    def __init__(
        self, api_key: str, model: str = "gemini-2.5-flash-lite", logger: logging.Logger | None = None
    ):
        """Initialize Gemini client.
        
        Args:
            api_key: Google Gemini API key
            model: Model name to use (default: gemini-2.5-flash-lite)
            logger: Optional logger instance
        """
        self.api_key = api_key
        self.model_name = model
        self.logger = logger or logging.getLogger(__name__)

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    @property
    def name(self) -> str:
        """Return LLM name."""
        return "gemini"

    @retry_with_backoff(
        max_attempts=3,
        min_wait=2,
        max_wait=10,
        exceptions=(google_exceptions.DeadlineExceeded,),
    )
    def query(self, prompt: str, timeout: int = 30) -> str:
        """Send prompt to Gemini and return response.

        Args:
            prompt: Question/prompt to send
            timeout: Maximum seconds to wait (note: Gemini SDK timeout handling is limited)

        Returns:
            Response text from Gemini

        Raises:
            LLMTimeoutError: If request times out
            LLMRateLimitError: If rate limit is hit
            LLMAPIError: If API returns an error
        """
        start_time = time.time()
        try:
            self.logger.debug(f"[Gemini] Querying with prompt length: {len(prompt)}")

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                ),
            )

            answer = response.text
            elapsed = time.time() - start_time

            self.logger.info(
                f"[Gemini] ✓ Query completed in {elapsed:.2f}s | "
                f"Prompt: {len(prompt)} chars | Response: {len(answer)} chars"
            )

            return answer

        except google_exceptions.ResourceExhausted as e:
            elapsed = time.time() - start_time
            self.logger.warning(
                f"[Gemini] ⚠ RATE LIMIT HIT after {elapsed:.2f}s | "
                f"Error: {str(e)} | "
                f"Please reduce request rate or upgrade your API plan"
            )
            raise LLMRateLimitError(f"Gemini rate limit exceeded: {str(e)}") from e

        except google_exceptions.DeadlineExceeded as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[Gemini] ✗ Timeout after {elapsed:.2f}s: {e}")
            raise LLMTimeoutError(f"Gemini request timed out after {timeout}s") from e

        except google_exceptions.GoogleAPIError as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[Gemini] ✗ API error after {elapsed:.2f}s: {e}")
            raise LLMAPIError(f"Gemini API error: {str(e)}") from e

        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[Gemini] ✗ Unexpected error after {elapsed:.2f}s: {e}")
            raise LLMError(f"Unexpected error: {str(e)}") from e

