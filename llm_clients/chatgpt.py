"""ChatGPT (OpenAI) client implementation."""

import logging
from openai import OpenAI, OpenAIError, APITimeoutError
from llm_clients.base import LLMError, LLMTimeoutError, LLMAPIError
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
            LLMAPIError: If API returns an error
        """
        try:
            self.logger.debug(f"Querying ChatGPT with prompt length: {len(prompt)}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                timeout=timeout,
                temperature=0.7,
            )

            answer = response.choices[0].message.content
            self.logger.debug(f"ChatGPT response length: {len(answer)}")

            return answer

        except APITimeoutError as e:
            self.logger.error(f"ChatGPT timeout: {e}")
            raise LLMTimeoutError(f"ChatGPT request timed out after {timeout}s") from e
        except OpenAIError as e:
            self.logger.error(f"ChatGPT API error: {e}")
            raise LLMAPIError(f"ChatGPT API error: {str(e)}") from e
        except Exception as e:
            self.logger.error(f"Unexpected ChatGPT error: {e}")
            raise LLMError(f"Unexpected error: {str(e)}") from e

