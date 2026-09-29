"""Strategy page: Recommendation generation with causal trail and draft deliverable."""

import streamlit as st

from ui.styles import render_header, badge_html


def render_strategy() -> None:
    brand_id = st.session_state.get("active_brand_id")
    brand_name = st.session_state.get("active_brand_name", "Unknown brand")
    platform_id = st.session_state.get("active_platform_id")
    agent = st.session_state.get("agent")

    if not agent or not brand_id:
        st.info("Select a brand from the sidebar to generate recommendations.")
        return

    render_header(
        "Next-content recommendation",
        f"Deterministic gap analysis paired with long-term memory for {brand_name}.",
    )

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        generate_clicked = st.button("Generate recommendation", type="primary", use_container_width=True)
    with col_info:
        st.caption(
            "Analyzes historical metrics to detect underserved pillars, then recalls "
            "brand guardrails, past feedback, and learned beliefs from Hindsight."
        )

    if generate_clicked:
        with st.spinner("Analyzing performance metrics and recalling Hindsight memory..."):
            st.session_state.comparison = agent.generate_comparison(brand_id, platform_id)
            st.session_state.pop("draft", None)

    comp = st.session_state.get("comparison")
    if not comp or comp.get("brand_id") != brand_id:
        st.info("Click 'Generate recommendation' to run the strategy engine.")
        return

    pillar = comp.get("recommended_pillar") or {}
    fmt = comp.get("recommended_format") or {}
    without = comp.get("without_memory") or {}
    withm = comp.get("with_memory") or {}
    conv = comp.get("conviction") or {}
    plan = comp.get("memory_plan") or {}
    mem_fmt = plan.get("format") or fmt
    angle = plan.get("angle")
    adjustments = plan.get("adjustments") or []

    # Recommendation Summary Metrics
    m1, m2, m3 = st.columns([1.2, 1.2, 1.6])
    with m1:
        st.metric("Target pillar", pillar.get("pillar_name", "—"))
    with m2:
        st.metric(
            "Recommended format",
            mem_fmt.get("format_name", "—"),
            delta=("Changed by memory" if plan.get("adjusted") else None),
        )
    with m3:
        score = int(conv.get("score", 0))
        label = conv.get("label", "Exploratory")
        st.caption(f"Conviction level: {label} ({score}/100)")
        st.progress(score)
        if conv.get("memory_boost"):
            st.markdown(
                badge_html(f"+{conv['memory_boost']} conviction points from memory", "info"),
                unsafe_allow_html=True,
            )

    if plan.get("adjusted"):
        st.markdown(
            f"""
            <div class="em-card" style="border-left: 3px solid #F59E0B; margin-top: 0.5rem;">
                <strong>Memory intervention:</strong> The default winning format
                (<em>{fmt.get('format_name')}</em>) was replaced with <em>{mem_fmt.get('format_name')}</em>
                because past feedback rejected the default format for this objective.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Side-by-side contrast: Without Memory vs With Hindsight Memory
    st.subheader("Causal comparison: stateless baseline vs memory-augmented")
    col_off, col_on = st.columns(2)

    with col_off:
        with st.container(border=True):
            st.markdown(badge_html("Stateless baseline (without memory)", "neutral"), unsafe_allow_html=True)
            st.caption(f"Fixed format: {fmt.get('format_name', '—')} · No historical preferences, no voice adaptation")
            st.markdown(without.get("body", "No narrative generated."))

    with col_on:
        with st.container(border=True):
            st.markdown(
                badge_html("EchoMind (with Hindsight long-term memory)", "success")
                + " "
                + badge_html(f"Source: {withm.get('source', 'deterministic')}", "info"),
                unsafe_allow_html=True,
            )
            st.caption(f"Personalized format: {mem_fmt.get('format_name', '—')}")
            if angle:
                st.markdown(f"**Learned editorial angle:** {angle}")
            st.markdown(withm.get("body", "No narrative generated."))

            if adjustments:
                st.markdown("**Memory-informed adjustments:**")
                for adj in adjustments:
                    st.markdown(f"- {adj}")

    # Causal Audit Sheet
    with st.expander("Causal audit trail: evidence behind this recommendation", expanded=True):
        st.markdown("**Deterministic numerical evidence (from SQL data):**")
        for bullet in comp.get("reasoning", []):
            st.markdown(f"- {bullet}")

        if comp.get("brand_constraints"):
            st.markdown("**Brand guardrails applied (world facts from memory):**")
            for c in comp["brand_constraints"]:
                st.markdown(f"- {c}")

        if comp.get("active_beliefs"):
            st.markdown("**Active strategic beliefs applied (Hindsight observations):**")
            for b in comp["active_beliefs"]:
                what = getattr(b, "what_was_learned", str(b))
                conf = getattr(b, "confidence_score", None)
                conf_str = f" (confidence: {conf:.2f})" if conf is not None else ""
                st.markdown(f"- {what}{conf_str}")

        if comp.get("relevant_experiences"):
            st.markdown("**Relevant past feedback honored (episodic experiences):**")
            for exp in comp["relevant_experiences"]:
                st.markdown(f"- {exp}")

    st.markdown("---")

    # Deliverable: Generate Post Draft
    st.subheader("Publication deliverable")
    st.caption("Generate ready-to-publish draft copy adhering strictly to the recommended pillar, format, and recalled voice.")

    if st.button("Generate post draft", type="secondary"):
        with st.spinner("Synthesizing draft copy using recalled brand constraints..."):
            st.session_state.draft = agent.generate_draft(brand_id, comp)

    draft = st.session_state.get("draft")
    if draft:
        with st.container(border=True):
            source_badge = badge_html(f"Draft generated via {draft.get('source', 'deterministic')}", "info")
            st.markdown(source_badge, unsafe_allow_html=True)
            st.markdown(draft.get("body", ""))


if __name__ == "__main__":
    render_strategy()
