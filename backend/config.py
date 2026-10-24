import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("finwise.config")


class Settings:
    """Application configuration settings."""

    # Google Gemini AI settings
    GOOGLE_API_KEY: str = (
        os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GEMINI_API_KEY", "").strip()
    )
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-3.8-flash").strip()
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/finwise",
    ).strip()

    # JWT Authentication settings
    JWT_SECRET: str = os.getenv(
        "JWT_SECRET",
        "finwise-dev-jwt-secret-key-2026-super-secure-change-in-production",
    ).strip()
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

    # Financial defaults
    EMERGENCY_FUND_MONTHS: int = int(os.getenv("EMERGENCY_FUND_MONTHS", "6"))
    DEFAULT_SAVINGS_RATE: float = float(os.getenv("DEFAULT_SAVINGS_RATE", "0.20"))
    CURRENCY_DEFAULT: str = os.getenv("CURRENCY_DEFAULT", "INR").strip().upper()

    @classmethod
    def is_gemini_available(cls) -> bool:
        """Check if Gemini API key is configured."""
        return bool(cls.GOOGLE_API_KEY)


settings = Settings()
