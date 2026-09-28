"""Tests for the memory-integrated agent loop.

Exercises the full recall -> recommend -> retain cycle using the offline
MockMemoryAdapter and an isolated temporary SQLite database.
"""

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from agent.orchestrator import EchoMindAgent
from database.repository import ContentRepository
from database.seed import seed_database
from memory.base import HindsightUnavailableError
from memory.mock_adapter import MockMemoryAdapter

BRAND_ID = "brand_echomind"


class TestAgentMemoryLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        seed_database(cls.db_path)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.db_path)
        except OSError:
            pass

    def setUp(self):
        # Force the deterministic narrator so unit tests never hit a live LLM,
        # regardless of whether an LLM key is present in the environment/.env.
        self._llm_patch = mock.patch(
            "agent.llm.settings",
            SimpleNamespace(LLM_API_KEY="", LLM_BASE_URL=None, LLM_MODEL="test"),
        )
        self._llm_patch.start()

    def tearDown(self):
        self._llm_patch.stop()

    def _agent(self, memory=None):
        repo = ContentRepository(db_path=self.db_path)
        return EchoMindAgent(
            repository=repo,
            memory=memory if memory is not None else MockMemoryAdapter(),
            strategy_phase="default",
        )

    def test_recommendation_shape(self):
        agent = self._agent()
        rec = agent.generate_recommendation(BRAND_ID)
        self.assertIn("recommendation_id", rec)
        self.assertTrue(rec["memory_online"])
        self.assertIsNotNone(rec["recommended_pillar"])
        self.assertIsNotNone(rec["recommended_format"])
        self.assertIn("body", rec["narrative"])
        self.assertEqual(rec["narrative"]["source"], "deterministic")
        # The known seed gap should surface as the recommended pillar.
        self.assertEqual(
            rec["recommended_pillar"]["pillar_name"],
            "Engineering Culture & Leadership",
        )

    def test_bootstrapped_memory_flows_into_recommendation(self):
        agent = self._agent()
        written = agent.bootstrap_demo_memory(BRAND_ID)
        self.assertGreater(written, 0)

        rec = agent.generate_recommendation(BRAND_ID)
        self.assertTrue(rec["brand_constraints"], "brand facts should be recalled")
        self.assertTrue(rec["active_beliefs"], "beliefs should be recalled")
        # The recalled guardrail should appear in the deterministic narrative body.
        self.assertIn("guardrails", rec["narrative"]["body"].lower())

    def test_feedback_is_retained_and_recalled(self):
        memory = MockMemoryAdapter()
        agent = self._agent(memory=memory)

        rec = agent.generate_recommendation(BRAND_ID)
        ok = agent.record_feedback(
            brand_id=BRAND_ID,
            recommendation_id=rec["recommendation_id"],
            decision="REJECT",
            context_summary="Proposed culture carousel",
            critique="Audience prefers deep technical teardowns over culture posts.",
        )
        self.assertTrue(ok)

        # A subsequent recommendation should surface the prior experience.
        rec2 = agent.generate_recommendation(BRAND_ID)
        joined = " ".join(rec2["relevant_experiences"]).lower()
        self.assertIn("reject", joined)
        self.assertIn("teardowns", joined)

    def test_memory_changes_the_recommendation(self):
        """Rejecting the default format should switch the recommended format."""
        memory = MockMemoryAdapter()
        agent = self._agent(memory=memory)

        baseline = agent.generate_comparison(BRAND_ID)
        base_fmt = baseline["memory_plan"]["baseline_format"]["format_name"]
        self.assertFalse(baseline["memory_plan"]["adjusted"])  # nothing learned yet

        # Reject the default format explicitly.
        agent.record_feedback(
            brand_id=BRAND_ID,
            recommendation_id=baseline["recommendation_id"],
            decision="REJECT",
            context_summary=f"a {base_fmt} post under 'Engineering Culture & Leadership'",
            critique="Carousels underperform for us; prefer technical threads.",
        )

        adjusted = agent.generate_comparison(BRAND_ID)
        plan = adjusted["memory_plan"]
        self.assertTrue(plan["adjusted"], "memory should switch the format after a rejection")
        self.assertNotEqual(plan["format"]["format_name"], base_fmt)
        self.assertTrue(plan["adjustments"])

    def test_offline_memory_degrades_transparently(self):
        repo = ContentRepository(db_path=self.db_path)
        agent = EchoMindAgent(repository=repo, memory=None, strategy_phase="default")
        # Force the offline condition regardless of local environment/SDK state.
        agent.memory = None
        agent.memory_error = "forced offline for test"

        rec = agent.generate_recommendation(BRAND_ID)
        self.assertFalse(rec["memory_online"])
        self.assertEqual(rec["brand_constraints"], [])
        self.assertIsNotNone(rec["recommended_pillar"])  # deterministic path still works

        with self.assertRaises(HindsightUnavailableError):
            agent.record_feedback(
                brand_id=BRAND_ID,
                recommendation_id="x",
                decision="ACCEPT",
                context_summary="whatever",
            )


if __name__ == "__main__":
    unittest.main()
