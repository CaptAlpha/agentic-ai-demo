"""Verify the debugging lab without ADK imports or Gemini access."""

import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NAME = "campus_tasks_offline"
package = types.ModuleType(NAME)
package.__path__ = [str(ROOT / "dev_team")]
sys.modules[NAME] = package


def load(name):
    spec = importlib.util.spec_from_file_location(f"{NAME}.{name}", ROOT / "dev_team" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


retrieval = load("retrieval")
tools = load("tools")


class EngineeringLabTests(unittest.TestCase):
    def test_real_experiments_and_unchanged_fixture(self):
        path = ROOT / "sample_repo" / "task_service.py"
        before = path.read_bytes()
        for variant, failures in (("baseline", 4), ("filter_first", 2), ("stable_sort", 3), ("combined", 0)):
            with self.subTest(variant=variant):
                result = tools.evaluate_fix(variant)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["tests_passed"], failures == 0)
                self.assertIn("Ran 8 tests", result["test_output"])
                if failures:
                    self.assertIn(f"FAILED (failures={failures})", result["test_output"])
                self.assertEqual(result["baseline_sha256"], hashlib.sha256(before).hexdigest())
                self.assertEqual(bool(result["patch"]), variant != "baseline")
                self.assertFalse(result["files_modified"])
        self.assertEqual(path.read_bytes(), before)

    def test_reject_unknown_experiment_without_execution(self):
        with patch.object(tools.subprocess, "run") as run:
            self.assertEqual(tools.evaluate_fix("arbitrary shell command")["status"], "error")
            run.assert_not_called()

    def test_changed_fixture_cannot_silently_use_wrong_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tests").mkdir()
            (root / "task_service.py").write_text("# Changed exercise\n", encoding="utf-8")
            (root / "tests" / "test_task_service.py").write_text("", encoding="utf-8")
            with patch.object(tools, "KNOWLEDGE_DIR", root), patch.object(tools.subprocess, "run") as run:
                self.assertEqual(tools.evaluate_fix("combined")["status"], "error")
                run.assert_not_called()

    def test_code_and_contract_retrieval(self):
        documents = retrieval.list_documents()["documents"]
        self.assertIn("task_service.py", documents)
        self.assertIn("tests/test_task_service.py", documents)
        self.assertIn("docs/api_contract.md", documents)
        matches = retrieval.search_knowledge("owner sorted window task", 8)["results"]
        self.assertIn("task_service.py", {result["source"] for result in matches})
        self.assertIn("BEFORE", retrieval.read_document("docs/api_contract.md")["content"])

    def test_citations_and_path_boundaries(self):
        self.assertTrue(tools.validate_citations("[task_service.py:L4-L13]")["all_valid"])
        for citation in ("[task_service.py:L1-L999]", "[../README.md:L1-L4]", "[missing.py:L1-L3]", "no citations"):
            self.assertFalse(tools.validate_citations(citation)["all_valid"])
        self.assertEqual(retrieval.read_document("/etc/passwd")["status"], "error")


if __name__ == "__main__":
    unittest.main()
