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
        "Rejection critique",
        value="Our audience prefers deep technical post-mortems with code and incident timelines over high-level culture essays. Lead with concrete incidents and metrics.",
    )

    if st.button("Run learning cycle", type="primary"):
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

                st.session_state.sim = {"before": before, "after": after, "critique": sim_critique}
            except HindsightUnavailableError as exc:
                st.error("The learning cycle could not reach memory; no feedback was recorded.")
            except Exception as exc:
                st.error("The learning cycle could not be completed. Review the System page for backend status.")

    sim = st.session_state.get("sim")
    if sim:
        before, after = sim["before"], sim["after"]
        bp = before.get("memory_plan") or {}
        ap = after.get("memory_plan") or {}

        before_fmt = (bp.get("format") or before.get("recommended_format") or {}).get("format_name", "—")
        after_fmt = (ap.get("format") or after.get("recommended_format") or {}).get("format_name", "—")
        before_angle = bp.get("angle", "Default generic angle")
        after_angle = ap.get("angle", "Default generic angle")
        before_confidence = before.get("conviction") or {}
        after_confidence = after.get("conviction") or {}

        # Before / After side-by-side cards
        c_before, c_after = st.columns(2)
        with c_before:
            with st.container(border=True):
                st.markdown(badge_html("Before feedback", "neutral"), unsafe_allow_html=True)
                st.caption(f"Experiences recalled: {len(before.get('relevant_experiences', []))}")
                st.markdown(f"**Format:** {before_fmt}")
                st.markdown(f"**Editorial angle:** {before_angle}")
                st.markdown(
                    f"**Confidence:** {before_confidence.get('label', 'Exploratory')} "
                    f"({before_confidence.get('score', 0)}/100)"
                )
                st.markdown("---")
                st.markdown((before.get("narrative") or {}).get("body", "")[:450] + "...")

        with c_after:
            with st.container(border=True):
                st.markdown(badge_html("After learning from critique", "success"), unsafe_allow_html=True)
                st.caption(f"Experiences recalled: {len(after.get('relevant_experiences', []))}")
                st.markdown(f"**Format:** {after_fmt}")
                st.markdown(f"**Editorial angle:** {after_angle}")
                st.markdown(
                    f"**Confidence:** {after_confidence.get('label', 'Exploratory')} "
                    f"({after_confidence.get('score', 0)}/100)"
                )
                st.markdown("---")
                st.markdown((after.get("narrative") or {}).get("body", "")[:450] + "...")

        # Explicit Diff Highlight
        st.markdown("---")
        st.subheader("What changed between recommendations")
        confidence_delta = after_confidence.get("score", 0) - before_confidence.get("score", 0)

        diff_col1, diff_col2, diff_col3 = st.columns(3)
        with diff_col1:
            st.markdown("**Format**")
            st.write(f"{before_fmt} → {after_fmt}")
            st.caption("Changed after recalled feedback rejected the original format." if before_fmt != after_fmt else "Format maintained.")

        with diff_col2:
            st.markdown("**Editorial angle**")
            st.write(f"{before_angle or 'Not set'} → {after_angle or 'Not set'}")
            st.caption("Updated from the learned critique." if before_angle != after_angle else "Angle maintained.")

        with diff_col3:
            st.markdown("**Confidence**")
            st.write(
                f"{before_confidence.get('score', 0)}/100 → "
                f"{after_confidence.get('score', 0)}/100 ({confidence_delta:+d})"
            )
            st.caption("Confidence includes the newly recalled experience.")

        if after.get("relevant_experiences"):
            st.markdown("**Recalled memory behind the change**")
            for exp in after["relevant_experiences"]:
                st.markdown(f"- {exp}")
        else:
            st.info("The second recommendation did not return an episodic memory. The diff is not attributed to feedback.")

        if sim.get("critique"):
            st.caption(f"Critique retained in this cycle: {sim['critique']}")

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

    edited_copy = ""
    if decision == "EDIT":
        edited_copy = st.text_area(
            "Edited recommendation",
            value=(comp.get("with_memory") or {}).get("body", ""),
            key="learning_edited_copy",
        )

    critique = st.text_area(
        "Critique or editorial guidance (optional)",
        placeholder="e.g. Good strategic direction, but emphasize latency numbers and system architecture instead of culture.",
    )

    if st.button("Submit feedback to memory", type="primary"):
        summary = f"a {format_name} post under '{pillar_name}'"
        try:
            with st.spinner("Retaining decision into Hindsight long-term memory..."):
                retained_critique = critique or None
                if decision == "EDIT" and edited_copy:
                    retained_critique = (
                        f"{critique.strip()}\nEdited copy: {edited_copy}" if critique.strip()
                        else f"Edited copy: {edited_copy}"
                    )
                agent.record_feedback(
                    brand_id=brand_id,
                    recommendation_id=comp["recommendation_id"],
                    decision=decision,
                    context_summary=summary,
                    critique=retained_critique,
                )
            st.success(
                f"Feedback recorded ({decision}). Return to the Strategy page and regenerate "
                f"to see the agent adapt to this feedback."
            )
        except HindsightUnavailableError as exc:
            st.error("Feedback was not persisted because the memory backend is unavailable. The System page shows its status.")
        except Exception:
            st.error("Feedback could not be submitted. No memory change was confirmed.")


if __name__ == "__main__":
    render_learning()
