"""Learning page: Accept/edit/reject feedback loop and before/after adaptation proof."""

import streamlit as st

from memory.base import HindsightUnavailableError
from ui.styles import render_header, badge_html


def render_learning() -> None:
    brand_id = st.session_state.get("active_brand_id")
    brand_name = st.session_state.get("active_brand_name", "Unknown brand")
    platform_id = st.session_state.get("active_platform_id")
    agent = st.session_state.get("agent")

    if not agent or not brand_id:
        st.info("Select a brand from the sidebar to test the learning loop.")
        return

    render_header(
        "Agent learning loop",
        f"Observe persistent behavior changes as feedback is retained into {brand_name}'s memory bank.",
    )

    # -------------------------------------------------------------------------
    # 1. Automated Learning Demonstration
    # -------------------------------------------------------------------------
    st.subheader("Automated before-and-after demonstration")
    st.caption(
        "Executes a complete cognitive cycle: generates a baseline recommendation, records a critique "
        "into Hindsight long-term memory, and regenerates to demonstrate that the agent adapts its plan."
    )

    sim_critique = st.text_input(
        "Editorial critique to teach the agent",
        value="Our audience prefers deep technical post-mortems with code and incident timelines over high-level culture essays. Lead with concrete incidents and metrics.",
    )

    if st.button("Run learning simulation", type="primary"):
        if not agent.memory_online:
            st.warning("Memory engine is currently offline. The learning loop requires an active memory backend.")
        else:
            try:
                with st.spinner("Step 1 of 3: Generating initial recommendation before feedback..."):
                    before = agent.generate_recommendation(brand_id, platform_id)

                with st.spinner("Step 2 of 3: Retaining editorial critique into Hindsight episodic memory..."):
                    context_summary = (
                        f"a {(before.get('recommended_format') or {}).get('format_name')} post "
                        f"under '{(before.get('recommended_pillar') or {}).get('pillar_name')}'"
                    )
                    agent.record_feedback(
                        brand_id=brand_id,
                        recommendation_id=before["recommendation_id"],
                        decision="REJECT",
                        context_summary=context_summary,
                        critique=sim_critique or None,
                    )

                with st.spinner("Step 3 of 3: Generating updated recommendation with new memory recalled..."):
                    after = agent.generate_recommendation(brand_id, platform_id)

                st.session_state.sim = {"before": before, "after": after}
            except HindsightUnavailableError as exc:
                st.error(f"Hindsight server error: {exc}")
            except Exception as exc:
                st.error(f"Learning cycle error: {exc}")

    sim = st.session_state.get("sim")
    if sim:
        before, after = sim["before"], sim["after"]
        bp = before.get("memory_plan") or {}
        ap = after.get("memory_plan") or {}

        before_fmt = (bp.get("format") or before.get("recommended_format") or {}).get("format_name", "—")
        after_fmt = (ap.get("format") or after.get("recommended_format") or {}).get("format_name", "—")
        before_angle = bp.get("angle", "Default generic angle")
        after_angle = ap.get("angle", "Default generic angle")

        # Before / After side-by-side cards
        c_before, c_after = st.columns(2)
        with c_before:
            with st.container(border=True):
                st.markdown(badge_html("Before feedback", "neutral"), unsafe_allow_html=True)
                st.caption(f"Experiences recalled: {len(before.get('relevant_experiences', []))}")
                st.markdown(f"**Format:** {before_fmt}")
                st.markdown(f"**Editorial angle:** {before_angle}")
                st.markdown("---")
                st.markdown((before.get("narrative") or {}).get("body", "")[:450] + "...")

        with c_after:
            with st.container(border=True):
                st.markdown(badge_html("After learning from critique", "success"), unsafe_allow_html=True)
                st.caption(f"Experiences recalled: {len(after.get('relevant_experiences', []))}")
                st.markdown(f"**Format:** {after_fmt}")
                st.markdown(f"**Editorial angle:** {after_angle}")
                st.markdown("---")
                st.markdown((after.get("narrative") or {}).get("body", "")[:450] + "...")

        # Explicit Diff Highlight
        st.markdown("---")
        st.subheader("What changed between recommendations")

        diff_col1, diff_col2, diff_col3 = st.columns(3)
        with diff_col1:
            format_changed = before_fmt != after_fmt
            status_var = "warning" if format_changed else "neutral"
            st.markdown(
                f"""
                <div class="em-card">
                    <div class="em-card-title">Format adaptation</div>
                    <strong>Before:</strong> {before_fmt}<br>
                    <strong>After:</strong> {after_fmt}<br>
                    <span style="font-size:0.8rem; color:rgba(128,128,128,0.9);">
                        {badge_html("Switched format based on rejection", status_var) if format_changed else "Format maintained"}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with diff_col2:
            angle_changed = before_angle != after_angle
            st.markdown(
                f"""
                <div class="em-card">
                    <div class="em-card-title">Editorial angle shift</div>
                    <strong>Before:</strong> {before_angle or 'None'}<br>
                    <strong>After:</strong> {after_angle or 'None'}<br>
                    <span style="font-size:0.8rem;">
                        {badge_html("Adapted angle to requested criteria", "success") if angle_changed else "Angle maintained"}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with diff_col3:
            recalled_count = len(after.get("relevant_experiences", []))
            st.markdown(
                f"""
                <div class="em-card">
                    <div class="em-card-title">Causal memory attribution</div>
                    <strong>Recalled experiences:</strong> {recalled_count}<br>
                    <strong>Triggering feedback:</strong> Past rejection retained in Hindsight.<br>
                    <span style="font-size:0.8rem;">{badge_html("Memory informed the change", "info")}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if after.get("relevant_experiences"):
            st.markdown("**Recalled feedback influencing the decision:**")
            for exp in after["relevant_experiences"]:
                st.markdown(f"- {exp}")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # 2. Interactive Feedback Submission
    # -------------------------------------------------------------------------
    st.subheader("Manual feedback submission")
    st.caption("Submit a direct review on any pending strategic recommendation to retain your decision into memory.")

    comp = st.session_state.get("comparison")
    if not comp or comp.get("brand_id") != brand_id:
        st.info("Generate a recommendation on the Strategy page first to review it here.")
        return

    pillar_name = (comp.get("recommended_pillar") or {}).get("pillar_name", "Target pillar")
    format_name = (comp.get("recommended_format") or {}).get("format_name", "Winning format")

    st.markdown(
        f"""
        <div class="em-card">
            <strong>Active recommendation target:</strong> {format_name} under <em>{pillar_name}</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

    decision = st.radio(
        "Editorial review decision",
        ["ACCEPT", "EDIT", "REJECT"],
        horizontal=True,
        help="Accept retains positive reinforcement; Reject forces the agent to explore alternatives.",
    )

    critique = st.text_area(
        "Critique or editorial guidance (optional)",
        placeholder="e.g. Good strategic direction, but emphasize latency numbers and system architecture instead of culture.",
    )

    if st.button("Submit feedback to memory", type="primary"):
        summary = f"a {format_name} post under '{pillar_name}'"
        try:
            with st.spinner("Retaining decision into Hindsight long-term memory..."):
                agent.record_feedback(
                    brand_id=brand_id,
                    recommendation_id=comp["recommendation_id"],
                    decision=decision,
                    context_summary=summary,
                    critique=critique or None,
                )
            st.success(
                f"Feedback recorded ({decision}). Return to the Strategy page and regenerate "
                f"to see the agent adapt to this feedback."
            )
        except HindsightUnavailableError as exc:
            st.error(f"Feedback was not persisted: {exc}")


if __name__ == "__main__":
    render_learning()
