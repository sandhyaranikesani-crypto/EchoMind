"""Application configuration and environment settings for EchoMind.

Never hard-code secrets or API keys. Settings are dynamically loaded
from the environment with sensible defaults for local development.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Default root directory for EchoMind
BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    """Immutable environment settings container."""
    # Database
    DB_PATH: str = os.getenv("ECHOMIND_DB_PATH", str(BASE_DIR / "echomind.db"))

    # Hindsight Memory Engine
    HINDSIGHT_BASE_URL: str = os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888")
    HINDSIGHT_API_KEY: str = os.getenv("HINDSIGHT_API_KEY", "")
    HINDSIGHT_USE_MOCK: bool = os.getenv("HINDSIGHT_USE_MOCK", "false").lower() in ("true", "1", "yes")
    HINDSIGHT_REFLECT_BUDGET: str = os.getenv("HINDSIGHT_REFLECT_BUDGET", "low")
    DEFAULT_STRATEGY_PHASE: str = os.getenv("DEFAULT_STRATEGY_PHASE", "default")

    # LLM Provider Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: Optional[str] = os.getenv("OPENAI_BASE_URL", None)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()


def get_brand_bank_id(brand_id: str) -> str:
    """Derive a deterministic, collision-safe Hindsight bank ID from SQLite brand ID.

    Guarantees strict tenant isolation across memory banks.
    Never uses human-readable or mutable brand names.
    """
    if not brand_id or not brand_id.strip():
        raise ValueError("brand_id must be a non-empty string.")
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", brand_id.strip().lower())
    return f"echomind_{sanitized}"


def get_memory_adapter(s: Optional[Settings] = None):
    """Factory creating the appropriate MemoryAdapter.

    Uses MockMemoryAdapter ONLY when HINDSIGHT_USE_MOCK=True.
    Otherwise instantiates HindsightMemoryAdapter.
    """
    from memory.hindsight_adapter import HindsightMemoryAdapter
    from memory.mock_adapter import MockMemoryAdapter

    active_settings = s or settings
    if active_settings.HINDSIGHT_USE_MOCK:
        return MockMemoryAdapter()
    return HindsightMemoryAdapter(
        base_url=active_settings.HINDSIGHT_BASE_URL,
        api_key=active_settings.HINDSIGHT_API_KEY or None,
    )
