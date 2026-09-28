"""EchoMind Streamlit UI.

Presentation layer for the AI Content Strategy Agent:
  - Strategy dashboard (pillar distribution, format performance, top posts)
  - Recommendation card with a causal audit sheet (deterministic evidence +
    recalled Hindsight memory)
  - Feedback controls (Accept / Edit / Reject + critique) that retain the
    decision back into long-term memory.

Run with:
    streamlit run ui/app.py
"""

import sys
from pathlib import Path

# Ensure the project root is importable when Streamlit runs this file directly.
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import streamlit as st

from agent.orchestrator import EchoMindAgent
from config.settings import get_brand_bank_id, settings
from database.repository import ContentRepository
from database.seed import seed_database
from memory.base import HindsightUnavailableError
from memory.mock_adapter import MockMemoryAdapter

st.set_page_config(
    page_title="EchoMind — Content Strategy Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

MOCK_BACKEND = "Mock (offline demo)"
HINDSIGHT_BACKEND = "Hindsight server"


# ---------------------------------------------------------------------------
# Look & feel
# ---------------------------------------------------------------------------
def _inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        :root {
            --bg:#0B1020; --panel:#121A32; --panel-2:#0F1730;
            --border:rgba(124,92,252,0.22); --border-strong:rgba(139,107,255,0.45);
            --purple:#8B6BFF; --blue:#4B8CFF; --pink:#F472B6; --cyan:#22D3EE;
            --green:#34D399; --text:#FFFFFF; --muted:#A9B0D0;
        }

        html, body, [class*="css"], .stMarkdown, .stMetric, button, input, textarea, select {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
        }

        /* App background with subtle neon glows */
        .stApp {
            background:
                radial-gradient(900px 500px at 12% -5%, rgba(139,107,255,0.16), transparent 55%),
                radial-gradient(800px 500px at 100% 0%, rgba(75,140,255,0.12), transparent 55%),
                radial-gradient(700px 500px at 90% 100%, rgba(34,211,238,0.06), transparent 55%),
                #0B1020;
        }
        .block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1200px; }

        h1, h2, h3 { color:#fff; letter-spacing:-0.02em; font-weight:800; }
        p, span, label, li { color:#E9EBF6; }

        /* ---------------- Sidebar: glassmorphism panel ---------------- */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(45,38,110,0.45), rgba(18,26,50,0.30));
            backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
            border-right: 1px solid var(--border-strong);
            box-shadow: 12px 0 40px rgba(90,70,200,0.12);
        }
        section[data-testid="stSidebar"] > div { padding-top: 8px; }
        section[data-testid="stSidebar"] .stRadio label,
        section[data-testid="stSidebar"] [role="radiogroup"] > label {
            padding:8px 12px; border-radius:12px; margin-bottom:4px;
            border:1px solid transparent; transition:all .15s ease;
        }
        section[data-testid="stSidebar"] [role="radiogroup"] > label:hover {
            background: rgba(124,92,252,0.10);
        }
        /* Highlight the selected memory-backend option */
        section[data-testid="stSidebar"] [role="radiogroup"] > label:has(input:checked) {
            background: linear-gradient(135deg, rgba(139,107,255,0.28), rgba(75,140,255,0.18));
            border:1px solid var(--border-strong);
            box-shadow: 0 0 0 1px rgba(139,107,255,0.22), 0 8px 22px rgba(124,92,252,0.25);
        }

        /* ---------------- Hero card ---------------- */
        .em-hero {
            position:relative; overflow:hidden; border-radius:24px; padding:32px 36px; margin-bottom:6px;
            background: linear-gradient(120deg, #211C57 0%, #3A2A82 42%, #1E3A8A 100%);
            border:1px solid var(--border-strong);
            box-shadow: 0 24px 70px rgba(70,54,160,0.38), inset 0 1px 0 rgba(255,255,255,0.07);
        }
        .em-hero::before {
            content:''; position:absolute; top:-45%; right:-8%; width:560px; height:360px;
            background: radial-gradient(circle at 30% 30%, rgba(139,107,255,0.55), transparent 60%),
                        radial-gradient(circle at 75% 60%, rgba(75,140,255,0.45), transparent 60%),
                        radial-gradient(circle at 55% 90%, rgba(244,114,182,0.30), transparent 60%);
            filter: blur(48px); opacity:.75; pointer-events:none;
        }
        .em-hero-row { position:relative; display:flex; align-items:center; gap:18px; }
        .em-hero h1 { margin:0 0 6px 0; font-size:2.3rem; font-weight:900; }
        .em-hero p  { margin:0; color:rgba(233,235,246,0.86); font-size:1.05rem; max-width:760px; }
        .em-logo {
            display:inline-flex; align-items:center; justify-content:center;
            width:56px; height:56px; border-radius:16px; font-size:28px; flex:0 0 auto;
            background: linear-gradient(135deg, rgba(139,107,255,0.9), rgba(75,140,255,0.85));
            border:1px solid rgba(255,255,255,0.18);
            box-shadow: 0 10px 26px rgba(124,92,252,0.55), inset 0 1px 0 rgba(255,255,255,0.25);
        }

        /* ---------------- Kicker + section titles ---------------- */
        .em-kicker { text-transform:uppercase; letter-spacing:.18em; font-size:.72rem;
            font-weight:700; color:#9AA2CE; margin:24px 0 2px 0; }
        .em-title { font-size:1.4rem; font-weight:800; color:#fff; margin:0 0 12px 0; }

        /* ---------------- Glass pill badges ---------------- */
        .em-pill {
            display:inline-flex; align-items:center; gap:8px; padding:6px 14px; border-radius:999px;
            font-size:.82rem; font-weight:600; color:#D7DBF5;
            background: rgba(18,26,50,0.55); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
            border:1px solid var(--border); box-shadow:0 2px 12px rgba(124,92,252,0.14);
        }
        .em-good { border-color:rgba(52,211,153,0.45); color:#8BEFC4; }
        .em-bad  { border-color:rgba(244,114,182,0.45); color:#FBC7E4; }
        .em-info { border-color:rgba(139,107,255,0.45); color:#CBBEFF; }
        .em-warn { border-color:rgba(250,204,21,0.40); color:#FDE68A; }
        .em-dot { width:9px; height:9px; border-radius:50%; background:var(--green);
            box-shadow:0 0 10px rgba(52,211,153,0.9); display:inline-block; }

        /* ---------------- Memory chips ---------------- */
        .em-chips { display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 4px 0; }
        .em-chip {
            background: rgba(18,26,50,0.6); border:1px solid var(--border); color:#D7DBF5;
            padding:8px 13px; border-radius:12px; font-size:.88rem; line-height:1.4;
            backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
        }
        .em-chip b { color:#CBBEFF; }

        /* ---------------- Metric cards ---------------- */
        [data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(18,26,50,0.75), rgba(15,23,48,0.55));
            border:1px solid var(--border); border-radius:16px; padding:16px 18px;
            box-shadow: 0 8px 26px rgba(10,14,32,0.45);
        }
        [data-testid="stMetricValue"] { font-weight:800; }
        [data-testid="stMetricLabel"] { color:var(--muted) !important; }

        /* ---------------- Buttons ---------------- */
        .stButton > button {
            border-radius:12px; font-weight:600; color:#E9EBF6;
            border:1px solid var(--border); background: rgba(18,26,50,0.6);
            padding:.55rem 1.1rem; transition: all .15s ease;
        }
        .stButton > button:hover {
            border-color:var(--border-strong); box-shadow:0 6px 18px rgba(124,92,252,0.22);
            transform: translateY(-1px);
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #8B6BFF 0%, #5B7CFF 55%, #4B8CFF 100%);
            border:none; color:#fff;
            box-shadow: 0 10px 26px rgba(124,92,252,0.45);
        }

        /* ---------------- Inputs / selects: glass ---------------- */
        [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div,
        .stTextInput input, .stTextArea textarea {
            background: rgba(18,26,50,0.6) !important;
            border:1px solid var(--border) !important; border-radius:12px !important;
            color:#fff !important;
        }
        .stTextInput input:focus, .stTextArea textarea:focus {
            border-color:var(--border-strong) !important;
            box-shadow: 0 0 0 3px rgba(139,107,255,0.20) !important;
        }

        /* ---------------- Tabs ---------------- */
        [data-baseweb="tab-list"] { gap:10px; border-bottom:1px solid rgba(124,92,252,0.14); }
        [data-baseweb="tab"] { font-weight:600; color:var(--muted); padding:8px 6px; }
        [data-baseweb="tab"][aria-selected="true"] { color:#fff; }
        [data-baseweb="tab-highlight"] {
            background: linear-gradient(90deg, #8B6BFF, #4B8CFF) !important;
            height:3px !important; border-radius:3px;
            box-shadow: 0 0 12px rgba(139,107,255,0.85);
        }

        /* ---------------- Cards / expanders ---------------- */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius:18px !important; border:1px solid var(--border) !important;
            background: linear-gradient(180deg, rgba(18,26,50,0.55), rgba(15,23,48,0.35)) !important;
            box-shadow: 0 10px 30px rgba(10,14,32,0.35);
        }
        div[data-testid="stExpander"] {
            border-radius:16px; border:1px solid var(--border);
            background: rgba(18,26,50,0.4);
        }
        hr { border-color: rgba(124,92,252,0.15); }
        [data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    st.markdown(
        """
        <div class="em-hero">
          <div class="em-hero-row">
            <span class="em-logo">🧠</span>
            <div>
              <h1>EchoMind</h1>
              <p>The content strategist that remembers what worked, learns your brand voice, and never repeats a losing idea.</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(kicker: str, title: str) -> None:
    st.markdown(f'<div class="em-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="em-title">{title}</div>', unsafe_allow_html=True)


def pill(text: str, kind: str = "info", dot: bool = False) -> str:
    dot_html = '<span class="em-dot"></span>' if dot else ""
    return f'<span class="em-pill em-{kind}">{dot_html}{text}</span>'


def chips(items, label: str = "") -> None:
    if not items:
        return
    lead = f"<b>{label}</b> " if label else ""
    html = '<div class="em-chips">' + "".join(
        f'<span class="em-chip">{lead}{str(it)}</span>' for it in items
    ) + "</div>"
    st.markdown(html, unsafe_allow_html=True)


_inject_css()



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _mock_adapter() -> MockMemoryAdapter:
    """A single mock adapter persisted across reruns so retained memory sticks."""
    if "mock_adapter" not in st.session_state:
        st.session_state.mock_adapter = MockMemoryAdapter()
    return st.session_state.mock_adapter


@st.cache_resource(show_spinner=False)
def _hindsight_adapter(base_url: str, api_key: str, budget: str):
    """Build the Hindsight client once and reuse it across reruns.

    Streamlit re-executes this script on every interaction; without caching we
    would open a brand-new network client each time, which is the main source
    of UI latency. Cached by (base_url, api_key, budget).
    """
    from memory.hindsight_adapter import HindsightMemoryAdapter

    return HindsightMemoryAdapter(base_url=base_url, api_key=api_key or None, budget=budget)


def build_agent(backend: str, phase: str) -> EchoMindAgent:
    if backend == MOCK_BACKEND:
        return EchoMindAgent(memory=_mock_adapter(), strategy_phase=phase)
    # Hindsight: reuse a cached client. On construction failure, run
    # deterministic-only and surface the error (never silently use the mock).
    try:
        mem = _hindsight_adapter(
            settings.HINDSIGHT_BASE_URL,
            settings.HINDSIGHT_API_KEY,
            "low",  # snappier recall for interactive use
        )
        return EchoMindAgent(memory=mem, strategy_phase=phase)
    except HindsightUnavailableError as exc:
        agent = EchoMindAgent(memory=_mock_adapter(), strategy_phase=phase)
        agent.memory = None  # do not use the mock as a silent fallback
        agent.memory_error = str(exc)
        return agent


def _pillar_frame(pillars) -> pd.DataFrame:
    rows = []
    for p in pillars:
        rows.append(
            {
                "Pillar": p.get("pillar_name"),
                "Posts": p.get("post_count"),
                "Actual %": p.get("actual_share_pct"),
                "Target %": p.get("target_share_pct"),
                "Delta %": p.get("share_delta_pct"),
                "Days since last": p.get("days_since_last_post"),
                "Avg engagement %": p.get("avg_engagement_rate"),
            }
        )
    return pd.DataFrame(rows)


def _format_frame(formats) -> pd.DataFrame:
    rows = []
    for f in formats:
        rows.append(
            {
                "Format": f.get("format_name"),
                "Platform": f.get("platform_name"),
                "Posts": f.get("post_count"),
                "Avg engagement %": f.get("avg_engagement_rate"),
                "Avg clicks": f.get("avg_clicks"),
                "Avg impressions": f.get("avg_impressions"),
            }
        )
    return pd.DataFrame(rows)


def _top_posts_frame(posts) -> pd.DataFrame:
    rows = []
    for p in posts:
        rows.append(
            {
                "Title": p.get("title"),
                "Pillar": p.get("pillar_name"),
                "Format": p.get("format_name"),
                "Engagement %": p.get("engagement_rate"),
                "Clicks": p.get("clicks"),
                "Impressions": p.get("impressions"),
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sidebar: configuration
# ---------------------------------------------------------------------------
st.sidebar.markdown("### 🧠 EchoMind")
st.sidebar.caption("Content strategy that remembers.")

backend = st.sidebar.radio(
    "Memory backend",
    [MOCK_BACKEND, HINDSIGHT_BACKEND],
    index=1,
    help="Mock runs fully offline. Hindsight connects to the configured server.",
)
phase = st.sidebar.text_input("Strategy phase", value=settings.DEFAULT_STRATEGY_PHASE)

repo = ContentRepository()

# Guard: database must be seeded.
try:
    brands = repo.list_brands()
except Exception as exc:
    brands = []
    st.sidebar.error(f"Database error: {exc}")

if not brands:
    st.sidebar.warning("No brands found. Seed the demo database to begin.")
    if st.sidebar.button("Seed demo database"):
        seed_database()
        st.rerun()
    st.title("EchoMind")
    st.info("The database is empty. Use the sidebar to seed the demo dataset.")
    st.stop()

brand_labels = {b["name"]: b["id"] for b in brands}
brand_name = st.sidebar.selectbox("Brand", list(brand_labels.keys()))
brand_id = brand_labels[brand_name]

platforms = [{"id": None, "name": "All platforms"}] + repo.list_platforms()
platform_labels = {p["name"]: p["id"] for p in platforms}
platform_name = st.sidebar.selectbox("Platform", list(platform_labels.keys()))
platform_id = platform_labels[platform_name]

st.sidebar.divider()
if st.sidebar.button("Re-seed demo database"):
    seed_database()
    st.rerun()
if st.sidebar.button("Reset demo view"):
    for _k in ("comparison", "sim", "ledger", "draft", "chat"):
        st.session_state.pop(_k, None)
    st.rerun()

agent = build_agent(backend, phase)

# Memory status banner.
if agent.memory_online:
    st.sidebar.success(f"Memory online: {backend}")
    if st.sidebar.button("Seed demo brand memory"):
        try:
            with st.spinner("Writing brand facts & beliefs to Hindsight..."):
                n = agent.bootstrap_demo_memory(brand_id)
            st.sidebar.success(f"Wrote {n} memory items.")
        except HindsightUnavailableError as exc:
            st.sidebar.error(str(exc))
else:
    st.sidebar.error("Memory offline. Running deterministic only.")
    if agent.memory_error:
        st.sidebar.caption(agent.memory_error)


# ---------------------------------------------------------------------------
# Main: dashboard + recommendation
# ---------------------------------------------------------------------------
hero()

status = (
    pill("Memory online · " + backend, "good", dot=True)
    if agent.memory_online
    else pill("Memory offline · deterministic only", "bad")
)
llm_badge = pill("LLM: " + (settings.LLM_MODEL if settings.LLM_API_KEY else "deterministic"), "info")
st.markdown(
    f'<div style="margin:16px 0 6px 0; display:flex; gap:10px; flex-wrap:wrap;">'
    f'{status}{llm_badge}{pill("Brand: " + brand_name, "info")}{pill("Phase: " + phase, "info")}</div>',
    unsafe_allow_html=True,
)

section("Overview", f"Strategy dashboard — {brand_name}")

result = agent.analyze_strategy(brand_id, platform_id)
analysis = result["analysis"]

tab_dash, tab_rec, tab_learn, tab_mem, tab_ask = st.tabs(
    ["📊 Dashboard", "🎯 Recommendation", "🎬 Watch it learn", "🧠 Memory", "💬 Ask"]
)

# =========================================================================
# TAB 1 — Dashboard
# =========================================================================
with tab_dash:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total posts", analysis.total_posts)
    c2.metric("Content gaps", len(analysis.content_gaps))
    c3.metric("Saturated pillars", len(analysis.saturated_pillars))
    c4.metric("Active pillars", len(analysis.pillar_distribution))

    section("Editorial mix", "Pillar distribution & gaps")
    pillar_df = _pillar_frame(analysis.pillar_distribution)
    if not pillar_df.empty:
        st.dataframe(pillar_df, width="stretch", hide_index=True)
        st.bar_chart(pillar_df.set_index("Pillar")[["Actual %", "Target %"]])

    col_a, col_b = st.columns(2)
    with col_a:
        section("What resonates", "Format performance")
        fmt_df = _format_frame(analysis.format_performance)
        if not fmt_df.empty:
            st.dataframe(fmt_df, width="stretch", hide_index=True)
    with col_b:
        section("Benchmarks", "Top posts")
        top_df = _top_posts_frame(analysis.top_posts)
        if not top_df.empty:
            st.dataframe(top_df, width="stretch", hide_index=True)

# =========================================================================
# TAB 2 — Recommendation (memory OFF vs ON + conviction + draft + feedback)
# =========================================================================
with tab_rec:
    section("The payoff", "Next-content recommendation")
    st.caption(
        "Same analytics, narrated twice: once without memory (generic) and once "
        "with Hindsight memory (personalized to brand voice, past feedback, and evolving beliefs)."
    )

    if st.button("Generate recommendation", type="primary"):
        with st.spinner("Recalling memory and generating recommendations (Hindsight + LLM)..."):
            st.session_state.comparison = agent.generate_comparison(brand_id, platform_id)
            st.session_state.pop("draft", None)

    comp = st.session_state.get("comparison")
    if comp and comp.get("brand_id") == brand_id:
        pillar = comp.get("recommended_pillar") or {}
        fmt = comp.get("recommended_format") or {}
        without = comp.get("without_memory") or {}
        withm = comp.get("with_memory") or {}
        conv = comp.get("conviction") or {}
        plan = comp.get("memory_plan") or {}
        mem_fmt = plan.get("format") or fmt
        angle = plan.get("angle")
        adjustments = plan.get("adjustments") or []

        m1, m2, m3 = st.columns([1, 1, 1.2])
        m1.metric("Under-served pillar", pillar.get("pillar_name", "—"))
        m2.metric(
            "Format",
            mem_fmt.get("format_name", "—"),
            delta=("changed by memory" if plan.get("adjusted") else None),
        )
        with m3:
            st.caption(f"Conviction: {conv.get('label', 'n/a')}")
            st.progress(int(conv.get("score", 0)))
            if conv.get("memory_boost"):
                st.markdown(
                    pill(f"+{conv['memory_boost']} from memory", "info"),
                    unsafe_allow_html=True,
                )

        if plan.get("adjusted"):
            st.markdown(
                pill(
                    f"🧠 Memory changed the plan: {fmt.get('format_name')} → {mem_fmt.get('format_name')}",
                    "warn",
                ),
                unsafe_allow_html=True,
            )

        off_col, on_col = st.columns(2)
        with off_col:
            with st.container(border=True):
                st.markdown(pill("✕ Without memory", "bad"), unsafe_allow_html=True)
                st.caption(f"Stateless · format: {fmt.get('format_name', '—')} · no angle, no history.")
                st.markdown(without.get("body", ""))
        with on_col:
            with st.container(border=True):
                st.markdown(
                    pill("✓ With Hindsight memory", "good") + " " + pill(withm.get("source", "—"), "info"),
                    unsafe_allow_html=True,
                )
                st.caption(f"Personalized · format: {mem_fmt.get('format_name', '—')}")
                if angle:
                    st.markdown(f"**Angle (from memory):** {angle}")
                st.markdown(withm.get("body", ""))
                if adjustments:
                    st.markdown("**How memory shaped this:**")
                    for adj in adjustments:
                        st.markdown(f"- {adj}")

        if not comp.get("memory_online"):
            st.warning("Memory is offline, so both columns are identical. " + (comp.get("memory_error") or ""))
        elif not (comp.get("brand_constraints") or comp.get("active_beliefs") or comp.get("relevant_experiences")):
            st.info("Memory is online but empty for this brand. Seed demo brand memory in the sidebar, then regenerate.")

        with st.expander("Causal audit sheet: what memory contributed", expanded=True):
            st.markdown("**Deterministic evidence**")
            for bullet in comp.get("reasoning", []):
                st.markdown(f"- {bullet}")
            if comp.get("brand_constraints"):
                st.markdown("**Brand guardrails** · world facts")
                chips(comp["brand_constraints"])
            if comp.get("active_beliefs"):
                st.markdown("**Evolving beliefs** · Hindsight observations")
                chips([getattr(b, "what_was_learned", str(b)) for b in comp["active_beliefs"]])
            if comp.get("relevant_experiences"):
                st.markdown("**Relevant past feedback** · experiences")
                chips(comp["relevant_experiences"])

        # Draft generator (deliverable)
        section("Deliverable", "Turn it into a post")
        if st.button("✍️ Generate post draft (uses recalled brand voice)"):
            with st.spinner("Drafting on-brand copy..."):
                st.session_state.draft = agent.generate_draft(brand_id, comp)
        draft = st.session_state.get("draft")
        if draft:
            with st.container(border=True):
                st.markdown(pill("Draft · " + draft.get("source", "—"), "info"), unsafe_allow_html=True)
                st.markdown(draft.get("body", ""))

        # Feedback
        section("Close the loop", "Your decision")
        decision = st.radio("Decision", ["ACCEPT", "EDIT", "REJECT"], horizontal=True, key="decision")
        critique = st.text_area(
            "Critique / edit notes (optional)",
            placeholder="e.g. Good pillar, but lead with the incident timeline, not the fix.",
            key="critique",
        )
        if st.button("Submit feedback"):
            context_summary = f"a {fmt.get('format_name')} post under '{pillar.get('pillar_name')}'"
            try:
                with st.spinner("Retaining your feedback into Hindsight..."):
                    agent.record_feedback(
                        brand_id=brand_id,
                        recommendation_id=comp["recommendation_id"],
                        decision=decision,
                        context_summary=context_summary,
                        critique=critique or None,
                    )
                st.success(f"Feedback retained ({decision}). Regenerate to see the agent recall it and adapt.")
            except HindsightUnavailableError as exc:
                st.error(f"Feedback not retained. Memory is offline. {exc}")
    else:
        st.info("Click **Generate recommendation** to see the memory OFF vs ON contrast.")

# =========================================================================
# TAB 3 — Watch it learn (one-click before/after simulation)
# =========================================================================
with tab_learn:
    section("Proof", "Watch EchoMind get smarter")
    st.caption(
        "One click runs a full learning cycle: recommend → you reject with a "
        "critique → recommend again. The agent recalls the critique and adapts."
    )
    sim_critique = st.text_input(
        "Simulated critique to teach the agent",
        value="Our audience prefers deep technical teardowns and post-mortems over culture or opinion pieces. Lead with concrete incidents and metrics.",
    )
    if st.button("▶ Run learning simulation", type="primary"):
        if not agent.memory_online:
            st.warning("Memory is offline. The learning loop needs Hindsight. " + (agent.memory_error or ""))
        else:
            try:
                with st.spinner("Step 1 of 3: first recommendation..."):
                    before = agent.generate_recommendation(brand_id, platform_id)
                with st.spinner("Step 2 of 3: recording your rejection into memory..."):
                    agent.record_feedback(
                        brand_id=brand_id,
                        recommendation_id=before["recommendation_id"],
                        decision="REJECT",
                        context_summary=(
                            f"a {(before.get('recommended_format') or {}).get('format_name')} post "
                            f"under '{(before.get('recommended_pillar') or {}).get('pillar_name')}'"
                        ),
                        critique=sim_critique or None,
                    )
                with st.spinner("Step 3 of 3: recommending again, now with the lesson learned..."):
                    after = agent.generate_recommendation(brand_id, platform_id)
                st.session_state.sim = {"before": before, "after": after}
            except HindsightUnavailableError as exc:
                st.error(str(exc))

    sim = st.session_state.get("sim")
    if sim:
        before, after = sim["before"], sim["after"]
        bp = before.get("memory_plan") or {}
        ap = after.get("memory_plan") or {}
        b1, b2 = st.columns(2)
        with b1:
            with st.container(border=True):
                st.markdown(pill("Before feedback", "warn"), unsafe_allow_html=True)
                st.metric("Experiences recalled", len(before.get("relevant_experiences", [])))
                st.caption(f"Format: {(bp.get('format') or {}).get('format_name', '—')}")
                if bp.get("angle"):
                    st.markdown(f"**Angle:** {bp['angle']}")
                st.markdown((before.get("narrative") or {}).get("body", "")[:500] + " …")
        with b2:
            with st.container(border=True):
                st.markdown(pill("After feedback", "good"), unsafe_allow_html=True)
                st.metric("Experiences recalled", len(after.get("relevant_experiences", [])))
                st.caption(f"Format: {(ap.get('format') or {}).get('format_name', '—')}")
                if ap.get("angle"):
                    st.markdown(f"**Angle:** {ap['angle']}")
                st.markdown((after.get("narrative") or {}).get("body", "")[:500] + " …")
        if ap.get("adjusted"):
            st.markdown(
                pill("🧠 The recommendation itself changed after learning", "warn"),
                unsafe_allow_html=True,
            )
        if after.get("relevant_experiences"):
            st.markdown("**The lesson the agent now recalls:**")
            chips(after["relevant_experiences"])
        st.success("The 'after' side recalls your critique and adapts. That is Hindsight memory changing behavior.")

# =========================================================================
# TAB 4 — Memory ledger + tenant isolation
# =========================================================================
with tab_mem:
    section("Transparency", "EchoMind's brain")
    st.caption("Everything the agent has stored for this brand's isolated memory bank.")
    st.markdown(
        pill("Bank: " + get_brand_bank_id(brand_id), "info")
        + " " + pill("Isolated bank, no cross-brand leakage", "good"),
        unsafe_allow_html=True,
    )
    if not agent.memory_online:
        st.warning("Memory is offline. " + (agent.memory_error or ""))
    else:
        if st.button("🔄 Load memory ledger"):
            try:
                with st.spinner("Reading the memory bank..."):
                    st.session_state.ledger = agent.memory_ledger(brand_id)
            except HindsightUnavailableError as exc:
                st.error(str(exc))
        ledger = st.session_state.get("ledger")
        if ledger is not None:
            if not ledger:
                st.info("The bank is empty. Seed demo brand memory in the sidebar.")
            else:
                type_label = {"world": "🌐 World facts", "experience": "💬 Experiences",
                              "observation": "🔭 Observations", "belief": "🔭 Beliefs"}
                counts = {}
                for it in ledger:
                    counts[it["type"]] = counts.get(it["type"], 0) + 1
                cc = st.columns(max(1, len(counts)))
                for i, (t, n) in enumerate(counts.items()):
                    cc[i].metric(type_label.get(t, t), n)
                for t in ("world", "observation", "belief", "experience"):
                    rows = [it for it in ledger if it["type"] == t]
                    if rows:
                        st.markdown(
                            f'<div class="em-title" style="font-size:1.12rem;margin:20px 0 8px;">'
                            f'{type_label.get(t, t)}</div>',
                            unsafe_allow_html=True,
                        )
                        for it in rows:
                            when = f"  ·  _{it['when']}_" if it.get("when") else ""
                            st.markdown(f"- {it['text']}{when}")
        st.info(
            "Switch the Brand in the sidebar to Verdant Coffee Co. and reload to see a "
            "completely different bank. Memories never cross tenants."
        )

# =========================================================================
# TAB 5 — Ask the strategist (Hindsight reflect)
# =========================================================================
with tab_ask:
    section("Conversation", "Ask the strategist")
    st.caption("Free-form questions answered by Hindsight reflection over this brand's memory.")
    if "chat" not in st.session_state:
        st.session_state.chat = []

    for q, a in st.session_state.chat:
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            st.markdown(a)

    with st.form("ask_form", clear_on_submit=True):
        question = st.text_input(
            "Your question",
            placeholder="e.g. What kind of posts should we avoid, and why?",
        )
        asked = st.form_submit_button("Ask", type="primary")

    if asked and question:
        if not agent.memory_online:
            answer = "Memory is offline, so I can't reflect. " + (agent.memory_error or "")
        else:
            try:
                with st.spinner("Reflecting over memory..."):
                    answer = agent.ask(brand_id, question)
            except HindsightUnavailableError as exc:
                answer = f"Reflection failed: {exc}"
        st.session_state.chat.append((question, answer))
        st.rerun()


