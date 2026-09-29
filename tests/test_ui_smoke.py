from pathlib import Path
from types import SimpleNamespace

import agent.llm as llm_module
from agent.orchestrator import EchoMindAgent
from database.repository import ContentRepository
from database.seed import seed_database
from memory.base import HindsightUnavailableError
from memory.mock_adapter import MockMemoryAdapter
from streamlit.testing.v1 import AppTest


class _UnavailableMemory(MockMemoryAdapter):
    def recall_strategic_context(self, *args, **kwargs):
        raise HindsightUnavailableError("simulated unreachable Hindsight endpoint")


def test_every_registered_page_renders_with_mock_memory(monkeypatch):
    monkeypatch.setenv("HINDSIGHT_USE_MOCK", "true")
    app_path = Path(__file__).resolve().parents[1] / "ui" / "app.py"
    app = AppTest.from_file(str(app_path), default_timeout=20).run()
    assert not app.exception, [str(error.value) for error in app.exception]

    for page_path in (
        "pages/overview.py",
        "pages/strategy.py",
        "pages/learning.py",
        "pages/memory.py",
        "pages/ask.py",
        "pages/system.py",
    ):
        app.switch_page(page_path).run()
        assert not app.exception, f"{page_path}: {[str(error.value) for error in app.exception]}"


def test_strategy_discloses_unreachable_hindsight(tmp_path, monkeypatch):
    db_path = tmp_path / "unreachable.db"
    seed_database(str(db_path))
    repository = ContentRepository(db_path=str(db_path))
    agent = EchoMindAgent(repository=repository, memory=_UnavailableMemory())
    monkeypatch.setattr(
        llm_module,
        "settings",
        SimpleNamespace(LLM_API_KEY="", LLM_BASE_URL=None, LLM_MODEL="test"),
    )

    page_path = Path(__file__).resolve().parents[1] / "ui" / "pages" / "strategy.py"
    page = AppTest.from_file(str(page_path), default_timeout=20)
    page.session_state["active_brand_id"] = "brand_echomind"
    page.session_state["active_brand_name"] = "EchoMind AI"
    page.session_state["active_platform_id"] = None
    page.session_state["agent"] = agent
    page.run()
    next(button for button in page.button if button.label == "Generate recommendation").click().run()

    assert not page.exception, [str(error.value) for error in page.exception]
    assert page.session_state["comparison"]["memory_online"] is False
    assert any("Hindsight could not be reached" in str(item.value) for item in page.warning)
