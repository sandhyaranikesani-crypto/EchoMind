"""Automated tests for EchoMind memory integration and adapter contracts.

Validates:
1. Interface contract compliance.
2. Collision-safe brand bank ID mapping.
3. In-memory MockMemoryAdapter lifecycle and tenant isolation.
4. Strategy phase recall filtering.
5. Explicit Hindsight failure behavior (raising HindsightUnavailableError).
6. Factory gating (Mock activated ONLY when HINDSIGHT_USE_MOCK=True).
7. Async-aware live Hindsight integration (skipped if server is unreachable).
"""

import time
import unittest
import urllib.request
from datetime import datetime

from config.settings import Settings, get_brand_bank_id, get_memory_adapter
from memory.base import (
    EpistemicType,
    HindsightUnavailableError,
    InferredMemory,
    MemoryAdapter,
    StrategicContext,
)
from memory.hindsight_adapter import HindsightMemoryAdapter
from memory.mock_adapter import MockMemoryAdapter


class TestMemoryAdapterContract(unittest.TestCase):
    """Test interface compliance and base invariants."""

    def test_subclass_compliance(self):
        """Verify both adapters inherit from MemoryAdapter and implement its methods."""
        self.assertTrue(issubclass(MockMemoryAdapter, MemoryAdapter))
        self.assertTrue(issubclass(HindsightMemoryAdapter, MemoryAdapter))

    def test_bank_id_derivation(self):
        """Verify bank ID mapping is deterministic, sanitized, and collision-safe."""
        self.assertEqual(get_brand_bank_id("brand_01"), "echomind_brand_01")
        self.assertEqual(get_brand_bank_id("B2B-DevTools-Core"), "echomind_b2b-devtools-core")
        self.assertEqual(get_brand_bank_id("brand.with.dots!"), "echomind_brand_with_dots_")

        with self.assertRaises(ValueError):
            get_brand_bank_id("")

        with self.assertRaises(ValueError):
            get_brand_bank_id("   ")


class TestMockMemoryAdapter(unittest.TestCase):
    """Test MockMemoryAdapter functional correctness and tenant isolation."""

    def setUp(self):
        self.adapter = MockMemoryAdapter()
        self.brand_id = "test_brand_alpha"

    def test_retain_and_recall_facts(self):
        """Verify brand facts can be retained and recalled selectively."""
        success = self.adapter.retain_brand_fact(
            brand_id=self.brand_id,
            fact="Never use hyperbolic hype words or aggressive sales hooks.",
            category="taboo",
        )
        self.assertTrue(success)

        context = self.adapter.recall_strategic_context(
            brand_id=self.brand_id,
            query="brand voice and tone",
        )
        self.assertIsInstance(context, StrategicContext)
        self.assertEqual(len(context.brand_constraints), 1)
        self.assertIn("Never use hyperbolic hype words", context.brand_constraints[0])

    def test_retain_interaction_with_evidence_pointers(self):
        """Verify episodic memories store SQL references without duplicating tables."""
        success = self.adapter.retain_interaction_experience(
            brand_id=self.brand_id,
            recommendation_id="rec_101",
            user_decision="REJECTED",
            critique="Too basic; write for staff engineers.",
            context_summary="Microservices 101 tutorial",
            sql_post_id="post_2026_09_042",
            strategy_phase="conversion",
        )
        self.assertTrue(success)

        context = self.adapter.recall_strategic_context(
            brand_id=self.brand_id,
            query="microservices tutorial",
        )
        self.assertEqual(len(context.relevant_experiences), 1)
        exp = context.relevant_experiences[0]
        self.assertIn("post_2026_09_042", exp)
        self.assertIn("Too basic", exp)

    def test_retain_inferred_belief_preserves_anatomy(self):
        """Verify inferred strategic beliefs preserve Rule 6 structural anatomy."""
        belief = InferredMemory(
            what_was_learned="Architecture carousels outperform text essays on LinkedIn by 2.5x.",
            why_it_was_learned="Senior engineering personas prefer visual system teardowns.",
            supporting_evidence_context=["sql_post_id:post_001", "rec_id:rec_101"],
            learned_at=datetime(2026, 9, 28, 12, 0, 0),
            confidence_score=0.82,
            strategy_phase="conversion",
            epistemic_type=EpistemicType.INFERRED,
        )
        success = self.adapter.retain_inferred_belief(
            brand_id=self.brand_id,
            belief_id="belief_arch_carousels",
            belief=belief,
        )
        self.assertTrue(success)

        context = self.adapter.recall_strategic_context(
            brand_id=self.brand_id,
            query="LinkedIn format performance",
            strategy_phase="conversion",
        )
        self.assertEqual(len(context.active_beliefs), 1)
        retrieved_belief = context.active_beliefs[0]
        self.assertEqual(retrieved_belief.confidence_score, 0.82)
        self.assertEqual(retrieved_belief.strategy_phase, "conversion")
        self.assertEqual(retrieved_belief.epistemic_type, EpistemicType.INFERRED)
        self.assertIn("sql_post_id:post_001", retrieved_belief.supporting_evidence_context)

    def test_tenant_brand_isolation(self):
        """Verify strict multi-tenant isolation: memories from brand A never leak to brand B."""
        self.adapter.retain_brand_fact(
            brand_id="brand_isolated_a",
            fact="Brand A confidential strategy constraint.",
            category="confidential",
        )
        self.adapter.retain_brand_fact(
            brand_id="brand_isolated_b",
            fact="Brand B distinct constraint.",
            category="confidential",
        )

        context_a = self.adapter.recall_strategic_context("brand_isolated_a", query="strategy")
        context_b = self.adapter.recall_strategic_context("brand_isolated_b", query="strategy")

        self.assertEqual(len(context_a.brand_constraints), 1)
        self.assertIn("Brand A confidential", context_a.brand_constraints[0])
        self.assertNotIn("Brand B", context_a.brand_constraints[0])

        self.assertEqual(len(context_b.brand_constraints), 1)
        self.assertIn("Brand B distinct", context_b.brand_constraints[0])
        self.assertNotIn("Brand A", context_b.brand_constraints[0])

    def test_strategy_phase_filtering(self):
        """Verify that recall filters out beliefs belonging to other non-matching phases."""
        self.adapter.retain_inferred_belief(
            brand_id=self.brand_id,
            belief_id="belief_q1_awareness",
            belief=InferredMemory(
                what_was_learned="Short memes drive top-of-funnel reach.",
                why_it_was_learned="Broad audience attraction.",
                supporting_evidence_context=[],
                learned_at=datetime.now(),
                confidence_score=0.90,
                strategy_phase="awareness",
            ),
        )
        self.adapter.retain_inferred_belief(
            brand_id=self.brand_id,
            belief_id="belief_q3_conversion",
            belief=InferredMemory(
                what_was_learned="Deep whitepapers drive trial signups.",
                why_it_was_learned="High intent capture.",
                supporting_evidence_context=[],
                learned_at=datetime.now(),
                confidence_score=0.88,
                strategy_phase="conversion",
            ),
        )

        # Recall for conversion phase
        context_conv = self.adapter.recall_strategic_context(
            self.brand_id, query="content", strategy_phase="conversion"
        )
        self.assertEqual(len(context_conv.active_beliefs), 1)
        self.assertEqual(context_conv.active_beliefs[0].strategy_phase, "conversion")
        self.assertIn("Deep whitepapers", context_conv.active_beliefs[0].what_was_learned)

    def test_reflection_synthesis(self):
        """Verify reflect_on_strategy returns a structured pattern synthesis string."""
        self.adapter.retain_brand_fact(self.brand_id, "B2B SaaS focus.", "positioning")
        reflection = self.adapter.reflect_on_strategy(self.brand_id, query="editorial trajectory")
        self.assertIn(f"[MOCK REFLECTION for {self.brand_id}]", reflection)


class TestHindsightFailureAndGating(unittest.TestCase):
    """Test explicit error handling and factory gating."""

    def test_factory_gating(self):
        """Verify MockMemoryAdapter is instantiated ONLY when HINDSIGHT_USE_MOCK=True."""
        mock_settings = Settings(HINDSIGHT_USE_MOCK=True)
        adapter = get_memory_adapter(mock_settings)
        self.assertIsInstance(adapter, MockMemoryAdapter)

        real_settings = Settings(
            HINDSIGHT_USE_MOCK=False,
            HINDSIGHT_BASE_URL="http://localhost:8888",
        )
        adapter_real = get_memory_adapter(real_settings)
        self.assertIsInstance(adapter_real, HindsightMemoryAdapter)

    def test_hindsight_failure_raises_unavailable_error(self):
        """Verify real Hindsight failures raise HindsightUnavailableError (no silent fallback)."""
        # Point to an unreachable port
        unreachable_adapter = HindsightMemoryAdapter(base_url="http://127.0.0.1:59999")

        with self.assertRaises(HindsightUnavailableError):
            unreachable_adapter.retain_brand_fact(
                brand_id="brand_fail_test",
                fact="Test fact that should fail",
                category="test",
            )

        with self.assertRaises(HindsightUnavailableError):
            unreachable_adapter.recall_strategic_context(
                brand_id="brand_fail_test",
                query="test",
            )


class TestLiveHindsightIntegration(unittest.TestCase):
    """Integration test against live Hindsight server (async-aware)."""

    @classmethod
    def setUpClass(cls):
        """Check if local Hindsight server is running before attempting live calls."""
        cls.server_url = "http://localhost:8888"
        cls.is_reachable = False
        try:
            with urllib.request.urlopen(cls.server_url, timeout=1) as response:
                cls.is_reachable = response.status in (200, 404, 405)
        except Exception:
            cls.is_reachable = False

    def test_live_server_status_and_async_recall(self):
        """Execute async-aware retain/recall if Hindsight is reachable, or skip cleanly."""
        if not self.is_reachable:
            self.skipTest(
                f"Hindsight server at {self.server_url} is not running. "
                "Explicit error propagation was verified in TestHindsightFailureAndGating."
            )

        adapter = HindsightMemoryAdapter(base_url=self.server_url)
        brand_id = "test_live_brand_01"
        test_fact = f"Live verification fact created at {time.time()}"

        adapter.retain_brand_fact(brand_id, test_fact, category="live_test")

        # Async-aware polling: wait up to 5 seconds for Hindsight extraction pipeline
        max_wait = 5.0
        start = time.time()
        found = False
        while time.time() - start < max_wait:
            context = adapter.recall_strategic_context(brand_id, query="live verification")
            if any(test_fact in f for f in context.brand_constraints):
                found = True
                break
            time.sleep(0.5)

        self.assertTrue(found, "Retained memory was not indexed within timeout window.")


if __name__ == "__main__":
    unittest.main()
