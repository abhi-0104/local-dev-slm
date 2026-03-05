"""Centralized configuration for the Local Enterprise SLM application."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

class Settings:
    """Single source of truth for all application configuration."""

    # --- Project Paths ---
    ROOT_DIR: Path = ROOT_DIR
    DATA_DIR: Path = ROOT_DIR / "data"

    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{ROOT_DIR / 'data' / 'database.db'}"
    )
    SQL_DEBUG: bool = os.getenv("SQL_DEBUG", "false").lower() == "true"

    # --- Ollama ---
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_GENERATE_URL: str = f"{OLLAMA_BASE_URL}/api/generate"
    OLLAMA_TAGS_URL: str = f"{OLLAMA_BASE_URL}/api/tags"
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))

    # --- Auth ---
    SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    SESSION_TOKEN_BYTES: int = 32  # Results in 64 hex characters

    # --- AI Defaults ---
    DEFAULT_WRITER_MODEL: str = os.getenv("DEFAULT_WRITER_MODEL", "llama3.2:3b")
    DEFAULT_REVIEWER_MODEL: str = os.getenv("DEFAULT_REVIEWER_MODEL", "phi3:mini")
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    MAX_LOOP_ITERATIONS: int = int(os.getenv("MAX_LOOP_ITERATIONS", "10"))
    MAX_LOOP_TIMEOUT_SECONDS: int = int(os.getenv("MAX_LOOP_TIMEOUT", "300"))

    # --- Input Limits ---
    MAX_PROMPT_LENGTH: int = int(os.getenv("MAX_PROMPT_LENGTH", "10000"))
    MAX_CODE_LENGTH: int = int(os.getenv("MAX_CODE_LENGTH", "50000"))
    MAX_FEEDBACK_LENGTH: int = int(os.getenv("MAX_FEEDBACK_LENGTH", "5000"))

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- API Server ---
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:8501"
    ).split(",")

    def __init__(self):
        """Ensure required directories exist on startup."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


# Singleton instance — import this everywhere
settings = Settings()