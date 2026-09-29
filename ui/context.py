"""Shared application context, session state, and agent lifecycle management."""

import streamlit as st
from typing import Optional, Dict, Any, List

from agent.orchestrator import EchoMindAgent
from config.settings import settings
from database.repository import ContentRepository
from database.seed import seed_database
from memory.base import HindsightUnavailableError
from memory.mock_adapter import MockMemoryAdapter

MOCK_BACKEND = "Mock (offline demo)"
HINDSIGHT_BACKEND = "Hindsight server"


def get_mock_adapter() -> MockMemoryAdapter:
    """A single mock adapter persisted across reruns so retained memory sticks."""
    if "mock_adapter" not in st.session_state:
        st.session_state.mock_adapter = MockMemoryAdapter()
    return st.session_state.mock_adapter


@st.cache_resource(show_spinner=False)
def get_hindsight_adapter(base_url: str, api_key: str, budget: str):
    """Build the Hindsight client once and reuse it across reruns."""
    from memory.hindsight_adapter import HindsightMemoryAdapter

    return HindsightMemoryAdapter(base_url=base_url, api_key=api_key or None, budget=budget)


def build_agent(backend: str, phase: str) -> EchoMindAgent:
    """Construct or reuse the EchoMind agent for the active backend and phase."""
    if backend == MOCK_BACKEND:
        return EchoMindAgent(memory=get_mock_adapter(), strategy_phase=phase)

    try:
        mem = get_hindsight_adapter(
            settings.HINDSIGHT_BASE_URL,
            settings.HINDSIGHT_API_KEY,
            "low",  # Fast interactive recall
        )
        return EchoMindAgent(memory=mem, strategy_phase=phase)
    except HindsightUnavailableError as exc:
        agent = EchoMindAgent(memory=get_mock_adapter(), strategy_phase=phase)
        agent.memory = None  # Do not use mock as silent fallback
        agent.memory_error = str(exc)
        return agent
    except Exception as exc:
        agent = EchoMindAgent(memory=get_mock_adapter(), strategy_phase=phase)
        agent.memory = None
        agent.memory_error = str(exc)
        return agent


def ensure_database_ready() -> ContentRepository:
    """Ensure database exists and is seeded with demo data."""
    repo = ContentRepository()
    try:
        brands = repo.list_brands()
    except Exception:
        brands = []

    if not brands:
        try:
            seed_database()
            repo = ContentRepository()
        except Exception as exc:
            st.error(f"Failed to initialize database: {exc}")
    return repo
