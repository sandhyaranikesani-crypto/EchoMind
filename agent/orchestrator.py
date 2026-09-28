"""
EchoMind Agent Orchestrator.

Coordinates the factual strategy analysis.
Hindsight and LLM generation will be connected in the next step.
"""

from typing import Any, Dict, Optional

from database.repository import ContentRepository
from strategy.engine import StrategyEngine


class EchoMindAgent:
    """Main orchestrator for EchoMind."""

    def __init__(self, repository: Optional[ContentRepository] = None):
        self.repository = repository or ContentRepository()
        self.strategy_engine = StrategyEngine(self.repository)

    def analyze_strategy(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze the brand's current content strategy.

        Currently uses deterministic SQL-based analysis.
        Hindsight memory and LLM reasoning will be added next.
        """

        brand = self.repository.get_brand(brand_id)

        if not brand:
            raise ValueError(f"Brand not found: {brand_id}")

        analysis = self.strategy_engine.analyze(
            brand_id=brand_id,
            platform_id=platform_id,
        )

        return {
            "brand": brand,
            "analysis": analysis,
        }

    def generate_baseline_recommendation(
        self,
        brand_id: str,
        platform_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a deterministic baseline recommendation.

        This is intentionally NOT the final AI recommendation.
        It gives us a baseline before adding Hindsight memory.
        """

        result = self.analyze_strategy(
            brand_id=brand_id,
            platform_id=platform_id,
        )

        analysis = result["analysis"]

        recommendation = {
            "brand_name": result["brand"]["name"],
            "recommended_pillar": analysis.recommended_pillar,
            "recommended_format": analysis.recommended_format,
            "reasoning": analysis.summary_bullets,
        }

        return recommendation