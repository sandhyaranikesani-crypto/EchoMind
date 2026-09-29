"""EchoMind Streamlit Multipage Application.

Presentation layer for the AI Content Strategy Agent:
  - Overview: KPIs, pillar distribution, gaps, format benchmarks
  - Strategy: Next-content recommendation with causal trail and draft
  - Learning: Accept/edit/reject-with-critique loop & adaptation diff
  - Memory: Memory bank inspector, belief timeline, evidence links
  - Ask: Reflect-based conversational Q&A
  - System: Runtime status, architecture diagram, reviewer briefing

Run with:
    streamlit run ui/app.py
"""

import sys
from pathlib import Path

# Ensure project root is importable
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from config.settings import settings
from ui.context import ensure_database_ready, build_agent, MOCK_BACKEND, HINDSIGHT_BACKEND
from ui.styles import apply_custom_styles, badge_html

st.set_page_config(
    page_title="EchoMind — Content Strategy Agent",
    page_icon=":material/psychology:",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()

# Ensure database is ready
repo = ensure_database_ready()

# ---------------------------------------------------------------------------
# Minimal Sidebar Controls
# ---------------------------------------------------------------------------
st.sidebar.markdown("### EchoMind")

# Brand selection
brands = repo.list_brands()
brand_labels = {b["name"]: b["id"] for b in brands}
active_brand_name = st.sidebar.selectbox("Brand", list(brand_labels.keys()), key="sidebar_brand")
active_brand_id = brand_labels[active_brand_name]

# Platform filter
platforms = [{"id": None, "name": "All platforms"}] + repo.list_platforms()
platform_labels = {p["name"]: p["id"] for p in platforms}
active_platform_name = st.sidebar.selectbox("Platform", list(platform_labels.keys()), key="sidebar_platform")
active_platform_id = platform_labels[active_platform_name]

# Strategy phase
active_phase = st.sidebar.text_input(
    "Strategy phase",
    value=settings.DEFAULT_STRATEGY_PHASE,
    help="Filters memory recall to beliefs and experiences matching this strategic phase.",
    key="sidebar_phase",
)

active_backend = MOCK_BACKEND if settings.HINDSIGHT_USE_MOCK else HINDSIGHT_BACKEND

agent = build_agent(active_backend, active_phase)

# Save shared state for pages
st.session_state["active_brand_id"] = active_brand_id
st.session_state["active_brand_name"] = active_brand_name
st.session_state["active_platform_id"] = active_platform_id
st.session_state["active_phase"] = active_phase
st.session_state["active_backend"] = active_backend
st.session_state["agent"] = agent
st.session_state["repository"] = repo

# Backend status indicator
if agent.memory_online:
    st.sidebar.markdown(badge_html(f"Memory configured ({active_backend})", "success", dot=True), unsafe_allow_html=True)
else:
    st.sidebar.markdown(badge_html("Memory offline; deterministic mode", "warning", dot=True), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Multipage Navigation Setup
# ---------------------------------------------------------------------------
pages = {
    "Strategy & Analytics": [
        st.Page("pages/overview.py", title="Overview", icon=":material/dashboard:", default=True),
        st.Page("pages/strategy.py", title="Strategy", icon=":material/lightbulb:"),
        st.Page("pages/learning.py", title="Learning", icon=":material/model_training:"),
    ],
    "Memory & Intelligence": [
        st.Page("pages/memory.py", title="Memory", icon=":material/psychology:"),
        st.Page("pages/ask.py", title="Ask the strategist", icon=":material/chat:"),
    ],
    "Diagnostics": [
        st.Page("pages/system.py", title="System", icon=":material/dns:"),
    ],
}

nav = st.navigation(pages)
nav.run()
