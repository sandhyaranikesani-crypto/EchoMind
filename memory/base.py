"""Abstract base classes and DTOs for the EchoMind Memory layer.

Defines the infrastructure contract decoupling business logic from
the underlying Hindsight SDK implementation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class HindsightUnavailableError(Exception):
    """Raised when the Hindsight server is unreachable or fails an operation.

    Never silently swallowed; preserves transparent degradation.
    """
    pass


class EpistemicType(str, Enum):
    """Epistemic classification of memory."""
    FACTUAL = "factual"
    EXPERIENTIAL = "experiential"
    INFERRED = "inferred"


@dataclass
class InferredMemory:
    """Anatomy of an inferred strategic belief passed from the strategy layer.

    Adheres strictly to Rule 6 (preserves proposition, rationale, evidence pointers,
    temporal anchor, confidence score, and strategy phase).
    """
    what_was_learned: str
    why_it_was_learned: str
    supporting_evidence_context: List[str]  # e.g. ["sql_post_id:post_001", "rec_id:rec_004"]
    learned_at: datetime
    confidence_score: float                 # Determined by strategy layer (0.0 to 1.0)
    strategy_phase: str = "default"         # e.g. "awareness", "conversion"
    epistemic_type: EpistemicType = EpistemicType.INFERRED


@dataclass
class StrategicContext:
    """Selective memory payload retrieved for recommendation context synthesis."""
    brand_constraints: List[str] = field(default_factory=list)
    audience_insights: List[str] = field(default_factory=list)
    relevant_experiences: List[str] = field(default_factory=list)
    active_beliefs: List[InferredMemory] = field(default_factory=list)


class MemoryAdapter(ABC):
    """Pure infrastructure contract for storing, retrieving, and reflecting on memory.

    Does not contain hypothesis thresholding or promotion rules; those belong
    exclusively to the strategy layer.
    """

    @abstractmethod
    def retain_brand_fact(
        self,
        brand_id: str,
        fact: str,
        category: str,
        document_id: Optional[str] = None,
    ) -> bool:
        """Store objective brand, audience, or taboo rules."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def retain_inferred_belief(
        self,
        brand_id: str,
        belief_id: str,
        belief: InferredMemory,
    ) -> bool:
        """Store a strategic rule with evidence pointers and confidence score."""
        pass

    @abstractmethod
    def recall_strategic_context(
        self,
        brand_id: str,
        query: str,
        strategy_phase: str = "default",
        channel: Optional[str] = None,
        limit_per_category: int = 3,
    ) -> StrategicContext:
        """Perform selective, scoped recall across logical categories."""
        pass

    @abstractmethod
    def reflect_on_strategy(
        self,
        brand_id: str,
        query: str,
        budget: str = "low",
    ) -> str:
        """Trigger Hindsight reflection to synthesize high-level patterns."""
        pass
