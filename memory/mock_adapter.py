"""In-memory Mock implementation of MemoryAdapter.

Activated ONLY when explicitly configured via HINDSIGHT_USE_MOCK=True.
Never used as a silent fallback.
Provides complete tenant isolation and reproducible test behavior.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import get_brand_bank_id
from memory.base import (
    EpistemicType,
    InferredMemory,
    MemoryAdapter,
    StrategicContext,
)


class MockMemoryAdapter(MemoryAdapter):
    """In-memory mock memory adapter for offline development, CI, and evaluation."""

    def __init__(self) -> None:
        # Structure: { bank_id: { "facts": dict, "experiences": dict, "beliefs": dict } }
        self._banks: Dict[str, Dict[str, Any]] = {}

    def _get_bank(self, brand_id: str) -> Dict[str, Any]:
        bank_id = get_brand_bank_id(brand_id)
        if bank_id not in self._banks:
            self._banks[bank_id] = {
                "facts": {},        # doc_id -> str
                "experiences": {},  # doc_id -> dict
                "beliefs": {},      # doc_id -> InferredMemory
            }
        return self._banks[bank_id]

    def retain_brand_fact(
        self,
        brand_id: str,
        fact: str,
        category: str,
        document_id: Optional[str] = None,
    ) -> bool:
        """Store or upsert objective brand, audience, or taboo rules."""
        bank = self._get_bank(brand_id)
        doc_id = document_id or f"brand_fact_{category.strip().lower()}"
        content = f"[BRAND FACT - {category.upper()}] {fact.strip()}"
        bank["facts"][doc_id] = content
        return True

    def retain_interaction_experience(
        self,
        brand_id: str,
        recommendation_id: str,
        user_decision: str,
        critique: Optional[str],
        context_summary: str,
        sql_post_id: Optional[str] = None,
        strategy_phase: str = "default",
    ) -> bool:
        """Store an episodic recommendation outcome and user review."""
        bank = self._get_bank(brand_id)
        doc_id = f"rec_{recommendation_id.strip()}"
        critique_text = f" User Critique: '{critique.strip()}'" if critique else " No critique provided."
        sql_ref = f" Reference SQL Post ID: {sql_post_id.strip()}." if sql_post_id else ""
        content = (
            f"[AGENT EXPERIENCE - REC {recommendation_id}] Decision: {user_decision.upper()}. "
            f"Proposal Summary: {context_summary.strip()}.{critique_text}{sql_ref} "
            f"Strategy Phase: {strategy_phase}."
        )
        bank["experiences"][doc_id] = {
            "content": content,
            "decision": user_decision.lower(),
            "phase": strategy_phase.lower(),
            "timestamp": datetime.now(),
        }
        return True

    def retain_inferred_belief(
        self,
        brand_id: str,
        belief_id: str,
        belief: InferredMemory,
    ) -> bool:
        """Store or update a strategic rule with evidence pointers and confidence score."""
        bank = self._get_bank(brand_id)
        doc_id = f"belief_{belief_id.strip()}"
        bank["beliefs"][doc_id] = belief
        return True

    def recall_strategic_context(
        self,
        brand_id: str,
        query: str,
        strategy_phase: str = "default",
        channel: Optional[str] = None,
        limit_per_category: int = 3,
    ) -> StrategicContext:
        """Selectively recall bounded, relevant memory for recommendation synthesis."""
        bank = self._get_bank(brand_id)

        # 1. Facts
        facts = list(bank["facts"].values())[:limit_per_category]

        # 2. Experiences
        exps = [exp["content"] for exp in bank["experiences"].values()][:limit_per_category]

        # 3. Beliefs filtered by current strategy phase
        target_phase = strategy_phase.strip().lower()
        matched_beliefs = [
            b for b in bank["beliefs"].values()
            if b.strategy_phase.strip().lower() in (target_phase, "default")
        ][:limit_per_category]

        return StrategicContext(
            brand_constraints=facts,
            audience_insights=[],
            relevant_experiences=exps,
            active_beliefs=matched_beliefs,
        )

    def list_memories(self, brand_id: str, limit: int = 50) -> list:
        """Flat ledger of everything stored for this brand (for the UI)."""
        bank = self._get_bank(brand_id)
        items = []
        for content in bank["facts"].values():
            items.append({"text": content, "type": "world", "when": None})
        for exp in bank["experiences"].values():
            ts = exp.get("timestamp")
            items.append({
                "text": exp.get("content", ""),
                "type": "experience",
                "when": ts.strftime("%Y-%m-%d %H:%M") if ts else None,
                "decision": exp.get("decision"),
                "phase": exp.get("phase"),
            })
        for belief in bank["beliefs"].values():
            la = getattr(belief, "learned_at", None)
            items.append({
                "text": getattr(belief, "what_was_learned", str(belief)),
                "type": "belief",
                "when": la.strftime("%Y-%m-%d %H:%M") if la else None,
                "why": getattr(belief, "why_it_was_learned", ""),
                "confidence": getattr(belief, "confidence_score", 0.75),
                "evidence": getattr(belief, "supporting_evidence_context", []),
                "phase": getattr(belief, "strategy_phase", "default"),
            })
        return items[:limit]

    def reflect_on_strategy(
        self,
        brand_id: str,
        query: str,
        budget: str = "low",
    ) -> str:
        """Synthesize high-level patterns across mock memories."""
        bank = self._get_bank(brand_id)
        belief_count = len(bank["beliefs"])
        exp_count = len(bank["experiences"])
        fact_count = len(bank["facts"])
        return (
            f"[MOCK REFLECTION for {brand_id}]\n"
            f"Reflected on '{query}' across {fact_count} facts, {exp_count} experiences, "
            f"and {belief_count} active beliefs. Budget: {budget}."
        )
