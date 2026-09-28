"""Realistic demo seed dataset for EchoMind.

Creates:
- 1 Brand: EchoMind AI
- 2 Platforms: LinkedIn, X (Twitter)
- 4 Content Formats: PDF Carousel, Technical Breakdown, Thread, Short Insight
- 4 Content Pillars:
  1. System Architecture & Resilience (target 35%)
  2. Developer Productivity & Tooling (target 25%)
  3. Engineering Culture & Leadership (target 20%)  <- Clear Content Gap (<7% actual)
  4. Product Updates & Changelog (target 20%)
- 15 Historical Posts with Metrics showing clear format/pillar performance differences.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from datetime import datetime, timedelta
from typing import Optional

from database.db import get_connection, init_db


def seed_database(db_path: Optional[str] = None) -> None:
    """Initialize schema and insert realistic demo dataset."""
    init_db(db_path)
    conn = get_connection(db_path)

    now = datetime.now()

    with conn:
        # 1. Demo Brand
        conn.execute(
            """
            INSERT OR REPLACE INTO brands (id, name, industry, website, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "brand_echomind",
                "EchoMind AI",
                "Developer Productivity & Infrastructure",
                "https://echomind.dev",
                (now - timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

        # 2. Platforms
        platforms = [
            ("linkedin", "LinkedIn", "https://www.linkedin.com"),
            ("x_twitter", "X (Twitter)", "https://x.com"),
        ]
        for p_id, p_name, p_url in platforms:
            conn.execute(
                "INSERT OR REPLACE INTO platforms (id, name, base_url) VALUES (?, ?, ?)",
                (p_id, p_name, p_url),
            )

        # 3. Content Formats
        formats = [
            ("li_carousel", "linkedin", "Document / PDF Carousel", "Multi-slide visual teardown"),
            ("li_text", "linkedin", "Long-form Text Breakdown", "Deep-dive technical narrative"),
            ("tw_thread", "x_twitter", "Technical Thread", "Multi-tweet breakdown with code"),
            ("tw_short", "x_twitter", "Short Technical Insight", "Single tweet with punchy takeaway"),
        ]
        for f_id, plat_id, f_name, f_desc in formats:
            conn.execute(
                "INSERT OR REPLACE INTO content_formats (id, platform_id, name, description) VALUES (?, ?, ?, ?)",
                (f_id, plat_id, f_name, f_desc),
            )

        # 4. Content Pillars
        pillars = [
            ("pillar_sys_arch", "brand_echomind", "System Architecture & Resilience", "Deep-dives into distributed systems, failovers, and latency bottlenecks", 35.0, 1),
            ("pillar_dev_tools", "brand_echomind", "Developer Productivity & Tooling", "Workflows, profiling tools, and developer efficiency benchmarks", 25.0, 1),
            ("pillar_eng_culture", "brand_echomind", "Engineering Culture & Leadership", "Mentorship, hiring top talent, post-mortem culture, and team structure", 20.0, 1),
            ("pillar_changelog", "brand_echomind", "Product Updates & Changelog", "New feature rollouts, benchmark improvements, and platform changelogs", 20.0, 1),
        ]
        for pil_id, b_id, pil_name, pil_desc, t_share, is_act in pillars:
            conn.execute(
                """
                INSERT OR REPLACE INTO content_pillars 
                (id, brand_id, name, description, target_share_pct, is_active) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (pil_id, b_id, pil_name, pil_desc, t_share, is_act),
            )

        # 5. Clear existing posts and metrics for clean re-seeding
        conn.execute("DELETE FROM posts WHERE brand_id = 'brand_echomind'")

        # 6. Realistic 15 historical posts
        posts_data = [
            # System Architecture Posts (High Engagement, especially Carousels)
            (
                "post_001", "pillar_sys_arch", "linkedin", "li_carousel",
                "Post-Mortem: Why Our Redis Cache Exhausted at 150k QPS",
                "Last Tuesday our primary cache connection pool hit saturation. Here is the step-by-step diagnostic breakdown...",
                now - timedelta(days=2), 48200, 39100, 1840, 980, 142, 310, 450, 86, 3.90
            ),
            (
                "post_002", "pillar_sys_arch", "linkedin", "li_carousel",
                "Visual Guide: Mitigating Cascading Failures in Microservices",
                "Circuit breakers without jittered retry backoffs create synchronized stampedes. Here are 4 architecture patterns to prevent it...",
                now - timedelta(days=6), 54100, 42300, 2100, 1120, 189, 410, 520, 102, 4.14
            ),
            (
                "post_003", "pillar_sys_arch", "linkedin", "li_text",
                "Why We Chose Raft over Paxos for Distributed Consensus",
                "Paxos is theoretically complete, but understanding edge cases in production consensus is notoriously difficult...",
                now - timedelta(days=9), 28400, 21000, 780, 410, 68, 85, 120, 24, 2.40
            ),
            (
                "post_004", "pillar_sys_arch", "x_twitter", "tw_thread",
                "Thread: How Zero-Copy Networking Saves 30% Server CPU",
                "1/8 Most distributed network proxies waste CPU cycles copying packet buffers between kernel and user space. Here is how zero-copy works...",
                now - timedelta(days=12), 34000, 27000, 1200, 780, 95, 230, 310, 45, 4.16
            ),
            (
                "post_005", "pillar_sys_arch", "linkedin", "li_carousel",
                "Database Sharding: When You Actually Need It and When It Hurts",
                "Premature sharding is the root of endless distributed transaction agony. Let's look at vertical partitioning vs read replicas first...",
                now - timedelta(days=15), 41500, 33200, 1450, 850, 112, 290, 380, 71, 3.93
            ),
            (
                "post_006", "pillar_sys_arch", "x_twitter", "tw_short",
                "Quick Latency Fact: p99 Matters More than p50",
                "If your median response is 15ms but your p99 is 1,200ms, 1 out of 100 enterprise users is experiencing a broken system.",
                now - timedelta(days=18), 19500, 16000, 340, 310, 24, 45, 60, 8, 2.25
            ),
            (
                "post_007", "pillar_sys_arch", "linkedin", "li_text",
                "Designing Idempotent APIs: Handling Network Retries Safely",
                "Without idempotency keys, duplicate network timeouts result in double billing. Here is our distributed locking schema...",
                now - timedelta(days=21), 22000, 17500, 510, 340, 42, 60, 95, 18, 2.44
            ),

            # Developer Productivity & Tooling Posts (Moderate-High Engagement)
            (
                "post_008", "pillar_dev_tools", "linkedin", "li_carousel",
                "Speeding Up Monorepo CI Builds from 45m to 4m",
                "Distributed remote caching, dependency graph pruning, and parallel test runners reduced our build times by 91%...",
                now - timedelta(days=4), 38900, 31000, 1320, 740, 88, 195, 290, 54, 3.37
            ),
            (
                "post_009", "pillar_dev_tools", "x_twitter", "tw_thread",
                "Thread: 5 eBPF Profiling Commands Every Senior SRE Should Know",
                "1/7 Traditional CPU sampling profilers introduce high overhead. Here is how eBPF kernel tracing lets you diagnose latency safely...",
                now - timedelta(days=11), 29500, 24100, 980, 620, 74, 180, 240, 39, 3.77
            ),
            (
                "post_010", "pillar_dev_tools", "linkedin", "li_text",
                "Why We Stopped Using Complex IDE Plugins and Returned to Clean CLI",
                "Lightweight terminal workflows keep developers in flow state. Here is our minimal dotfiles setup for team onboarding...",
                now - timedelta(days=16), 18400, 14200, 310, 210, 35, 25, 40, 11, 1.68
            ),
            (
                "post_011", "pillar_dev_tools", "x_twitter", "tw_short",
                "Developer Productivity Quote",
                "The most productive code is the code you deleted after simplifying your domain model.",
                now - timedelta(days=23), 14200, 11800, 180, 220, 18, 30, 25, 5, 2.06
            ),

            # Product Updates & Changelog (Lower Viral Reach, Direct Conversions)
            (
                "post_012", "pillar_changelog", "linkedin", "li_carousel",
                "EchoMind v2.4 Release: Automatic Anomaly Detection",
                "We just released real-time distributed latency anomaly tracing. See the new dashboard in action...",
                now - timedelta(days=7), 21500, 16800, 890, 340, 48, 75, 90, 68, 2.57
            ),
            (
                "post_013", "pillar_changelog", "x_twitter", "tw_thread",
                "Changelog: 5x Faster Memory Indexing in v2.4",
                "1/5 How we rewrote our indexing worker pool to cut ingestion latency from 800ms down to 140ms...",
                now - timedelta(days=14), 16200, 12900, 610, 280, 31, 65, 80, 42, 2.81
            ),
            (
                "post_014", "pillar_changelog", "linkedin", "li_text",
                "EchoMind Security Bulletin: SOC-2 Type II Certified",
                "Security is foundational for enterprise developer tools. We are proud to announce our SOC-2 Type II audit completion...",
                now - timedelta(days=22), 12400, 9800, 240, 180, 22, 18, 30, 15, 2.01
            ),

            # Engineering Culture & Leadership (THE GAP: Only 1 post, 26 days ago!)
            (
                "post_015", "pillar_eng_culture", "linkedin", "li_text",
                "Blameless Post-Mortems: How We Turn Incidents into Team Growth",
                "When production breaks, asking 'who caused this' destroys psychological safety. Instead, we ask 'what system permitted this'...",
                now - timedelta(days=26), 31200, 24800, 920, 690, 84, 160, 210, 32, 3.66
            ),
        ]

        for p_id, pil_id, plat_id, f_id, title, copy, pub_date, imp, reach, clicks, likes, comm, shares, saves, conv, eng_rate in posts_data:
            conn.execute(
                """
                INSERT INTO posts 
                (id, brand_id, pillar_id, platform_id, format_id, title, content_text, published_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PUBLISHED')
                """,
                (p_id, "brand_echomind", pil_id, plat_id, f_id, title, copy, pub_date.strftime("%Y-%m-%d %H:%M:%S")),
            )

            conn.execute(
                """
                INSERT INTO performance_metrics 
                (post_id, recorded_at, impressions, reach, clicks, likes, comments, shares, saves, conversions, engagement_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (p_id, (pub_date + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"), imp, reach, clicks, likes, comm, shares, saves, conv, eng_rate),
            )

    conn.close()


if __name__ == "__main__":
    seed_database()
    print("EchoMind demo database seeded successfully.")
