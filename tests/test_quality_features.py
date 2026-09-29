import csv
import io
from datetime import datetime
from types import SimpleNamespace

from agent.guardrails import evaluate_guardrails
from agent.orchestrator import EchoMindAgent
from memory.base import InferredMemory, StrategicContext
from memory.hindsight_adapter import HindsightMemoryAdapter
from strategy.calendar import (
    export_calendar_csv,
    export_calendar_markdown,
    generate_weekly_plan,
)
from strategy.engine import StrategyAnalysisResult


def _analysis() -> StrategyAnalysisResult:
    pillar = {
        "pillar_name": "Engineering Culture",
        "share_delta_pct": -12.0,
        "actual_share_pct": 8.0,
        "target_share_pct": 20.0,
        "days_since_last_post": 24,
        "gap_severity": "HIGH",
    }
    formats = [
        {"format_name": "Carousel", "platform_name": "LinkedIn", "avg_engagement_rate": 4.2},
        {"format_name": "Technical Thread", "platform_name": "X", "avg_engagement_rate": 3.7},
    ]
    return StrategyAnalysisResult(
        brand_id="brand_test",
        platform_id=None,
        total_posts=12,
        pillar_distribution=[pillar],
        format_performance=formats,
        top_posts=[],
        content_gaps=[pillar],
        saturated_pillars=[],
        recommended_pillar=pillar,
        recommended_format=formats[0],
    )


def test_guardrails_return_reasoned_failures_and_passes():
    constraints = [
        "Voice: evidence-driven, avoid hype",
        "Audience: write for senior engineers, not beginners",
        "Taboo: never disparage competitors",
    ]

    compliant = evaluate_guardrails(
        "Measure p99 latency across the distributed system before changing the cache.",
        constraints,
    )
    assert [check["status"] for check in compliant] == ["PASS", "PASS", "PASS"]
    assert all(check["reason"] for check in compliant)

    violations = evaluate_guardrails(
        "A revolutionary 101 tutorial for beginners: our competitors suck.",
        constraints,
    )
    assert [check["status"] for check in violations] == ["FAIL", "FAIL", "FAIL"]
    assert all(check["reason"] for check in violations)


def test_weekly_plan_and_exports_are_balanced_and_complete():
    plan = generate_weekly_plan(
        _analysis(),
        "Test brand",
        memory_plan={
            "format": {"format_name": "Carousel", "platform_name": "LinkedIn"},
            "angle": "Lead with a benchmark.",
        },
        start_date=datetime(2026, 9, 29),
    )

    assert len(plan) == 5
    assert plan[0]["Date"] == "2026-10-05"
    assert plan[0]["Pillar"] == "Engineering Culture"
    assert plan[0]["Format"] == "Carousel"

    csv_rows = list(csv.DictReader(io.StringIO(export_calendar_csv(plan))))
    assert len(csv_rows) == 5
    assert csv_rows[0]["Working Title / Angle"]
    markdown = export_calendar_markdown(plan, "Test brand")
    assert "Weekly Editorial Calendar" in markdown
    assert "Strategic Alignment Notes" in markdown


def test_confidence_and_provenance_reflect_recalled_evidence():
    belief = InferredMemory(
        what_was_learned="Technical post-mortems perform well.",
        why_it_was_learned="Recent technical posts exceeded the engagement baseline.",
        supporting_evidence_context=["sql_post_id:post_001"],
        learned_at=datetime(2026, 9, 28, 12, 0),
        confidence_score=0.84,
        strategy_phase="default",
    )
    context = StrategicContext(
        brand_constraints=["Technical and evidence-driven voice."],
        relevant_experiences=["Decision: REJECT. Proposed Carousel; prefer a thread."],
        active_beliefs=[belief],
    )
    analysis = _analysis()

    conviction = EchoMindAgent._conviction(analysis, context)
    provenance = EchoMindAgent._build_provenance(
        analysis,
        context,
        {"adjusted": True},
    )

    assert conviction["score"] == 82
    assert conviction["label"] == "High conviction (evidence-grounded)"
    assert conviction["memory_boost"] == 12
    assert conviction["evidence"] == {"facts": 1, "beliefs": 1, "experiences": 1}
    assert [item["type"] for item in provenance] == [
        "sql", "sql", "world", "observation", "experience"
    ]
    rejection = provenance[-1]
    assert rejection["weight"] == "Decisive (Override)"
    assert "format switch" in rejection["impact"].lower()


def test_specific_rejection_changes_angle_even_with_seeded_beliefs():
    seeded_belief = InferredMemory(
        what_was_learned="Technical post-mortems drive engagement.",
        why_it_was_learned="Historical posts outperformed the average.",
        supporting_evidence_context=[],
        learned_at=datetime(2026, 9, 28),
        confidence_score=0.88,
    )
    before_context = StrategicContext(active_beliefs=[seeded_belief])
    after_context = StrategicContext(
        active_beliefs=[seeded_belief],
        relevant_experiences=[
            "Decision: REJECT. Proposed Document / PDF Carousel. User critique: prefer code and incident timelines over broad essays."
        ],
    )

    before = EchoMindAgent._memory_plan(_analysis(), before_context)
    after = EchoMindAgent._memory_plan(_analysis(), after_context)

    assert before["angle"] != after["angle"]
    assert "code and an incident timeline" in after["angle"]
    assert after["adjusted"] is True


def test_hindsight_ledger_recovers_explicit_belief_metadata():
    row = SimpleNamespace(
        text=(
            "Strategic belief: Post-mortems perform well. "
            "Rationale: Recent technical posts exceeded baseline. "
            "Evidence: [sql_post_id:post_001, rec_id:rec_002]. Confidence: 0.84."
        ),
        fact_type="observation",
        mentioned_at=datetime(2026, 9, 28, 12, 0),
        metadata={"phase": "conversion"},
    )
    adapter = object.__new__(HindsightMemoryAdapter)
    adapter._client = SimpleNamespace(
        list_memories=lambda **kwargs: SimpleNamespace(items=[row])
    )

    [item] = adapter.list_memories("brand_test")

    assert item["type"] == "observation"
    assert item["why"] == "Recent technical posts exceeded baseline."
    assert item["evidence"] == ["sql_post_id:post_001", "rec_id:rec_002"]
    assert item["confidence"] == 0.84
    assert item["phase"] == "conversion"
    assert item["learned_at"].startswith("2026-09-28")
