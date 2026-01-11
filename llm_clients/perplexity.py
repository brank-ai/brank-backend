"""Perplexity client implementation."""

import logging
import time
import requests
from requests.exceptions import Timeout, RequestException
from llm_clients.base import LLMError, LLMTimeoutError, LLMAPIError, LLMRateLimitError
from utils.retry import retry_with_backoff


class PerplexityClient:
    """Perplexity client using Perplexity API."""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.perplexity.ai/chat/completions",
        model: str = "llama-3.1-sonar-small-128k-online",
        logger: logging.Logger | None = None,
    ):
        """Initialize Perplexity client.
        
        Args:
            api_key: Perplexity API key
            api_url: API endpoint URL
            model: Model name to use
            logger: Optional logger instance
        """
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.logger = logger or logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """Return LLM name."""
        return "perplexity"

    @retry_with_backoff(
        max_attempts=3, min_wait=2, max_wait=10, exceptions=(Timeout, RequestException)
    )
    def query(self, prompt: str, timeout: int = 30) -> str:
        """Send prompt to Perplexity and return response.

        Args:
            prompt: Question/prompt to send
            timeout: Maximum seconds to wait

        Returns:
            Response text from Perplexity

        Raises:
            LLMTimeoutError: If request times out
            LLMRateLimitError: If rate limit is hit
            LLMAPIError: If API returns an error
        """
        start_time = time.time()
        try:
            self.logger.debug(f"[Perplexity] Querying with prompt length: {len(prompt)}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
            }

            response = requests.post(
                self.api_url, json=payload, headers=headers, timeout=timeout
            )

            # Check for rate limit (HTTP 429)
            if response.status_code == 429:
                elapsed = time.time() - start_time
                try:
                    error_msg = response.json().get("error", {}).get("message", response.text)
                except:
                    error_msg = response.text
                self.logger.warning(
                    f"[Perplexity] ⚠ RATE LIMIT HIT after {elapsed:.2f}s | "
                    f"Error: {error_msg} | "
                    f"Please reduce request rate or upgrade your API plan"
                )
                raise LLMRateLimitError(f"Perplexity rate limit exceeded: {error_msg}")

            if response.status_code != 200:
                elapsed = time.time() - start_time
                try:
                    error_msg = response.json().get("error", {}).get("message", response.text)
                except:
                    error_msg = response.text
                self.logger.error(f"[Perplexity] ✗ API error after {elapsed:.2f}s (status {response.status_code})")
                raise LLMAPIError(
                    f"Perplexity API error (status {response.status_code}): {error_msg}"
                )

            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            elapsed = time.time() - start_time

            self.logger.info(
                f"[Perplexity] ✓ Query completed in {elapsed:.2f}s | "
                f"Prompt: {len(prompt)} chars | Response: {len(answer)} chars"
            )

            return answer

        except Timeout as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[Perplexity] ✗ Timeout after {elapsed:.2f}s: {e}")
            raise LLMTimeoutError(
                f"Perplexity request timed out after {timeout}s"
            ) from e
        except RequestException as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[Perplexity] ✗ Request error after {elapsed:.2f}s: {e}")
            raise LLMAPIError(f"Perplexity request error: {str(e)}") from e
        except KeyError as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[Perplexity] ✗ Response parsing error after {elapsed:.2f}s: {e}")
            raise LLMAPIError(f"Invalid Perplexity response format: {str(e)}") from e
        except (LLMRateLimitError, LLMTimeoutError, LLMAPIError):
            # Re-raise our custom exceptions without wrapping
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[Perplexity] ✗ Unexpected error after {elapsed:.2f}s: {e}")
            raise LLMError(f"Unexpected error: {str(e)}") from e

