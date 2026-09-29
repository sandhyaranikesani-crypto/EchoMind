"""
EchoMind Agent Orchestrator.

Coordinates the full decision cycle:
  1. Deterministic factual strategy analysis (SQL).
  2. Hindsight recall of strategic context (facts, experiences, beliefs).
  3. Recommendation synthesis with causal justification (LLM optional).
  4. Retention of user feedback back into episodic memory.

Memory is treated as a first-class cognitive layer but is never a hard
dependency of the deterministic path: if the memory backend is offline the
agent degrades transparently (surfacing `memory_error`) instead of failing.
It never silently falls back to a different backend.
"""

import uuid
from typing import Any, Dict, List, Optional

from agent.llm import compose_draft, compose_recommendation
from config.settings import get_memory_adapter, settings
from database.repository import ContentRepository
from memory.base import (
    EpistemicType,
    HindsightUnavailableError,
    InferredMemory,
    MemoryAdapter,
    StrategicContext,
)
from strategy.engine import StrategyAnalysisResult, StrategyEngine
from datetime import datetime


class EchoMindAgent:
    """Main orchestrator for EchoMind."""

    def __init__(
        self,
        repository: Optional[ContentRepository] = None,
        memory: Optional[MemoryAdapter] = None,
        strategy_phase: Optional[str] = None,
    ):
        self.repository = repository or ContentRepository()
        self.strategy_engine = StrategyEngine(self.repository)
        self.strategy_phase = strategy_phase or settings.DEFAULT_STRATEGY_PHASE

        # Memory is optional at runtime. A construction failure (e.g. Hindsight
        # server unreachable, SDK missing) is recorded, not raised, so the
        # deterministic pipeline keeps working.
        self.memory: Optional[MemoryAdapter] = None
        self.memory_error: Optional[str] = None
        if memory is not None:
            self.memory = memory
        else:
            try:
                self.memory = get_memory_adapter()
            except HindsightUnavailableError as exc:
                self.memory_error = str(exc)
            except Exception as exc:  # missing SDK, bad config, etc.
                self.memory_error = f"Memory backend unavailable: {exc}"

    @property
    def memory_online(self) -> bool:
        return self.memory is not None

    # -------------------------------------------------------------------------
    # Analysis
    # -------------------------------------------------------------------------
    def analyze_strategy(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze the brand's current content strategy (deterministic SQL)."""
        brand = self.repository.get_brand(brand_id)
        if not brand:
            raise ValueError(f"Brand not found: {brand_id}")

        analysis = self.strategy_engine.analyze(
            brand_id=brand_id,
            platform_id=platform_id,
        )
        return {"brand": brand, "analysis": analysis}

    # -------------------------------------------------------------------------
    # Memory recall
    # -------------------------------------------------------------------------
    def _recall_context(
        self,
        brand_id: str,
        analysis: StrategyAnalysisResult,
    ) -> Optional[StrategicContext]:
        """Recall scoped strategic context relevant to the pending recommendation."""
        if not self.memory:
            return None

        query_terms: List[str] = []
        if analysis.recommended_pillar:
            query_terms.append(str(analysis.recommended_pillar.get("pillar_name", "")))
        if analysis.recommended_format:
            query_terms.append(str(analysis.recommended_format.get("format_name", "")))
        query = " ".join(t for t in query_terms if t).strip() or "content strategy"

        try:
            return self.memory.recall_strategic_context(
                brand_id=brand_id,
                query=query,
                strategy_phase=self.strategy_phase,
            )
        except HindsightUnavailableError as exc:
            # Transparent degradation: record and continue deterministically.
            self.memory_error = str(exc)
            self.memory = None
            return None

    # -------------------------------------------------------------------------
    # Recommendation
    # -------------------------------------------------------------------------
    def generate_recommendation(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
        use_memory: bool = True,
    ) -> Dict[str, Any]:
        """Full recommendation: deterministic analysis + memory recall + narrative.

        Set ``use_memory=False`` to produce the memory-blind baseline used for
        the "with vs without memory" comparison.
        """
        result = self.analyze_strategy(brand_id, platform_id)
        brand = result["brand"]
        analysis: StrategyAnalysisResult = result["analysis"]

        context = self._recall_context(brand_id, analysis) if use_memory else None
        narrative = compose_recommendation(brand, analysis, context)
        memory_plan = self._memory_plan(analysis, context)
        recommendation_id = uuid.uuid4().hex[:12]
        conviction = self._conviction(analysis, context)
        provenance = self._build_provenance(analysis, context, memory_plan)

        return {
            "recommendation_id": recommendation_id,
            "brand_id": brand_id,
            "brand_name": brand["name"],
            "platform_id": platform_id,
            "strategy_phase": self.strategy_phase,
            "used_memory": bool(use_memory and context is not None),
            "recommended_pillar": analysis.recommended_pillar,
            "recommended_format": analysis.recommended_format,
            "memory_plan": memory_plan,
            "reasoning": analysis.summary_bullets,
            "narrative": narrative,
            "analysis": analysis,
            "memory_online": self.memory_online,
            "memory_error": self.memory_error,
            "conviction": conviction,
            "decision_provenance": provenance,
            "uncertainty": conviction.get("uncertainty_notes", []),
            "brand_constraints": list(getattr(context, "brand_constraints", []) or []),
            "audience_insights": list(getattr(context, "audience_insights", []) or []),
            "relevant_experiences": list(getattr(context, "relevant_experiences", []) or []),
            "active_beliefs": list(getattr(context, "active_beliefs", []) or []),
        }

    def generate_comparison(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Produce the memory OFF vs memory ON recommendation side-by-side.

        This is the core "make memory the star" demo view: the same
        deterministic analysis, narrated once WITHOUT memory (generic) and once
        WITH recalled Hindsight context (personalized to brand voice, past
        feedback, and evolving beliefs).
        """
        result = self.analyze_strategy(brand_id, platform_id)
        brand = result["brand"]
        analysis: StrategyAnalysisResult = result["analysis"]

        without_memory = compose_recommendation(brand, analysis, None)

        context = self._recall_context(brand_id, analysis)
        with_memory = compose_recommendation(brand, analysis, context)
        memory_plan = self._memory_plan(analysis, context)
        conviction = self._conviction(analysis, context)
        provenance = self._build_provenance(analysis, context, memory_plan)

        return {
            "recommendation_id": uuid.uuid4().hex[:12],
            "brand_id": brand_id,
            "brand_name": brand["name"],
            "platform_id": platform_id,
            "strategy_phase": self.strategy_phase,
            "recommended_pillar": analysis.recommended_pillar,
            "recommended_format": analysis.recommended_format,
            "memory_plan": memory_plan,
            "reasoning": analysis.summary_bullets,
            "analysis": analysis,
            "memory_online": self.memory_online,
            "memory_error": self.memory_error,
            "without_memory": without_memory,
            "with_memory": with_memory,
            "conviction": conviction,
            "decision_provenance": provenance,
            "uncertainty": conviction.get("uncertainty_notes", []),
            "brand_constraints": list(getattr(context, "brand_constraints", []) or []),
            "relevant_experiences": list(getattr(context, "relevant_experiences", []) or []),
            "active_beliefs": list(getattr(context, "active_beliefs", []) or []),
        }

    @classmethod
    def _build_provenance(
        cls,
        analysis: StrategyAnalysisResult,
        context: Optional[Any],
        memory_plan: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Construct full decision provenance for recalled inputs."""
        provenance: List[Dict[str, Any]] = []

        pillar = analysis.recommended_pillar or {}
        if pillar:
            delta = pillar.get("share_delta_pct", 0)
            provenance.append({
                "source": "Deterministic SQL Database",
                "category": "Factual Content Gap",
                "type": "sql",
                "evidence": f"Pillar '{pillar.get('pillar_name')}' is {abs(delta):.1f}% below target allocation.",
                "age": "Real-time SQL aggregation",
                "weight": "Foundational",
                "impact": f"Selected target editorial pillar: '{pillar.get('pillar_name')}'.",
            })

        fmt = analysis.recommended_format or {}
        if fmt:
            provenance.append({
                "source": "Deterministic SQL Database",
                "category": "Factual Benchmark",
                "type": "sql",
                "evidence": f"Format '{fmt.get('format_name')}' has {fmt.get('avg_engagement_rate')}% avg historical engagement.",
                "age": "Historical metrics",
                "weight": "Baseline benchmark",
                "impact": "Initial format benchmark prior to memory evaluation.",
            })

        if context is None:
            return provenance

        constraints = getattr(context, "brand_constraints", []) or []
        for c in constraints:
            provenance.append({
                "source": "Hindsight Memory Bank",
                "category": "Brand Voice & Guardrail",
                "type": "world",
                "evidence": str(c),
                "age": "Static guideline",
                "weight": "High (Hard constraint)",
                "impact": "Constrains narrative tone, ICP persona, and taboo boundaries.",
            })

        beliefs = getattr(context, "active_beliefs", []) or []
        for b in beliefs:
            conf = getattr(b, "confidence_score", 0.75)
            la = getattr(b, "learned_at", None)
            age_str = la.strftime("%Y-%m-%d") if la else "Consolidated observation"
            provenance.append({
                "source": "Hindsight Memory Bank",
                "category": "Learned Strategic Belief",
                "type": "observation",
                "evidence": getattr(b, "what_was_learned", str(b)),
                "age": age_str,
                "weight": f"Confidence {conf:.2f}",
                "impact": "Informs recommended editorial angle and positioning.",
            })

        experiences = getattr(context, "relevant_experiences", []) or []
        for exp in experiences:
            is_rejection = "reject" in exp.lower()
            provenance.append({
                "source": "Hindsight Memory Bank",
                "category": "Prior Human Review",
                "type": "experience",
                "evidence": str(exp),
                "age": "Episodic memory",
                "weight": "Decisive (Override)" if is_rejection else "Moderate",
                "impact": (
                    "Triggered format switch away from rejected format."
                    if (is_rejection and memory_plan.get("adjusted"))
                    else "Reinforces positive historical review patterns."
                ),
            })

        return provenance

    @staticmethod
    def _conviction(analysis: StrategyAnalysisResult, context) -> Dict[str, Any]:
        """Heuristic 0-100 confidence, honestly reflecting evidence depth."""
        score = 40
        pillar = analysis.recommended_pillar or {}
        if pillar.get("gap_severity") == "HIGH":
            score += 20
        elif pillar.get("gap_severity") == "MEDIUM":
            score += 10
        if analysis.recommended_format:
            score += 10
        if analysis.top_posts:
            score += 5

        n_facts = len(getattr(context, "brand_constraints", []) or [])
        n_beliefs = len(getattr(context, "active_beliefs", []) or [])
        n_exp = len(getattr(context, "relevant_experiences", []) or [])
        memory_boost = min(25, n_facts * 3 + n_beliefs * 5 + n_exp * 4)
        score = min(100, score + memory_boost)

        uncertainty_notes: List[str] = []
        if analysis.total_posts < 5:
            uncertainty_notes.append("Small historical post volume (<5 published posts). Engagement metrics may carry high variance.")
        if not n_exp:
            uncertainty_notes.append("No prior human reviews recorded for this pillar/format combination. Recommendation is exploratory.")
        if not n_beliefs:
            uncertainty_notes.append("No active strategic beliefs consolidated for this phase yet.")
        if abs(pillar.get("share_delta_pct", 0)) < 5.0:
            uncertainty_notes.append("Target pillar deficit is within standard variance range (+/-5%).")

        if score >= 80:
            label = "High conviction (evidence-grounded)"
        elif score >= 60:
            label = "Moderate conviction"
        else:
            label = "Exploratory (insufficient evidence)"

        return {
            "score": score,
            "label": label,
            "memory_boost": memory_boost,
            "evidence": {"facts": n_facts, "beliefs": n_beliefs, "experiences": n_exp},
            "uncertainty_notes": uncertainty_notes,
        }

    # -------------------------------------------------------------------------
    # Memory-informed planning
    #
    # The deterministic engine decides WHICH pillar is under-served (objective
    # math). Memory decides HOW to win it: the editorial angle and — when past
    # feedback rejected the default format — a switched format. This is what
    # makes the recommendation itself (not just its wording) change with memory.
    # -------------------------------------------------------------------------
    _FORMAT_KEYWORDS = {
        "carousel": ["carousel", "pdf", "document", "slide"],
        "thread": ["thread", "tweetstorm"],
        "text": ["text", "long-form", "long form", "breakdown", "essay", "article", "narrative"],
        "short": ["short", "one-liner", "single tweet", "insight", "punchy"],
    }

    @classmethod
    def _format_group(cls, format_name: str) -> Optional[str]:
        low = (format_name or "").lower()
        for group, kws in cls._FORMAT_KEYWORDS.items():
            if any(k in low for k in kws):
                return group
        return None

    @classmethod
    def _mentions_format(cls, text: str, format_name: str) -> bool:
        low = (text or "").lower()
        if format_name and format_name.lower() in low:
            return True
        group = cls._format_group(format_name)
        if group and any(k in low for k in cls._FORMAT_KEYWORDS[group]):
            return True
        return False

    @classmethod
    def _memory_plan(cls, analysis: StrategyAnalysisResult, context) -> Dict[str, Any]:
        baseline = analysis.recommended_format or {}
        plan = {
            "baseline_format": baseline,
            "format": baseline,
            "angle": None,
            "adjustments": [],
            "adjusted": False,
        }
        if context is None:
            return plan

        beliefs = [getattr(b, "what_was_learned", "") for b in (getattr(context, "active_beliefs", []) or [])]
        experiences = list(getattr(context, "relevant_experiences", []) or [])
        blob = " ".join(beliefs + experiences).lower()

        # 1) Editorial angle derived from beliefs / feedback (memory-only signal).
        if any(k in blob for k in ["teardown", "post-mortem", "postmortem", "incident", "outage", "metric"]):
            plan["angle"] = "Lead with a concrete incident or post-mortem, with a real timeline and hard metrics, not opinion."
        elif any(k in blob for k in ["technical", "architecture", "deep-dive", "deep dive", "benchmark"]):
            plan["angle"] = "Go deep and technical, showing the system detail senior engineers respect."
        elif beliefs:
            plan["angle"] = "Apply the learned belief: " + beliefs[0]
        elif experiences:
            plan["angle"] = "Honor prior feedback: " + experiences[0]

        # 2) Format switch when past feedback rejected the default format.
        #    Real Hindsight may file a rejection under experience OR consolidate
        #    it into an observation/world fact, so scan both.
        formats = analysis.format_performance or []
        rejected = [t for t in (experiences + beliefs) if "reject" in t.lower()]
        if rejected and len(formats) > 1 and baseline:
            base_name = baseline.get("format_name", "")
            if any(cls._mentions_format(e, base_name) for e in rejected):
                alt = formats[1]
                plan["format"] = alt
                plan["adjusted"] = True
                plan["adjustments"].append(
                    f"Past feedback rejected '{base_name}', so I switched to the next best "
                    f"performer, '{alt.get('format_name')}' ({alt.get('avg_engagement_rate')}% avg engagement)."
                )

        if plan["angle"]:
            plan["adjustments"].append("Editorial angle set from learned beliefs / feedback.")
        return plan

    def generate_draft(
        self,
        brand_id: str,
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Turn an accepted recommendation into ready-to-publish post copy.

        Recalls brand voice/guardrails so the draft sounds on-brand.
        """
        brand = self.repository.get_brand(brand_id) or {"name": brand_id}
        analysis = recommendation.get("analysis")
        context = None
        if self.memory and analysis is not None:
            context = self._recall_context(brand_id, analysis)
        return compose_draft(brand, recommendation, context)

    def ask(self, brand_id: str, question: str) -> str:
        """Answer a free-form strategy question via Hindsight reflection."""
        return self.reflect(brand_id, query=question)

    def memory_ledger(self, brand_id: str, limit: int = 50):
        """Return the flat list of stored memories for the brand's bank."""
        if not self.memory:
            raise HindsightUnavailableError(
                self.memory_error or "Memory backend is offline; cannot list memories."
            )
        return self.memory.list_memories(brand_id, limit=limit)

    def generate_baseline_recommendation(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Deterministic-only baseline (kept for backward compatibility)."""
        result = self.analyze_strategy(brand_id, platform_id)
        analysis = result["analysis"]
        return {
            "brand_name": result["brand"]["name"],
            "recommended_pillar": analysis.recommended_pillar,
            "recommended_format": analysis.recommended_format,
            "reasoning": analysis.summary_bullets,
        }

    # -------------------------------------------------------------------------
    # Feedback retention (Retain)
    # -------------------------------------------------------------------------
    def record_feedback(
        self,
        brand_id: str,
        recommendation_id: str,
        decision: str,
        context_summary: str,
        critique: Optional[str] = None,
        sql_post_id: Optional[str] = None,
    ) -> bool:
        """Retain a user decision (ACCEPT / EDIT / REJECT) into episodic memory.

        Raises HindsightUnavailableError if memory is offline, so the caller
        can surface that the feedback was NOT persisted (no silent loss).
        """
        if not self.memory:
            raise HindsightUnavailableError(
                self.memory_error
                or "Memory backend is offline; feedback was not retained."
            )
        return self.memory.retain_interaction_experience(
            brand_id=brand_id,
            recommendation_id=recommendation_id,
            user_decision=decision,
            critique=critique,
            context_summary=context_summary,
            sql_post_id=sql_post_id,
            strategy_phase=self.strategy_phase,
        )

    def reflect(self, brand_id: str, query: str = "recent strategy shifts") -> str:
        """Trigger a Hindsight reflection pass to synthesize higher-level patterns."""
        if not self.memory:
            raise HindsightUnavailableError(
                self.memory_error or "Memory backend is offline; cannot reflect."
            )
        return self.memory.reflect_on_strategy(
            brand_id=brand_id,
            query=query,
            budget=settings.HINDSIGHT_REFLECT_BUDGET,
        )

    # -------------------------------------------------------------------------
    # Demo helper
    # -------------------------------------------------------------------------
    def bootstrap_demo_memory(self, brand_id: str) -> int:
        """Seed a few illustrative brand facts and beliefs for demos.

        Returns the number of memory items written. Requires an online backend.
        """
        if not self.memory:
            raise HindsightUnavailableError(
                self.memory_error or "Memory backend is offline; cannot seed memory."
            )

        self.memory.ensure_bank(brand_id)

        facts = [
            ("voice", "Brand voice is technical, evidence-driven, and never hype-y."),
            ("icp", "Primary audience is senior engineers, SREs, and eng leaders at scale-ups."),
            ("taboo", "Never disparage competitors; never post beginner 101 tutorials."),
        ]
        for category, fact in facts:
            self.memory.retain_brand_fact(
                brand_id=brand_id, fact=fact, category=category
            )

        beliefs = [
            InferredMemory(
                what_was_learned=(
                    "Technical post-mortems and architecture teardowns drive far higher "
                    "engagement than opinion pieces."
                ),
                why_it_was_learned=(
                    "Carousel post-mortems consistently top engagement in historical metrics."
                ),
                supporting_evidence_context=["sql_post_id:post_001", "sql_post_id:post_002"],
                learned_at=datetime.now(),
                confidence_score=0.88,
                strategy_phase=self.strategy_phase,
                epistemic_type=EpistemicType.INFERRED,
            ),
            InferredMemory(
                what_was_learned=(
                    "The 'Engineering Culture & Leadership' pillar is under-served relative "
                    "to its target and should be replenished."
                ),
                why_it_was_learned="Only one post in ~26 days versus a 20% target allocation.",
                supporting_evidence_context=["sql_post_id:post_015"],
                learned_at=datetime.now(),
                confidence_score=0.79,
                strategy_phase=self.strategy_phase,
                epistemic_type=EpistemicType.INFERRED,
            ),
        ]
        for idx, belief in enumerate(beliefs, start=1):
            self.memory.retain_inferred_belief(
                brand_id=brand_id, belief_id=f"demo_{idx}", belief=belief
            )

        return len(facts) + len(beliefs)
