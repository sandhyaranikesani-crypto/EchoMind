"""Strategy page: Recommendation generation with decision provenance, guardrail checks, and weekly calendar export."""

import pandas as pd
import streamlit as st

from agent.guardrails import evaluate_guardrails
from strategy.calendar import export_calendar_csv, export_calendar_markdown, generate_weekly_plan
from ui.styles import badge_html, render_header


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
            st.session_state.pop("guardrail_results", None)

    comp = st.session_state.get("comparison")
    if not comp or comp.get("brand_id") != brand_id:
        st.info("Click 'Generate recommendation' to run the strategy engine.")
        return

    if not comp.get("memory_online", True):
        st.warning(
            "Hindsight could not be reached. This recommendation uses deterministic database evidence only; "
            "no recalled memory influenced the result."
        )

    pillar = comp.get("recommended_pillar") or {}
    fmt = comp.get("recommended_format") or {}
    without = comp.get("without_memory") or {}
    withm = comp.get("with_memory") or {}
    conv = comp.get("conviction") or {}
    plan = comp.get("memory_plan") or {}
    mem_fmt = plan.get("format") or fmt
    angle = plan.get("angle")
    adjustments = plan.get("adjustments") or []
    provenance = comp.get("decision_provenance", [])
    uncertainty_notes = comp.get("uncertainty", [])

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
        st.caption(f"Confidence: {label} ({score}/100)")
        st.progress(score)
        if conv.get("memory_boost"):
            st.markdown(
                badge_html(f"+{conv['memory_boost']} conviction points from memory", "info"),
                unsafe_allow_html=True,
            )

    st.subheader("Why this recommendation")
    why_this, why_now, why_format = st.columns(3)
    with why_this:
        st.markdown("**Why this pillar**")
        if pillar:
            st.write(
                f"{pillar.get('pillar_name', 'The selected pillar')} is "
                f"{abs(pillar.get('share_delta_pct', 0)):.1f}% below its target "
                f"({pillar.get('actual_share_pct', 0):.1f}% actual vs "
                f"{pillar.get('target_share_pct', 0):.1f}% target)."
            )
        else:
            st.write("No under-served pillar was identified in the selected data.")
    with why_now:
        st.markdown("**Why now**")
        if pillar:
            days_since = pillar.get("days_since_last_post")
            recency = f" The last post was {days_since} days ago." if days_since is not None else ""
            st.write(f"The allocation gap is {abs(pillar.get('share_delta_pct', 0)):.1f} percentage points.{recency}")
        else:
            st.write("Timing is based on the current publishing history.")
    with why_format:
        st.markdown("**Why this format**")
        format_reason = (
            f"{mem_fmt.get('format_name', 'Selected format')} has "
            f"{mem_fmt.get('avg_engagement_rate', fmt.get('avg_engagement_rate', ''))}% "
            "average historical engagement."
        )
        if plan.get("adjusted"):
            format_reason = "Memory changed the baseline choice. " + " ".join(adjustments)
        elif angle:
            format_reason += " The editorial angle reflects recalled brand memory."
        st.write(format_reason)

    if plan.get("adjusted"):
        st.info(
            f"Memory changed the format from {fmt.get('format_name')} to "
            f"{mem_fmt.get('format_name')} based on prior rejection feedback."
        )

    # Honest Uncertainty Callout
    if uncertainty_notes:
        with st.container(border=True):
            st.markdown(badge_html("Honest uncertainty & assumptions", "warning"), unsafe_allow_html=True)
            for note in uncertainty_notes:
                st.markdown(f"- {note}")

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

    # -------------------------------------------------------------------------
    # Decision Provenance Table
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Decision provenance matrix")
    st.caption("Complete causal trail: every factual metric and recalled memory item that influenced this recommendation.")

    if provenance:
        prov_rows = []
        for p in provenance:
            prov_rows.append(
                {
                    "Source": p.get("source", ""),
                    "Category": p.get("category", ""),
                    "Type": p.get("type", ""),
                    "Recalled Evidence": p.get("evidence", ""),
                    "Recency / Age": p.get("age", ""),
                    "Influence Weight": p.get("weight", ""),
                    "Decision Impact": p.get("impact", ""),
                }
            )
        st.dataframe(pd.DataFrame(prov_rows), use_container_width=True, hide_index=True)
    else:
        st.caption("No provenance records available.")

    # -------------------------------------------------------------------------
    # Deliverable: Generate Post Draft & Guardrail Check
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Publication deliverable & responsible AI guardrails")
    st.caption("Draft copy adhering to recommended format and validated against brand guardrails.")

    if st.button("Generate post draft", type="secondary"):
        with st.spinner("Synthesizing draft copy using recalled brand constraints..."):
            draft = agent.generate_draft(brand_id, comp)
            st.session_state.draft = draft
            constraints = comp.get("brand_constraints", [])
            st.session_state.guardrail_results = evaluate_guardrails(
                draft.get("body", ""),
                constraints,
                brand_name=brand_name,
            )

    draft = st.session_state.get("draft")
    guardrail_results = st.session_state.get("guardrail_results")

    if draft:
        with st.container(border=True):
            source_badge = badge_html(f"Draft generated via {draft.get('source', 'deterministic')}", "info")
            st.markdown(source_badge, unsafe_allow_html=True)
            st.markdown(draft.get("body", ""))

        # Guardrail Compliance Check Matrix
        if guardrail_results:
            st.subheader("Brand guardrail evaluation (Responsible AI)")
            st.caption("Automated audit verifying that draft copy adheres to recalled voice rules, target ICP, and taboos.")

            all_passed = all(r.get("status") == "PASS" for r in guardrail_results)
            overall_badge = (
                badge_html("All brand guardrails passed", "success")
                if all_passed
                else badge_html("Guardrail warnings detected", "warning")
            )
            st.markdown(overall_badge, unsafe_allow_html=True)

            guard_rows = []
            for g in guardrail_results:
                guard_rows.append(
                    {
                        "Rule": g.get("rule"),
                        "Category": g.get("category"),
                        "Status": g.get("status"),
                        "Audit Justification": g.get("reason"),
                    }
                )
            st.dataframe(pd.DataFrame(guard_rows), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # Weekly Plan: Editorial Calendar Export
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Weekly editorial calendar")
    st.caption("Converts detected strategic gaps into an exportable 5-day balanced editorial schedule.")

    analysis = comp.get("analysis")
    if analysis:
        calendar = generate_weekly_plan(
            analysis=analysis,
            brand_name=brand_name,
            memory_plan=plan,
        )

        cal_df = pd.DataFrame(calendar)
        display_cols = ["Day", "Pillar", "Format", "Platform", "Objective", "Working Title / Angle"]
        st.dataframe(cal_df[display_cols], use_container_width=True, hide_index=True)

        col_csv, col_md = st.columns(2)
        with col_csv:
            csv_data = export_calendar_csv(calendar)
            st.download_button(
                label="Download calendar as CSV",
                data=csv_data,
                file_name=f"{brand_id}_editorial_calendar.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col_md:
            md_data = export_calendar_markdown(calendar, brand_name)
            st.download_button(
                label="Download calendar as Markdown",
                data=md_data,
                file_name=f"{brand_id}_editorial_calendar.md",
                mime="text/markdown",
                use_container_width=True,
            )


if __name__ == "__main__":
    render_strategy()
