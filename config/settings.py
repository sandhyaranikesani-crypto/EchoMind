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


def _load_dotenv(path: Path) -> None:
    """Minimal, dependency-free .env loader.

    Reads KEY=VALUE lines from ``path`` and populates os.environ for any key
    that is not already set in the real environment (so real env vars always
    win). Ignores blank lines and ``#`` comments. Never overwrites existing
    values, and never logs secret values.
    """
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        # A malformed/unreadable .env must not crash the app.
        pass


# Load .env from the project root before Settings defaults are evaluated.
_load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Immutable environment settings container."""
    # Database
    DB_PATH: str = os.getenv("ECHOMIND_DB_PATH", str(BASE_DIR / "echomind.db"))

    # Hindsight Memory Engine (defaults to Hindsight Cloud).
    HINDSIGHT_BASE_URL: str = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
    HINDSIGHT_API_KEY: str = os.getenv("HINDSIGHT_API_KEY", "")
    HINDSIGHT_USE_MOCK: bool = os.getenv("HINDSIGHT_USE_MOCK", "false").lower() in ("true", "1", "yes")
    HINDSIGHT_RECALL_BUDGET: str = os.getenv("HINDSIGHT_RECALL_BUDGET", "mid")
    HINDSIGHT_REFLECT_BUDGET: str = os.getenv("HINDSIGHT_REFLECT_BUDGET", "low")
    DEFAULT_STRATEGY_PHASE: str = os.getenv("DEFAULT_STRATEGY_PHASE", "default")

    # LLM Provider Configuration.
    # Defaults target Groq (fast, generous free tier) via its OpenAI-compatible
    # endpoint. Set LLM_API_KEY (or GROQ_API_KEY) to enable LLM narratives;
    # otherwise EchoMind uses a deterministic offline narrative.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", os.getenv("GROQ_API_KEY", os.getenv("OPENAI_API_KEY", "")))
    LLM_BASE_URL: Optional[str] = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")


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
        budget=active_settings.HINDSIGHT_RECALL_BUDGET,
    )
