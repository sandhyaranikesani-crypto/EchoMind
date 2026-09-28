import unittest

from agent.orchestrator import EchoMindAgent
from database.repository import ContentRepository


class TestStrategyFlow(unittest.TestCase):

    def test_strategy_analysis(self):
        repo = ContentRepository()
        agent = EchoMindAgent(repo)

        brands = repo.list_brands()

        self.assertGreater(len(brands), 0)

        brand_id = brands[0]["id"]

        result = agent.generate_baseline_recommendation(
            brand_id=brand_id
        )

        print("\n========== ECHOMIND BASELINE ==========")
        print("Brand:", result["brand_name"])

        print("\nRecommended Pillar:")
        print(result["recommended_pillar"])

        print("\nRecommended Format:")
        print(result["recommended_format"])

        print("\nReasoning:")
        for reason in result["reasoning"]:
            print("-", reason)

        print("=======================================\n")


if __name__ == "__main__":
    unittest.main()