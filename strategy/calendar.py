"""Weekly editorial calendar generator for EchoMind.

Transforms detected content gaps, saturated pillars, and historical benchmarks
into an actionable 5-day editorial schedule, exportable as Markdown and CSV.
"""

import csv
import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from strategy.engine import StrategyAnalysisResult


def generate_weekly_plan(
    analysis: StrategyAnalysisResult,
    brand_name: str,
    memory_plan: Optional[Dict[str, Any]] = None,
    start_date: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Generate a balanced 5-day editorial calendar targeting detected gaps."""
    base_date = start_date or datetime.now()
    # Next Monday or tomorrow
    days_until_monday = (7 - base_date.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 1
    start_monday = base_date + timedelta(days=days_until_monday)

    pillars = analysis.pillar_distribution or []
    formats = analysis.format_performance or []
    gaps = analysis.content_gaps or []

    # Default winning format
    top_format = (
        (memory_plan.get("format") if memory_plan else None)
        or analysis.recommended_format
        or (formats[0] if formats else {"format_name": "Technical Post", "platform_name": "LinkedIn"})
    )
    top_format_name = top_format.get("format_name", "Technical Breakdown")

    alt_format = formats[1] if len(formats) > 1 else top_format
    alt_format_name = alt_format.get("format_name", "Short Insight")

    # Priority queue of pillars: gaps first, then active pillars
    priority_pillars: List[Dict[str, Any]] = list(gaps)
    for p in pillars:
        if p not in priority_pillars:
            priority_pillars.append(p)

    if not priority_pillars:
        priority_pillars = [
            {"pillar_name": "System Architecture", "share_delta_pct": -10.0},
            {"pillar_name": "Developer Productivity", "share_delta_pct": 0.0},
            {"pillar_name": "Engineering Culture", "share_delta_pct": -5.0},
            {"pillar_name": "Product Updates", "share_delta_pct": 0.0},
        ]

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    calendar_entries: List[Dict[str, Any]] = []

    for i, day_name in enumerate(days):
        slot_date = start_monday + timedelta(days=i)
        date_str = slot_date.strftime("%Y-%m-%d")

        # Pick pillar in round-robin prioritizing gaps
        assigned_pillar = priority_pillars[i % len(priority_pillars)]
        pil_name = assigned_pillar.get("pillar_name", "General Strategy")
        delta = assigned_pillar.get("share_delta_pct", 0)

        # Assign format and rationale
        if i == 0:
            # Primary slot: Top priority gap
            fmt = top_format_name
            plat = top_format.get("platform_name", "LinkedIn")
            angle = (memory_plan.get("angle") if memory_plan else None) or "Lead with a concrete incident post-mortem and metrics."
            objective = f"Primary gap repair: currently {abs(delta):.1f}% below target allocation."
            working_title = f"Post-Mortem: Overcoming Distributed Bottlenecks in {pil_name}"
        elif i == 1:
            # Secondary slot: High-engagement technical breakdown
            fmt = alt_format_name
            plat = alt_format.get("platform_name", "X (Twitter)")
            angle = "Deep dive with code and architectural diagrams."
            objective = "Maintain weekly cadence on core technical foundation."
            working_title = f"Deep Dive: 4 Architecture Patterns for {pil_name}"
        elif i == 2:
            # Midweek slot: Next under-represented pillar
            fmt = top_format_name
            plat = "LinkedIn"
            angle = "Practical benchmarks and tooling comparisons."
            objective = "Topical breadth rebalancing against saturated topics."
            working_title = f"How We Scaled Our Internal Tooling for {pil_name}"
        elif i == 3:
            # Thursday slot: Team workflow or operational learning
            fmt = alt_format_name
            plat = "X (Twitter)"
            angle = "Concise engineering takeaways for staff engineers."
            objective = "Continuous audience engagement."
            working_title = f"Thread: 5 Hard Lessons Learned in Production {pil_name}"
        else:
            # Friday slot: Weekly retrospective or culture summary
            fmt = top_format_name
            plat = "LinkedIn"
            angle = "Thought leadership and team reflections."
            objective = "Close weekly cycle with forward-looking engineering leadership."
            working_title = f"Weekly Retrospective: What Scaled and What Broke in {pil_name}"

        calendar_entries.append(
            {
                "Day": f"{day_name} ({date_str})",
                "Date": date_str,
                "Pillar": pil_name,
                "Format": fmt,
                "Platform": plat,
                "Objective": objective,
                "Working Title / Angle": working_title,
                "Editorial Angle": angle,
            }
        )

    return calendar_entries


def export_calendar_csv(calendar: List[Dict[str, Any]]) -> str:
    """Export calendar entries to standard CSV format."""
    if not calendar:
        return ""
    fieldnames = ["Day", "Date", "Pillar", "Format", "Platform", "Objective", "Working Title / Angle"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in calendar:
        writer.writerow(row)
    return output.getvalue()


def export_calendar_markdown(calendar: List[Dict[str, Any]], brand_name: str) -> str:
    """Export calendar entries to a clean Markdown report."""
    if not calendar:
        return f"# Editorial Calendar — {brand_name}\n\nNo scheduled posts."

    lines = [
        f"# Weekly Editorial Calendar — {brand_name}",
        "",
        f"*Generated on {datetime.now().strftime('%Y-%m-%d')} based on deterministic gap analysis and Hindsight memory.*",
        "",
        "| Day & Date | Pillar | Format | Platform | Objective | Working Title / Angle |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for item in calendar:
        day = item.get("Day", "")
        pil = item.get("Pillar", "")
        fmt = item.get("Format", "")
        plat = item.get("Platform", "")
        obj = item.get("Objective", "").replace("|", "/")
        title = item.get("Working Title / Angle", "").replace("|", "/")
        lines.append(f"| {day} | {pil} | {fmt} | {plat} | {obj} | {title} |")

    lines.append("")
    lines.append("## Strategic Alignment Notes")
    lines.append("- Highest-priority strategic gap receives primary slot on Monday.")
    lines.append("- Content formats align with top historical engagement rates.")
    lines.append("- Brand voice constraints and guardrails apply to all scheduled drafts.")
    return "\n".join(lines)
