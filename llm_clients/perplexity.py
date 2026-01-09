"""Perplexity client implementation."""

import logging
import requests
from requests.exceptions import Timeout, RequestException
from llm_clients.base import LLMError, LLMTimeoutError, LLMAPIError
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
            LLMAPIError: If API returns an error
        """
        try:
            self.logger.debug(f"Querying Perplexity with prompt length: {len(prompt)}")

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

            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", response.text)
                raise LLMAPIError(
                    f"Perplexity API error (status {response.status_code}): {error_msg}"
                )

            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            self.logger.debug(f"Perplexity response length: {len(answer)}")

            return answer

        except Timeout as e:
            self.logger.error(f"Perplexity timeout: {e}")
            raise LLMTimeoutError(
                f"Perplexity request timed out after {timeout}s"
            ) from e
        except RequestException as e:
            self.logger.error(f"Perplexity request error: {e}")
            raise LLMAPIError(f"Perplexity request error: {str(e)}") from e
        except KeyError as e:
            self.logger.error(f"Perplexity response parsing error: {e}")
            raise LLMAPIError(f"Invalid Perplexity response format: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected Perplexity error: {e}")
            raise LLMError(f"Unexpected error: {str(e)}") from e

