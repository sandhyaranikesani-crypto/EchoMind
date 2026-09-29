"""System page: Diagnostics, architecture diagram, and technical reviewer briefing."""

import streamlit as st

from config.settings import get_brand_bank_id, settings
from ui.styles import render_header, badge_html


def render_system() -> None:
    brand_id = st.session_state.get("active_brand_id")
    brand_name = st.session_state.get("active_brand_name", "Unknown brand")
    agent = st.session_state.get("agent")
    backend = st.session_state.get("active_backend", "Unknown")

    render_header(
        "System diagnostics & architecture",
        "Technical overview of memory pipelines, model configuration, and system invariants.",
    )

    # Diagnostics Grid
    c_mem, c_llm, c_db = st.columns(3)

    with c_mem:
        with st.container(border=True):
            st.markdown(
                badge_html("Memory engine", "info")
                + " "
                + badge_html("Online" if agent and agent.memory_online else "Offline", "success" if agent and agent.memory_online else "danger", dot=True),
                unsafe_allow_html=True,
            )
            st.markdown(f"**Backend:** {backend}")
            st.markdown(f"**Endpoint:** `{settings.HINDSIGHT_BASE_URL}`")
            if brand_id:
                st.markdown(f"**Bank ID:** `{get_brand_bank_id(brand_id)}`")
            st.markdown(f"**Recall budget:** `{settings.HINDSIGHT_RECALL_BUDGET}`")
            st.markdown(f"**Reflect budget:** `{settings.HINDSIGHT_REFLECT_BUDGET}`")

    with c_llm:
        with st.container(border=True):
            has_key = bool(settings.LLM_API_KEY)
            st.markdown(
                badge_html("Language model", "info")
                + " "
                + badge_html("Configured" if has_key else "Deterministic fallback", "success" if has_key else "neutral"),
                unsafe_allow_html=True,
            )
            st.markdown(f"**Provider:** {settings.LLM_PROVIDER.upper()}")
            st.markdown(f"**Model:** `{settings.LLM_MODEL}`")
            st.markdown(f"**Base URL:** `{settings.LLM_BASE_URL or 'Default'}`")
            st.markdown("**Fallback:** Offline deterministic templates active")

    with c_db:
        with st.container(border=True):
            st.markdown(badge_html("Relational store", "info") + " " + badge_html("SQLite", "success"), unsafe_allow_html=True)
            st.markdown(f"**Database:** `{settings.DB_PATH.split('/')[-1].split('\\')[-1]}`")
            st.markdown("**Isolation:** Foreign-keyed multi-tenant schema")
            st.markdown("**Tenants:** EchoMind AI, Verdant Coffee Co.")
            st.markdown("**Tables:** brands, pillars, formats, posts, metrics")

    st.markdown("---")

    # Architecture Diagram
    st.subheader("System architecture")
    st.caption("Information flow from factual analytics to cognitive memory synthesis and feedback retention.")

    st.markdown(
        """
        ```mermaid
        flowchart TD
            User([Marketer / User]) -->|Review & Critique| UI[Streamlit Multipage Interface]
            UI --> Agent[EchoMind Agent Orchestrator]
            
            subgraph AnalyticsLayer [Deterministic Analytics Layer]
                Agent --> StrategyEngine[Deterministic Strategy Engine]
                StrategyEngine --> SQLite[(SQLite Database)]
                SQLite -.->|Pillar Distribution & Gap Math| StrategyEngine
            end
            
            subgraph MemoryLayer [Biomimetic Memory Layer - Hindsight]
                Agent -->|Scoped Recall & Retain| Hindsight[Hindsight Memory Engine]
                Hindsight --> Facts[World Facts: Voice, ICP, Taboos]
                Hindsight --> Experiences[Experiences: Decisions & Critiques]
                Hindsight --> Observations[Observations: Consolidated Beliefs]
            end
            
            subgraph SynthesisLayer [Synthesis & Output Layer]
                Agent --> LLM[LLM / Deterministic Narrator]
                LLM --> Deliverable[Causal Plan & Post Draft]
            end
            
            Deliverable --> User
            User -.->|Accept / Edit / Reject| Agent
        ```
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Reviewer Technical Briefing
    st.subheader("Reviewer technical briefing")
    st.caption("Key architectural decisions and design criteria for hackathon evaluation.")

    with st.expander("1. Separation of deterministic math vs cognitive memory", expanded=True):
        st.markdown(
            """
            - **Deterministic SQL Layer (WHAT to create):** Content gap calculations, historical engagement percentiles, 
              and target allocation deficits are mathematical facts. LLMs should never guess metrics or hallucinations.
            - **Cognitive Memory Layer (HOW to win it):** Hindsight stores the brand voice, editorial taboos, 
              accumulated learnings, and past human reviews. This dictates the tone, format switch, and editorial angle.
            """
        )

    with st.expander("2. Biomimetic memory pathways (Hindsight)", expanded=True):
        st.markdown(
            """
            EchoMind adheres directly to Hindsight's native memory architecture:
            - **World Facts:** Immutable brand guidelines, target ICP persona details, and strict taboo rules.
            - **Experiences:** Episodic interaction records storing the marketer's decision (ACCEPT, EDIT, REJECT) and raw critique.
            - **Observations / Beliefs:** Hindsight automatically consolidates repeated signals into evidence-backed observations over time.
            """
        )

    with st.expander("3. Memory alters decisions, not just wording", expanded=True):
        st.markdown(
            """
            A common failure of AI agent demos is having memory merely append adjectives to a prompt.
            In EchoMind, memory fundamentally alters the structural decision:
            - If past feedback rejected a format for a given objective, the agent **switches format** to the next best alternative.
            - Recalled beliefs set the specific **editorial angle** (e.g. pivoting from an opinion piece to an incident post-mortem).
            - Accumulating evidence directly boosts **conviction scores**.
            """
        )

    with st.expander("4. Resilient offline degradation", expanded=True):
        st.markdown(
            """
            EchoMind implements transparent degradation:
            - If Hindsight or the LLM is unreachable or unconfigured, the app never crashes or silently fakes state.
            - It explicitly indicates offline status and runs deterministic analytics and template narratives.
            """
        )

    with st.expander("5. Strict multi-tenant isolation", expanded=True):
        st.markdown(
            """
            - Each brand derives a deterministic, sanitized memory bank ID (`echomind_<brand_id>`).
            - Memory queries and retention calls are cryptographically isolated per bank.
            - Switching from *EchoMind AI* to *Verdant Coffee Co.* in the sidebar opens a completely different brain with zero cross-tenant contamination.
            """
        )


if __name__ == "__main__":
    render_system()
