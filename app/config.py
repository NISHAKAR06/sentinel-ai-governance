"""
config.py — Sentinel AI Governance Platform
Centralised application configuration via environment variables.
"""
import os
from pathlib import Path
from functools import lru_cache
from typing import List


class Settings:
    # ── App ──────────────────────────────────────────────────
    APP_NAME: str         = "Sentinel AI Governance"
    APP_VERSION: str      = "2.0.0"
    DEBUG: bool           = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY: str       = os.getenv("SECRET_KEY", "sentinel-secret-change-in-production-x9k2p")

    # ── Server ───────────────────────────────────────────────
    HOST: str             = os.getenv("HOST", "0.0.0.0")
    PORT: int             = int(os.getenv("PORT", "8000"))

    # ── Paths ─────────────────────────────────────────────────
    BASE_DIR: Path        = Path(__file__).parent
    STATIC_DIR: Path      = BASE_DIR / "static"
    TEMPLATES_DIR: Path   = BASE_DIR / "templates"

    # ── Database ──────────────────────────────────────────────
    # Defaults to SQLite for local dev; set DATABASE_URL in .env for PostgreSQL
    _default_db_path: Path = BASE_DIR.parent / "sentinel.db"
    DATABASE_URL: str     = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{_default_db_path}"
    )
    DATABASE_ECHO: bool   = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    DB_POOL_SIZE: int     = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int  = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # ── Alembic (sync URL for migrations) ─────────────────────
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        f"sqlite:///{_default_db_path}"
    )

    # ── JWT Auth ──────────────────────────────────────────────
    JWT_SECRET: str       = os.getenv("JWT_SECRET", SECRET_KEY)
    JWT_ALGORITHM: str    = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    # ── Gemini LLM ────────────────────────────────────────────
    GEMINI_API_KEY: str   = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str     = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    LLM_MAX_TOKENS: int   = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    LLM_TIMEOUT: int      = int(os.getenv("LLM_TIMEOUT", "30"))

    # ── Risk Thresholds ───────────────────────────────────────
    AUTO_APPROVE_THRESHOLD: int   = int(os.getenv("AUTO_APPROVE_THRESHOLD", "30"))
    CONFIRM_THRESHOLD: int        = int(os.getenv("CONFIRM_THRESHOLD", "60"))
    HUMAN_REVIEW_THRESHOLD: int   = int(os.getenv("HUMAN_REVIEW_THRESHOLD", "80"))

    # ── Adaptive Learning ─────────────────────────────────────
    LEARNING_RATE: float  = float(os.getenv("LEARNING_RATE", "0.1"))
    LEARNING_ENABLED: bool = os.getenv("LEARNING_ENABLED", "true").lower() == "true"
    MIN_SAMPLES_TO_LEARN: int = int(os.getenv("MIN_SAMPLES_TO_LEARN", "5"))

    # ── WebSocket ─────────────────────────────────────────────
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))

    # ── CORS ─────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://localhost:3000").split(",")

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str        = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str       = "json"

    # ── Business rules ────────────────────────────────────────
    BUSINESS_HOURS_START: int = int(os.getenv("BUSINESS_HOURS_START", "9"))
    BUSINESS_HOURS_END: int   = int(os.getenv("BUSINESS_HOURS_END", "18"))
    PROTECTED_TABLES: List[str] = ["employees", "settings", "audit_logs"]
    RESTRICTED_OPERATIONS: List[str] = ["DELETE", "TRUNCATE", "DROP"]

    # ── i18n ─────────────────────────────────────────────────
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
