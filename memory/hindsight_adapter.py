"""Concrete implementation of MemoryAdapter wrapping the official Hindsight SDK.

Interacts with the Hindsight server via hindsight-client.
Raises HindsightUnavailableError on any communication or server failure.
Never performs silent fallbacks.
"""

from datetime import datetime
from typing import List, Optional

from hindsight_client import Hindsight

from config.settings import get_brand_bank_id
from memory.base import (
    EpistemicType,
    HindsightUnavailableError,
    InferredMemory,
    MemoryAdapter,
    StrategicContext,
)


class HindsightMemoryAdapter(MemoryAdapter):
    """Production memory adapter backed by the Hindsight SDK."""

    def __init__(
        self,
        base_url: str = "http://localhost:8888",
        api_key: Optional[str] = None,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        try:
            self._client = Hindsight(
                base_url=self.base_url,
                api_key=self.api_key or None,
            )
        except Exception as e:
            raise HindsightUnavailableError(
                f"Failed to initialize Hindsight client with base_url '{self.base_url}': {e}"
            ) from e

    def retain_brand_fact(
        self,
        brand_id: str,
        fact: str,
        category: str,
        document_id: Optional[str] = None,
    ) -> bool:
        """Store objective brand, audience, or taboo rules in Hindsight."""
        bank_id = get_brand_bank_id(brand_id)
        doc_id = document_id or f"brand_fact_{category.strip().lower()}"
        content = f"[BRAND FACT - {category.upper()}] {fact.strip()}"
        tags = ["scope:world_fact", f"category:{category.strip().lower()}"]
        context = f"brand_guideline_{category.strip().lower()}"

        try:
            self._client.retain(
                bank_id=bank_id,
                content=content,
                document_id=doc_id,
                context=context,
                tags=tags,
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
        """Store an episodic recommendation outcome and user review in Hindsight."""
        bank_id = get_brand_bank_id(brand_id)
        doc_id = f"rec_{recommendation_id.strip()}"
        critique_text = f" User Critique: '{critique.strip()}'" if critique else " No critique provided."
        sql_ref = f" Reference SQL Post ID: {sql_post_id.strip()}." if sql_post_id else ""
        content = (
            f"[AGENT EXPERIENCE - REC {recommendation_id}] Decision: {user_decision.upper()}. "
            f"Proposal Summary: {context_summary.strip()}.{critique_text}{sql_ref} "
            f"Strategy Phase: {strategy_phase}."
        )
        tags = [
            "scope:experience",
            f"phase:{strategy_phase.strip().lower()}",
            f"decision:{user_decision.strip().lower()}",
        ]
        context = "marketer_editorial_feedback"

        try:
            self._client.retain(
                bank_id=bank_id,
                content=content,
                document_id=doc_id,
                context=context,
                tags=tags,
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
        """Store a strategic rule with evidence pointers and confidence score."""
        bank_id = get_brand_bank_id(brand_id)
        doc_id = f"belief_{belief_id.strip()}"
        evidence_str = ", ".join(belief.supporting_evidence_context) if belief.supporting_evidence_context else "None"
        content = (
            f"[INFERRED BELIEF - {belief_id}]\n"
            f"• Proposition: {belief.what_was_learned.strip()}\n"
            f"• Rationale: {belief.why_it_was_learned.strip()}\n"
            f"• Evidence Pointers: [{evidence_str}]\n"
            f"• Confidence Score: {belief.confidence_score:.2f}\n"
            f"• Learned At: {belief.learned_at.isoformat()}\n"
            f"• Strategy Phase: {belief.strategy_phase.strip()}"
        )
        tags = [
            "scope:belief",
            f"phase:{belief.strategy_phase.strip().lower()}",
        ]
        context = "inferred_strategic_heuristic"

        try:
            self._client.retain(
                bank_id=bank_id,
                content=content,
                document_id=doc_id,
                context=context,
                tags=tags,
            )
            return True
        except Exception as e:
            raise HindsightUnavailableError(
                f"Hindsight retain_inferred_belief failed for brand '{brand_id}' (bank '{bank_id}'): {e}"
            ) from e

    def recall_strategic_context(
        self,
        brand_id: str,
        query: str,
        strategy_phase: str = "default",
        channel: Optional[str] = None,
        limit_per_category: int = 3,
    ) -> StrategicContext:
        """Perform selective, scoped recall across logical categories."""
        bank_id = get_brand_bank_id(brand_id)
        channel_str = f" for channel {channel}" if channel else ""

        try:
            # 1. Recall World Facts (Brand constraints & taboos)
            facts_res = self._client.recall(
                bank_id=bank_id,
                query=f"Brand constraints, taboos, and tone rules{channel_str}",
                tags=["scope:world_fact"],
                tags_match="any",
            )
            raw_facts = [r.text for r in getattr(facts_res, "results", [])]
            brand_constraints = raw_facts[:limit_per_category]

            # 2. Recall Experiences (Past recommendations and user feedback)
            exp_res = self._client.recall(
                bank_id=bank_id,
                query=f"Past recommendations, editorial critiques, and outcomes related to: {query}",
                tags=["scope:experience"],
                tags_match="any",
            )
            raw_exps = [r.text for r in getattr(exp_res, "results", [])]
            relevant_experiences = raw_exps[:limit_per_category]

            # 3. Recall Inferred Beliefs (Scoped to current strategy phase)
            belief_tags = ["scope:belief", f"phase:{strategy_phase.strip().lower()}"]
            belief_res = self._client.recall(
                bank_id=bank_id,
                query=f"Strategic patterns, editorial rules, and hypotheses related to: {query}",
                tags=belief_tags,
                tags_match="any",
            )
            raw_beliefs = [r.text for r in getattr(belief_res, "results", [])][:limit_per_category]

            active_beliefs = []
            for b_text in raw_beliefs:
                # Reconstruct InferredMemory DTO from returned text
                active_beliefs.append(
                    InferredMemory(
                        what_was_learned=b_text,
                        why_it_was_learned="Retrieved from Hindsight Evolving Beliefs network.",
                        supporting_evidence_context=[],
                        learned_at=datetime.now(),
                        confidence_score=0.75,
                        strategy_phase=strategy_phase,
                        epistemic_type=EpistemicType.INFERRED,
                    )
                )

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

    def reflect_on_strategy(
        self,
        brand_id: str,
        query: str,
        budget: str = "low",
    ) -> str:
        """Trigger Hindsight reflection to synthesize high-level patterns."""
        bank_id = get_brand_bank_id(brand_id)
        try:
            res = self._client.reflect(
                bank_id=bank_id,
                query=query,
                budget=budget,
            )
            return getattr(res, "text", str(res))
        except Exception as e:
            raise HindsightUnavailableError(
                f"Hindsight reflect_on_strategy failed for brand '{brand_id}' (bank '{bank_id}'): {e}"
            ) from e
