"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM API Keys (optional - at least min_llm_count required)
    chatgpt_api_key: str = ""
    gemini_api_key: str = ""
    grok_api_key: str = ""
    perplexity_api_key: str = ""

    # Pipeline Configuration
    prompts_n: int = 10
    min_llm_count: int  # REQUIRED - Minimum number of LLMs needed to run

    # Database
    database_url: str

    # Timeouts and Retries
    llm_timeout_seconds: int = 30
    max_retries: int = 3
    retry_min_wait: int = 2
    retry_max_wait: int = 10

    # Flask
    flask_env: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = False

    # Logging
    log_level: str = "INFO"

    # Slack (optional - notifications disabled if empty)
    slack_webhook_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        """Initialize settings and validate required keys."""
        super().__init__(**kwargs)
        self._validate_api_keys()

    def _validate_api_keys(self) -> None:
        """Validate that minimum required API keys are present and not placeholders."""
        available_keys = {
            "CHATGPT_API_KEY": self.chatgpt_api_key,
            "GEMINI_API_KEY": self.gemini_api_key,
            "GROK_API_KEY": self.grok_api_key,
            "PERPLEXITY_API_KEY": self.perplexity_api_key,
        }

        # Placeholder patterns to reject
        placeholder_patterns = [
            "your-",
            "sk-your-",
            "your_",
            "replace-",
            "add-",
            "insert-",
            "paste-",
            "example-",
            "dummy-",
            "test-key",
            "placeholder",
            "<",
            ">",
        ]

        def is_valid_key(value: str) -> bool:
            """Check if a key is valid (not empty and not a placeholder)."""
            if not value or not value.strip():
                return False

            value_lower = value.lower()

            # Check for placeholder patterns
            for pattern in placeholder_patterns:
                if pattern in value_lower:
                    return False

            # Key must be at least 20 characters (real API keys are longer)
            if len(value.strip()) < 20:
                return False

            return True

        # Count valid keys
        present_keys = [
            key for key, value in available_keys.items() if is_valid_key(value)
        ]
        invalid_keys = [
            key for key, value in available_keys.items()
            if value and value.strip() and not is_valid_key(value)
        ]
        missing_keys = [
            key for key, value in available_keys.items() if not value or not value.strip()
        ]

        present_count = len(present_keys)

        if present_count < self.min_llm_count:
            error_msg = (
                f"Insufficient valid API keys: Found {present_count}, minimum required is {self.min_llm_count}.\n"
            )

            if present_keys:
                error_msg += f"Valid keys: {', '.join(present_keys)}\n"

            if invalid_keys:
                error_msg += f"Invalid/Placeholder keys: {', '.join(invalid_keys)} (detected as placeholders)\n"

            if missing_keys:
                error_msg += f"Missing keys: {', '.join(missing_keys)}\n"

            error_msg += f"\nPlease add {self.min_llm_count - present_count} more REAL API key(s) to your .env file."

            raise ValueError(error_msg)

        if invalid_keys:
            print(f"⚠ Warning: Placeholder API keys detected and ignored: {', '.join(invalid_keys)}")

        print(f"✓ API Keys validated: {present_count} LLMs available ({', '.join(present_keys)})")


# Global settings instance (loaded once at startup)
def get_settings() -> Settings:
    """Get application settings instance.
    
    Returns:
        Settings instance loaded from environment
        
    Raises:
        ValueError: If required configuration is missing
    """
    return Settings()

