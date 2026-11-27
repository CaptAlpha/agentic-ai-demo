"""Offline tests: no ADK imports, model calls, or API credentials."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "enterprise_offline_tools"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT / "solution_team")]
sys.modules[PACKAGE] = package


def load(name):
    spec = importlib.util.spec_from_file_location(f"{PACKAGE}.{name}", ROOT / "solution_team" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


retrieval = load("retrieval")
tools = load("tools")


class EnterpriseTests(unittest.TestCase):
    def test_full_demo_costs(self):
        for vendor, total in (("atlas", "290000.00"), ("beacon", "260000.00"), ("cedar", "340000.00")):
            quote = tools.calculate_quote(vendor, 25, 12, 350000)
            self.assertEqual(quote["total_inr"], total)
            self.assertTrue(quote["within_budget"])
        self.assertEqual(tools.calculate_quote("atlas", 25, 12, 280000)["remaining_budget_inr"], "-10000.00")

    def test_minimum_seats_and_budget_boundary(self):
        quote = tools.calculate_quote("beacon", 2, 1, 50000)
        self.assertEqual(quote["billed_seats"], 20)
        self.assertEqual(quote["total_inr"], "50000.00")
        self.assertTrue(quote["within_budget"])

    def test_invalid_inputs(self):
        for args in (("unknown", 2, 12, 100), ("atlas", 0, 12, 100),
                     ("atlas", 2, -1, 100), ("atlas", 2, 12, -1),
                     ("atlas", 2, 12, float("nan")), ("atlas", True, 12, 100)):
            self.assertEqual(tools.calculate_quote(*args)["status"], "error")

    def test_citation_validation(self):
        self.assertTrue(tools.validate_citations("Policy [procurement.md:L1-L10]")["all_valid"])
        for text in ("No citations", "[missing.md:L1-L5]", "[atlas.md:L1-L999]", "[../README.md:L1-L5]"):
            self.assertFalse(tools.validate_citations(text)["all_valid"])

    def test_retrieval_and_conflicting_policy_available(self):
        results = retrieval.search_knowledge("procurement approval policy", 8)["results"]
        sources = {result["source"] for result in results}
        self.assertTrue({"procurement.md", "procurement_legacy.md"}.issubset(sources))
        self.assertIn("Singapore", retrieval.read_document("beacon.md")["content"])
        self.assertIn("not supported", retrieval.read_document("cedar.md")["content"])
        self.assertEqual(retrieval.search_knowledge("teleportation")["results"], [])

    def test_catalog_matches_vendor_documents(self):
        for vendor, record in tools.CATALOG.items():
            content = retrieval.read_document(f"{vendor}.md")["content"]
            self.assertIn(f"Monthly price per seat: INR {record['monthly_inr']:,}.", content)
            self.assertIn(f"One-time setup fee: INR {record['setup_inr']:,}.", content)
            self.assertIn(f"Minimum billed seats: {record['minimum_seats']}.", content)


if __name__ == "__main__":
    unittest.main()
