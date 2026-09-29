"""Overview page: Editorial KPIs, pillar distribution, gaps, and format benchmarks."""

import altair as alt
import pandas as pd
import streamlit as st

from ui.styles import render_header


def render_overview() -> None:
    brand_id = st.session_state.get("active_brand_id")
    brand_name = st.session_state.get("active_brand_name", "Unknown brand")
    platform_id = st.session_state.get("active_platform_id")
    agent = st.session_state.get("agent")

    if not agent or not brand_id:
        st.info("Select a brand from the sidebar to view editorial metrics.")
        return

    render_header(
        "Content strategy overview",
        f"Quantitative analysis and performance benchmarks for {brand_name}.",
    )

    try:
        result = agent.analyze_strategy(brand_id, platform_id)
        analysis = result["analysis"]
    except Exception:
        st.error("Analytics could not be loaded for this selection. Check the local database and try again.")
        return

    # Top KPI row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total published posts", analysis.total_posts)
    with col2:
        gap_count = len(analysis.content_gaps)
        st.metric("Detected gaps", gap_count)
    with col3:
        sat_count = len(analysis.saturated_pillars)
        st.metric("Saturated pillars", sat_count)
    with col4:
        st.metric("Active pillars", len(analysis.pillar_distribution))

    st.markdown("---")

    # Content gaps and saturation callout
    if analysis.content_gaps or analysis.saturated_pillars:
        gap_texts = []
        if analysis.content_gaps:
            top_gap = analysis.content_gaps[0]
            gap_texts.append(
                f"Under-served pillar: <strong>{top_gap['pillar_name']}</strong> is "
                f"{abs(top_gap['share_delta_pct']):.1f}% below target allocation "
                f"({top_gap['actual_share_pct']:.1f}% actual vs {top_gap['target_share_pct']:.1f}% target; "
                f"last post was {top_gap.get('days_since_last_post', 'N/A')} days ago)."
            )
        if analysis.saturated_pillars:
            top_sat = analysis.saturated_pillars[0]
            gap_texts.append(
                f"Saturated pillar: <strong>{top_sat['pillar_name']}</strong> is "
                f"over-indexed at {top_sat['actual_share_pct']:.1f}% "
                f"({top_sat['share_delta_pct']:+.1f}% above target allocation)."
            )
        st.subheader("Editorial balance diagnosis")
        for gap_text in gap_texts:
            st.write(gap_text.replace("<strong>", "").replace("</strong>", ""))

    # Pillar Distribution Table and Grouped Bar Chart
    st.subheader("Content pillar allocation vs targets")
    pillar_rows = []
    for p in analysis.pillar_distribution:
        status_label = "Balanced"
        if p.get("share_delta_pct", 0) <= -5.0:
            status_label = "Under-served"
        elif p.get("share_delta_pct", 0) >= 5.0:
            status_label = "Saturated"

        pillar_rows.append(
            {
                "Pillar": p.get("pillar_name"),
                "Posts": p.get("post_count"),
                "Actual %": round(p.get("actual_share_pct", 0), 1),
                "Target %": round(p.get("target_share_pct", 0), 1),
                "Delta %": round(p.get("share_delta_pct", 0), 1),
                "Days since last": p.get("days_since_last_post", 0),
                "Avg engagement %": round(p.get("avg_engagement_rate", 0), 2),
                "Status": status_label,
            }
        )

    pillar_df = pd.DataFrame(pillar_rows)

    c_left, c_right = st.columns([1.2, 1])
    with c_left:
        st.dataframe(pillar_df, use_container_width=True, hide_index=True)
    with c_right:
        if not pillar_df.empty:
            chart_df = pd.melt(
                pillar_df,
                id_vars=["Pillar"],
                value_vars=["Actual %", "Target %"],
                var_name="Metric",
                value_name="Share %",
            )
            chart = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
                .encode(
                    x=alt.X("Pillar:N", title=None, axis=alt.Axis(labelAngle=-20)),
                    y=alt.Y("Share %:Q", title="Share percentage (%)"),
                    color=alt.Color("Metric:N", legend=alt.Legend(title=None, orient="top")),
                    xOffset="Metric:N",
                    tooltip=["Pillar", "Metric", "Share %"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart, use_container_width=True, theme="streamlit")

    st.markdown("---")

    # Format Performance and Benchmark Posts
    col_fmt, col_bench = st.columns(2)
    with col_fmt:
        st.subheader("Format performance")
        fmt_rows = []
        for f in analysis.format_performance:
            fmt_rows.append(
                {
                    "Format": f.get("format_name"),
                    "Platform": f.get("platform_name"),
                    "Posts": f.get("post_count"),
                    "Avg engagement %": round(f.get("avg_engagement_rate", 0), 2),
                    "Avg clicks": f.get("avg_clicks", 0),
                    "Avg impressions": f.get("avg_impressions", 0),
                }
            )
        fmt_df = pd.DataFrame(fmt_rows)
        if not fmt_df.empty:
            st.dataframe(fmt_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No published posts for selected platform filter.")

    with col_bench:
        st.subheader("Top-performing historical posts")
        bench_rows = []
        for p in analysis.top_posts:
            bench_rows.append(
                {
                    "Title": p.get("title"),
                    "Pillar": p.get("pillar_name"),
                    "Format": p.get("format_name"),
                    "Engagement %": round(p.get("engagement_rate", 0), 2),
                    "Clicks": p.get("clicks", 0),
                }
            )
        bench_df = pd.DataFrame(bench_rows)
        if not bench_df.empty:
            st.dataframe(bench_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No historical benchmark posts recorded.")


if __name__ == "__main__":
    render_overview()
