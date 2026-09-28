"""Deterministic Strategy Engine for EchoMind.

Analyzes factual SQL data to detect:
1. Underrepresented content pillars (mathematical content gaps).
2. Saturated / over-indexed pillars.
3. Top and bottom performing formats per platform.
4. Top-performing historical content benchmarks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.repository import ContentRepository


@dataclass
class StrategyAnalysisResult:
    """Structured output of the deterministic strategy engine."""
    brand_id: str
    platform_id: Optional[str]
    total_posts: int
    pillar_distribution: List[Dict[str, Any]]
    format_performance: List[Dict[str, Any]]
    top_posts: List[Dict[str, Any]]
    content_gaps: List[Dict[str, Any]]
    saturated_pillars: List[Dict[str, Any]]
    recommended_pillar: Optional[Dict[str, Any]]
    recommended_format: Optional[Dict[str, Any]]
    summary_bullets: List[str] = field(default_factory=list)


class StrategyEngine:
    """Calculates deterministic metrics and detects editorial opportunities."""

    def __init__(self, repository: Optional[ContentRepository] = None) -> None:
        self.repo = repository or ContentRepository()

    def analyze(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
    ) -> StrategyAnalysisResult:
        """Run full deterministic diagnostic on brand's published history."""
        # 1. Fetch factual aggregations
        pillars = self.repo.get_pillar_distribution_and_performance(brand_id)
        formats = self.repo.get_format_performance(brand_id, platform_id)
        recent_posts = self.repo.get_recent_posts(brand_id, platform_id, limit=20)

        # Sort posts by engagement rate
        top_posts = sorted(recent_posts, key=lambda x: x["engagement_rate"], reverse=True)[:5]
        total_posts = sum(p["post_count"] for p in pillars)

        # 2. Content Gap Detection
        # A pillar is a gap if:
        # a) actual_share_pct is significantly below target_share_pct (delta <= -5.0)
        # b) or no post in the last 21 days
        now = datetime.now()
        content_gaps = []
        saturated_pillars = []

        for p in pillars:
            days_since_post = None
            if p["last_published_at"]:
                last_dt = datetime.strptime(p["last_published_at"], "%Y-%m-%d %H:%M:%S")
                days_since_post = (now - last_dt).days
                p["days_since_last_post"] = days_since_post
            else:
                p["days_since_last_post"] = 999

            if p["share_delta_pct"] <= -5.0 or (days_since_post is not None and days_since_post >= 21):
                p["gap_severity"] = "HIGH" if p["share_delta_pct"] <= -10.0 else "MEDIUM"
                content_gaps.append(p)
            elif p["share_delta_pct"] >= 5.0:
                saturated_pillars.append(p)

        # 3. Sort gaps by largest deficit
        content_gaps.sort(key=lambda x: x["share_delta_pct"])

        # 4. Determine Recommended Pillar & Winning Format
        recommended_pillar = content_gaps[0] if content_gaps else (pillars[0] if pillars else None)
        recommended_format = formats[0] if formats else None

        # 5. Build human-readable bullet points for prompt and UI
        bullets = []
        if content_gaps:
            top_gap = content_gaps[0]
            bullets.append(
                f"🚨 Major Content Gap: '{top_gap['pillar_name']}' is {abs(top_gap['share_delta_pct'])}% below target allocation "
                f"({top_gap['actual_share_pct']}% actual vs {top_gap['target_share_pct']}% target; last post {top_gap.get('days_since_last_post', 'N/A')} days ago)."
            )
        if saturated_pillars:
            top_sat = saturated_pillars[0]
            bullets.append(
                f"⚠️ Saturated Pillar: '{top_sat['pillar_name']}' is over-indexed at {top_sat['actual_share_pct']}% "
                f"({top_sat['share_delta_pct']:+}% over target allocation of {top_sat['target_share_pct']}%)."
            )
        if recommended_format:
            bullets.append(
                f"📈 Top-Performing Format: '{recommended_format['format_name']}' averages {recommended_format['avg_engagement_rate']}% engagement "
                f"and {recommended_format['avg_clicks']} average clicks."
            )
        if top_posts:
            bullets.append(
                f"🏆 Benchmark Post: '{top_posts[0]['title']}' ({top_posts[0]['format_name']}) achieved {top_posts[0]['engagement_rate']}% engagement."
            )

        return StrategyAnalysisResult(
            brand_id=brand_id,
            platform_id=platform_id,
            total_posts=total_posts,
            pillar_distribution=pillars,
            format_performance=formats,
            top_posts=top_posts,
            content_gaps=content_gaps,
            saturated_pillars=saturated_pillars,
            recommended_pillar=recommended_pillar,
            recommended_format=recommended_format,
            summary_bullets=bullets,
        )
