"""Configuration module for Neuro-Triage."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None

    # PostgreSQL
    db_user: str = "neuro_user"
    db_password: str = "secure_password_here"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "neuro_triage"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Langfuse
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_base_url: Optional[str] = None

    # Application
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Safety Thresholds
    hallucination_threshold: float = 0.3
    safety_score_min: int = 4
    triage_recall_target: float = 0.98

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Streamlit
    streamlit_port: int = 8501

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )


# Global settings instance
settings = Settings()
