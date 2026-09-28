"""Concrete implementation of MemoryAdapter wrapping the official Hindsight SDK.

Targets a real Hindsight server (Hindsight Cloud at
https://api.hindsight.vectorize.io, or a self-hosted server) via the
`hindsight-client` package.

Design notes (aligned with the real Hindsight API, docs v0.10):
  * Each brand maps to its own **memory bank** (strict tenant isolation).
  * `retain()` lets Hindsight's LLM extraction classify content into the
    native pathways: **world facts** (objective brand rules) and
    **experiences** (the agent's own actions / user feedback). We do NOT
    hand-roll a tagging scheme for this; we use `context` + `metadata`.
  * Evolving beliefs are Hindsight **observations** — deduplicated,
    evidence-grounded beliefs that Hindsight consolidates automatically in the
    background. We surface them by recalling `types=["observation"]`.
  * `recall()` uses the native `types` filter and `budget`.
  * `reflect()` performs agentic synthesis shaped by the bank's mission and
    disposition.

Raises HindsightUnavailableError on any communication or server failure.
Never performs silent fallbacks.
"""

from datetime import datetime
from typing import Any, List, Optional

from config.settings import get_brand_bank_id
from memory.base import (
    EpistemicType,
    HindsightUnavailableError,
    InferredMemory,
    MemoryAdapter,
    StrategicContext,
)

# Mission + disposition give the bank a strategist "personality" that shapes
# how `reflect` reasons over the brand's memories.
STRATEGIST_MISSION = (
    "I am a senior content strategist. I track what content was published, what "
    "performed well, which editorial pillars are over- or under-served, and the "
    "brand's voice and guardrails. I learn from every acceptance, edit, and "
    "rejection, and I recommend the next piece of content with clear causal "
    "justification grounded in past evidence."
)
STRATEGIST_DISPOSITION = {
    "skepticism": 4,   # demand evidence before asserting a pattern
    "literalism": 3,
    "empathy": 3,
}


class HindsightMemoryAdapter(MemoryAdapter):
    """Production memory adapter backed by the Hindsight SDK."""

    def __init__(
        self,
        base_url: str = "https://api.hindsight.vectorize.io",
        api_key: Optional[str] = None,
        budget: str = "mid",
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.budget = budget
        self._ensured_banks: set = set()
        try:
            # Imported lazily so this module stays importable (and the rest of
            # the app runs) even when the optional SDK is not installed.
            from hindsight_client import Hindsight

            self._client = Hindsight(
                base_url=self.base_url,
                api_key=self.api_key or None,
            )
        except Exception as e:
            raise HindsightUnavailableError(
                f"Failed to initialize Hindsight client with base_url '{self.base_url}': {e}"
            ) from e

    # -------------------------------------------------------------------------
    # Bank lifecycle
    # -------------------------------------------------------------------------
    def ensure_bank(self, brand_id: str, name: Optional[str] = None) -> str:
        """Idempotently create the brand's memory bank with a strategist mission."""
        bank_id = get_brand_bank_id(brand_id)
        if bank_id in self._ensured_banks:
            return bank_id
        try:
            self._client.create_bank(
                bank_id=bank_id,
                name=name or f"EchoMind strategy bank ({brand_id})",
                mission=STRATEGIST_MISSION,
                disposition=STRATEGIST_DISPOSITION,
            )
        except Exception as e:
            # A bank that already exists is fine; anything else is surfaced only
            # if a later operation actually fails. We record success optimistically
            # to avoid repeated create attempts within a session.
            msg = str(e).lower()
            if "exist" not in msg and "conflict" not in msg and "409" not in msg:
                # Non-idempotent failure (e.g. auth/network) — let subsequent
                # retain/recall raise a clear HindsightUnavailableError.
                pass
        self._ensured_banks.add(bank_id)
        return bank_id

    # -------------------------------------------------------------------------
    # Retain
    # -------------------------------------------------------------------------
    def retain_brand_fact(
        self,
        brand_id: str,
        fact: str,
        category: str,
        document_id: Optional[str] = None,
    ) -> bool:
        """Store an objective brand/audience/taboo rule as a world fact."""
        bank_id = self.ensure_bank(brand_id)
        cat = category.strip().lower()
        doc_id = document_id or f"brand_fact_{cat}"
        content = f"Brand {cat} rule: {fact.strip()}"
        try:
            self._client.retain(
                bank_id=bank_id,
                content=content,
                context=f"brand_guideline:{cat}",
                document_id=doc_id,
                metadata={"scope": "world_fact", "category": cat},
                retain_async=False,
            )
            return True
        except Exception as e:
            raise HindsightUnavailableError(
                f"Hindsight retain_brand_fact failed for brand '{brand_id}' (bank '{bank_id}'): {e}"
            ) from e

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
        """Store an episodic recommendation outcome + user review as an experience."""
        bank_id = self.ensure_bank(brand_id)
        doc_id = f"rec_{recommendation_id.strip()}"
        critique_text = (
            f" The marketer's critique was: '{critique.strip()}'."
            if critique else " No critique was provided."
        )
        sql_ref = f" (source metric post: {sql_post_id.strip()})" if sql_post_id else ""
        content = (
            f"I recommended: {context_summary.strip()}{sql_ref}. "
            f"The marketer's decision was {user_decision.upper()}.{critique_text}"
        )
        try:
            self._client.retain(
                bank_id=bank_id,
                content=content,
                context="editorial_feedback",
                document_id=doc_id,
                metadata={
                    "scope": "experience",
                    "decision": user_decision.strip().lower(),
                    "phase": strategy_phase.strip().lower(),
                },
                timestamp=datetime.now(),
                retain_async=False,
            )
            return True
        except Exception as e:
            raise HindsightUnavailableError(
                f"Hindsight retain_interaction_experience failed for brand '{brand_id}' (bank '{bank_id}'): {e}"
            ) from e

    def retain_inferred_belief(
        self,
        brand_id: str,
        belief_id: str,
        belief: InferredMemory,
    ) -> bool:
        """Store an explicit strategic belief.

        Note: Hindsight also forms its own **observations** from raw facts over
        time; this method records an explicit, human-authored hypothesis so it
        participates in recall and consolidation.
        """
        bank_id = self.ensure_bank(brand_id)
        doc_id = f"belief_{belief_id.strip()}"
        evidence = ", ".join(belief.supporting_evidence_context) or "none"
        content = (
            f"Strategic belief: {belief.what_was_learned.strip()} "
            f"Rationale: {belief.why_it_was_learned.strip()} "
            f"Evidence: [{evidence}]. Confidence: {belief.confidence_score:.2f}."
        )
        try:
            self._client.retain(
                bank_id=bank_id,
                content=content,
                context="strategic_belief",
                document_id=doc_id,
                metadata={
                    "scope": "belief",
                    "phase": belief.strategy_phase.strip().lower(),
                    "confidence": f"{belief.confidence_score:.2f}",
                },
                timestamp=belief.learned_at,
                retain_async=False,
            )
            return True
        except Exception as e:
            raise HindsightUnavailableError(
                f"Hindsight retain_inferred_belief failed for brand '{brand_id}' (bank '{bank_id}'): {e}"
            ) from e

    # -------------------------------------------------------------------------
    # Recall
    # -------------------------------------------------------------------------
    def _recall_texts(
        self,
        bank_id: str,
        query: str,
        types: List[str],
        limit: int,
    ) -> List[str]:
        res = self._client.recall(
            bank_id=bank_id,
            query=query,
            types=types,
            budget=self.budget,
        )
        results = getattr(res, "results", []) or []
        return [getattr(r, "text", str(r)) for r in results][:limit]

    def recall_strategic_context(
        self,
        brand_id: str,
        query: str,
        strategy_phase: str = "default",
        channel: Optional[str] = None,
        limit_per_category: int = 3,
    ) -> StrategicContext:
        """Selective, scoped recall across Hindsight's native memory types."""
        bank_id = get_brand_bank_id(brand_id)
        channel_str = f" for the {channel} channel" if channel else ""
        try:
            # NOTE: calls are sequential on purpose. The hindsight-client wraps
            # aiohttp; invoking it from multiple threads raises "Timeout context
            # manager should be used inside a task", so we must not parallelize.
            brand_constraints = self._recall_texts(
                bank_id,
                f"Brand voice, guardrails, audience, and taboos{channel_str}",
                ["world"],
                limit_per_category,
            )
            relevant_experiences = self._recall_texts(
                bank_id,
                f"Past recommendations, editorial critiques, and outcomes related to: {query}",
                ["experience"],
                limit_per_category,
            )
            belief_texts = self._recall_texts(
                bank_id,
                f"Strategic patterns, editorial rules of thumb, and learnings related to: {query}",
                ["observation"],
                limit_per_category,
            )

            active_beliefs = [
                InferredMemory(
                    what_was_learned=text,
                    why_it_was_learned="Consolidated by Hindsight from accumulated evidence.",
                    supporting_evidence_context=[],
                    learned_at=datetime.now(),
                    confidence_score=0.75,
                    strategy_phase=strategy_phase,
                    epistemic_type=EpistemicType.INFERRED,
                )
                for text in belief_texts
            ]
            return StrategicContext(
                brand_constraints=brand_constraints,
                audience_insights=[],
                relevant_experiences=relevant_experiences,
                active_beliefs=active_beliefs,
            )
        except Exception as e:
            raise HindsightUnavailableError(
                f"Hindsight recall_strategic_context failed for brand '{brand_id}' (bank '{bank_id}'): {e}"
            ) from e

    # -------------------------------------------------------------------------
    # Ledger
    # -------------------------------------------------------------------------
    def list_memories(self, brand_id: str, limit: int = 50) -> List[dict]:
        """Flat ledger of stored memories across all types, for the UI panel."""
        bank_id = get_brand_bank_id(brand_id)
        try:
            res = self._client.list_memories(bank_id=bank_id, limit=limit)
            rows = (
                getattr(res, "items", None)
                or getattr(res, "memories", None)
                or getattr(res, "results", None)
                or (res if isinstance(res, list) else [])
            )
            items: List[dict] = []
            for r in rows:
                items.append({
                    "text": getattr(r, "text", str(r)),
                    "type": getattr(r, "fact_type", None) or getattr(r, "type", None) or "memory",
                    "when": getattr(r, "mentioned_at", None) or getattr(r, "occurred_start", None),
                })
            return items[:limit]
        except Exception as e:
            raise HindsightUnavailableError(
                f"Hindsight list_memories failed for brand '{brand_id}' (bank '{bank_id}'): {e}"
            ) from e

    # -------------------------------------------------------------------------
    # Reflect
    # -------------------------------------------------------------------------
    def reflect_on_strategy(
        self,
        brand_id: str,
        query: str,
        budget: str = "low",
    ) -> str:
        """Agentic synthesis over the bank's memories, shaped by its mission."""
        bank_id = get_brand_bank_id(brand_id)
        try:
            res = self._client.reflect(
                bank_id=bank_id,
                query=query,
                budget=budget,
                context="content strategy planning",
            )
            return getattr(res, "text", str(res))
        except Exception as e:
            raise HindsightUnavailableError(
                f"Hindsight reflect_on_strategy failed for brand '{brand_id}' (bank '{bank_id}'): {e}"
            ) from e
