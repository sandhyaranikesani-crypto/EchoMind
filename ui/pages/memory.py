"""Memory page: Memory bank inspector, belief timeline, and evidence provenance."""

import altair as alt
import pandas as pd
import streamlit as st

from config.settings import get_brand_bank_id
from database.repository import ContentRepository
from memory.base import HindsightUnavailableError
from ui.styles import render_header, badge_html


def _memory_kind(item: dict) -> str:
    memory_type = str(item.get("type", "")).lower().rsplit(".", 1)[-1]
    if memory_type in {"world", "fact", "factual", "world_fact"}:
        return "World fact"
    if memory_type in {"experience", "experiential"}:
        return "Experience"
    if memory_type in {"belief", "observation", "inferred"}:
        return "Belief"
    return "Other"


def render_memory() -> None:
    brand_id = st.session_state.get("active_brand_id")
    brand_name = st.session_state.get("active_brand_name", "Unknown brand")
    agent = st.session_state.get("agent")
    repo: ContentRepository = st.session_state.get("repository", ContentRepository())

    if not agent or not brand_id:
        st.info("Select a brand from the sidebar to inspect its memory bank.")
        return

    render_header(
        "Memory bank inspector",
        f"Granular inspection of long-term memory stored for {brand_name}.",
    )

    bank_id = get_brand_bank_id(brand_id)

    # Tenant isolation banner
    st.markdown(
        f"""
        <div class="em-card">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div>
                    <strong>Isolated memory bank:</strong> <code>{bank_id}</code><br>
                    <span class="em-muted">
                        Tenant isolation guarantees zero cross-brand memory leakage. Switch brands in the sidebar to verify.
                    </span>
                </div>
                <div>
                    {badge_html("Memory online" if agent.memory_online else "Memory offline", "success" if agent.memory_online else "danger", dot=True)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not agent.memory_online:
        st.warning("Memory backend is offline. Deterministic strategy analysis remains available.")
        return

    # Actions row
    c_btn1, c_btn2 = st.columns([1, 1.5])
    with c_btn1:
        if st.button("Refresh memory ledger", use_container_width=True):
            try:
                with st.spinner("Fetching memories from Hindsight..."):
                    st.session_state.ledger = agent.memory_ledger(brand_id)
            except HindsightUnavailableError as exc:
                st.error("The memory ledger could not be refreshed. The memory backend may be unavailable.")
    with c_btn2:
        if st.button("Seed demo brand memory", use_container_width=True):
            try:
                with st.spinner("Writing initial brand rules and beliefs..."):
                    n = agent.bootstrap_demo_memory(brand_id)
                    st.session_state.ledger = agent.memory_ledger(brand_id)
                st.success(f"Wrote {n} memory records to bank '{bank_id}'.")
            except HindsightUnavailableError as exc:
                st.error("Demo memories could not be written. The memory backend may be unavailable.")

    # Auto-load ledger if not yet fetched
    if "ledger" not in st.session_state or st.session_state.get("last_ledger_brand") != brand_id:
        try:
            st.session_state.ledger = agent.memory_ledger(brand_id)
            st.session_state.last_ledger_brand = brand_id
        except Exception:
            st.session_state.ledger = []

    ledger = st.session_state.get("ledger", [])

    if not ledger:
        st.info(
            "The memory bank is currently empty for this brand. Click 'Seed demo brand memory' "
            "above or submit feedback on the Learning page to begin recording memories."
        )
        return

    # Filters operate on the same normalized ledger for each adapter.
    filter_col, phase_col = st.columns(2)
    with filter_col:
        selected_type = st.selectbox(
            "Memory type",
            ["All types", "World fact", "Experience", "Belief", "Other"],
        )
    phases = sorted({str(item.get("phase") or "Unspecified") for item in ledger})
    with phase_col:
        selected_phase = st.selectbox("Strategy phase", ["All phases", *phases])

    filtered_ledger = [
        item for item in ledger
        if (selected_type == "All types" or _memory_kind(item) == selected_type)
        and (selected_phase == "All phases" or str(item.get("phase") or "Unspecified") == selected_phase)
    ]
    facts = [it for it in filtered_ledger if _memory_kind(it) == "World fact"]
    experiences = [it for it in filtered_ledger if _memory_kind(it) == "Experience"]
    beliefs = [it for it in filtered_ledger if _memory_kind(it) == "Belief"]

    # KPI counts
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Filtered items", len(filtered_ledger))
    with k2:
        st.metric("World facts (rules)", len(facts))
    with k3:
        st.metric("Active beliefs", len(beliefs))
    with k4:
        st.metric("Episodic experiences", len(experiences))

    st.markdown("---")

    # Inspector Tabs
    tab_beliefs, tab_facts, tab_experiences = st.tabs(
        ["Active beliefs & timeline", "World facts (guardrails)", "Episodic experiences"]
    )

    # 1. Beliefs Tab
    with tab_beliefs:
        st.subheader("Consolidated strategic beliefs")
        st.caption(
            "Beliefs synthesized by Hindsight observations from accumulated evidence, "
            "complete with causal rationale and database evidence pointers."
        )

        if not beliefs:
            st.caption("No strategic beliefs recorded yet.")
        else:
            # Timeline chart if multiple beliefs or timestamped
            timeline_data = []
            for b in beliefs:
                learned_at = b.get("learned_at") or b.get("when")
                confidence = b.get("confidence")
                if learned_at and confidence is not None:
                    timeline_data.append(
                        {
                            "Belief": b.get("text", ""),
                            "Confidence": float(confidence),
                            "Learned at": pd.to_datetime(learned_at, errors="coerce"),
                        }
                    )

            tdf = pd.DataFrame(timeline_data)
            if not tdf.empty:
                tdf = tdf.dropna(subset=["Learned at"])
            if not tdf.empty:
                chart = (
                    alt.Chart(tdf)
                    .mark_line(point=True, strokeWidth=2)
                    .encode(
                        x=alt.X("Learned at:T", title="Learned at"),
                        y=alt.Y("Confidence:Q", scale=alt.Scale(domain=[0, 1]), title="Confidence score"),
                        tooltip=["Belief", "Learned at:T", "Confidence"],
                    )
                    .properties(height=200)
                )
                st.altair_chart(chart, use_container_width=True, theme="streamlit")
            else:
                st.caption("No timestamped confidence values are available for this filtered set.")

            # Belief detail cards
            for b in beliefs:
                conf = b.get("confidence")
                why = b.get("why")
                evidence_list = b.get("evidence", [])

                with st.container(border=True):
                    st.markdown(f"**Learned principle:** {b.get('text')}")
                    if why:
                        st.markdown(f"**Causal rationale:** {why}")
                    else:
                        st.caption("Causal rationale was not returned by this memory record.")

                    b_c1, b_c2 = st.columns([1, 2])
                    with b_c1:
                            if conf is not None:
                                st.caption(f"Confidence score: {float(conf):.2f}")
                                st.progress(max(0, min(100, int(float(conf) * 100))))
                            else:
                                st.caption("Confidence score not provided")
                            st.caption(f"Learned at: {b.get('learned_at') or b.get('when') or 'Not recorded'}")
                    with b_c2:
                        if evidence_list:
                            st.caption("Supporting database evidence:")
                            for ev in evidence_list:
                                ev_label = ev
                                if "sql_post_id:" in ev:
                                    post_id = ev.replace("sql_post_id:", "").strip()
                                    try:
                                        post = repo.get_post(post_id)
                                        if post:
                                            ev_label = f"Post: '{post['title']}' ({post['engagement_rate']}% engagement)"
                                    except Exception:
                                        pass
                                st.markdown(f"- <code>{ev_label}</code>", unsafe_allow_html=True)
                        else:
                            st.caption("Evidence pointers were not returned by this memory record.")

    # 2. World Facts Tab
    with tab_facts:
        st.subheader("Objective brand rules & constraints")
        st.caption("Factual constraints and voice boundaries retained in the brand's long-term memory.")

        if not facts:
            st.caption("No brand facts stored yet.")
        else:
            for f in facts:
                st.markdown(f"- {f.get('text')}")

    # 3. Episodic Experiences Tab
    with tab_experiences:
        st.subheader("Historical decisions & feedback")
        st.caption("Episodic log of editorial reviews (acceptances, edits, rejections) retained from marketer interactions.")

        if not experiences:
            st.caption("No episodic experiences recorded yet.")
        else:
            for exp in experiences:
                when_str = f" · {exp['when']}" if exp.get("when") else ""
                dec = exp.get("decision", "REVIEW")
                var = "success" if dec == "accept" else ("danger" if dec == "reject" else "warning")
                with st.container(border=True):
                    st.markdown(badge_html(dec.upper(), var) + f"<span class='em-muted'>{when_str}</span>", unsafe_allow_html=True)
                    st.markdown(exp.get("text", ""))


if __name__ == "__main__":
    render_memory()
