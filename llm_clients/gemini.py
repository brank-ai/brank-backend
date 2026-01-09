"""Gemini (Google) client implementation."""

import logging
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from llm_clients.base import LLMError, LLMTimeoutError, LLMAPIError
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
            LLMAPIError: If API returns an error
        """
        try:
            self.logger.debug(f"Querying Gemini with prompt length: {len(prompt)}")

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                ),
            )

            answer = response.text
            self.logger.debug(f"Gemini response length: {len(answer)}")

            return answer

        except google_exceptions.DeadlineExceeded as e:
            self.logger.error(f"Gemini timeout: {e}")
            raise LLMTimeoutError(f"Gemini request timed out after {timeout}s") from e
        except google_exceptions.GoogleAPIError as e:
            self.logger.error(f"Gemini API error: {e}")
            raise LLMAPIError(f"Gemini API error: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected Gemini error: {e}")
            raise LLMError(f"Unexpected error: {str(e)}") from e

