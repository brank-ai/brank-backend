"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM API Keys
    chatgpt_api_key: str
    gemini_api_key: str
    grok_api_key: str
    perplexity_api_key: str

    # Pipeline Configuration
    prompts_n: int = 10

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
        """Validate that all required API keys are present and non-empty."""
        required_keys = {
            "CHATGPT_API_KEY": self.chatgpt_api_key,
            "GEMINI_API_KEY": self.gemini_api_key,
            "GROK_API_KEY": self.grok_api_key,
            "PERPLEXITY_API_KEY": self.perplexity_api_key,
        }

        missing_keys = [
            key for key, value in required_keys.items() if not value or value == ""
        ]

        if missing_keys:
            raise ValueError(
                f"Missing required API keys: {', '.join(missing_keys)}. "
                f"Please set them in your .env file."
            )


# Global settings instance (loaded once at startup)
def get_settings() -> Settings:
    """Get application settings instance.
    
    Returns:
        Settings instance loaded from environment
        
    Raises:
        ValueError: If required configuration is missing
    """
    return Settings()

