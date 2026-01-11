"""ChatGPT (OpenAI) client implementation."""

import logging
import time
from openai import OpenAI, OpenAIError, APITimeoutError, RateLimitError
from llm_clients.base import LLMError, LLMTimeoutError, LLMAPIError, LLMRateLimitError
from utils.retry import retry_with_backoff


class ChatGPTClient:
    """ChatGPT client using OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", logger: logging.Logger | None = None):
        """Initialize ChatGPT client.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use (default: gpt-4o-mini for cost efficiency)
            logger: Optional logger instance
        """
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.logger = logger or logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """Return LLM name."""
        return "chatgpt"

    @retry_with_backoff(
        max_attempts=3, min_wait=2, max_wait=10, exceptions=(APITimeoutError,)
    )
    def query(self, prompt: str, timeout: int = 30) -> str:
        """Send prompt to ChatGPT and return response.

        Args:
            prompt: Question/prompt to send
            timeout: Maximum seconds to wait

        Returns:
            Response text from ChatGPT

        Raises:
            LLMTimeoutError: If request times out
            LLMRateLimitError: If rate limit is hit
            LLMAPIError: If API returns an error
        """
        start_time = time.time()
        try:
            self.logger.debug(f"[ChatGPT] Querying with prompt length: {len(prompt)}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
                temperature=0.7,
            )

            answer = response.choices[0].message.content
            elapsed = time.time() - start_time

            self.logger.info(
                f"[ChatGPT] ✓ Query completed in {elapsed:.2f}s | "
                f"Prompt: {len(prompt)} chars | Response: {len(answer)} chars"
            )

            return answer

        except RateLimitError as e:
            elapsed = time.time() - start_time
            self.logger.warning(
                f"[ChatGPT] ⚠ RATE LIMIT HIT after {elapsed:.2f}s | "
                f"Error: {str(e)} | "
                f"Please reduce request rate or upgrade your API plan"
            )
            raise LLMRateLimitError(f"ChatGPT rate limit exceeded: {str(e)}") from e

        except APITimeoutError as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[ChatGPT] ✗ Timeout after {elapsed:.2f}s: {e}")
            raise LLMTimeoutError(f"ChatGPT request timed out after {timeout}s") from e

        except OpenAIError as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[ChatGPT] ✗ API error after {elapsed:.2f}s: {e}")
            raise LLMAPIError(f"ChatGPT API error: {str(e)}") from e

        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[ChatGPT] ✗ Unexpected error after {elapsed:.2f}s: {e}")
            raise LLMError(f"Unexpected error: {str(e)}") from e

