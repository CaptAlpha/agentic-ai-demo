"""Exercise retrieval without importing ADK or making network requests."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "knowledge_agent" / "retrieval.py"
spec = importlib.util.spec_from_file_location("retrieval", MODULE)
retrieval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retrieval)


class RetrievalTests(unittest.TestCase):
    def test_relevant_policy_and_verifiable_citation(self):
        result = retrieval.search_knowledge("home office equipment allowance")
        first = result["results"][0]
        self.assertEqual(first["source"], "remote_work.md")
        self.assertIn("15,000", first["content"])
        passage = retrieval.read_document(first["source"], first["start_line"], first["end_line"])
        self.assertEqual(passage["content"].strip(), first["content"])
        self.assertEqual(passage["citation"], first["citation"])

    def test_cross_document_retrieval(self):
        results = retrieval.search_knowledge("equipment internet allowance", 8)["results"]
        sources = {result["source"] for result in results}
        self.assertTrue({"remote_work.md", "expenses.md"}.issubset(sources))

    def test_absent_evidence_and_empty_query(self):
        self.assertEqual(retrieval.search_knowledge("spaceship teleportation")["results"], [])
        self.assertEqual(retrieval.search_knowledge(" ")["status"], "error")

    def test_reject_paths_outside_knowledge_base(self):
        for path in ("../knowledge_agent/agent.py", "/etc/passwd", "../README.md"):
            self.assertEqual(retrieval.read_document(path)["status"], "error")

    def test_invalid_line_ranges(self):
        for start, end in ((0, 4), (10, 2), (999, 1000)):
            self.assertEqual(retrieval.read_document("leave.md", start, end)["status"], "error")

    def test_reindex_edits_overlap_and_empty_corpus(self):
        original = retrieval.KNOWLEDGE_DIR
        try:
            with tempfile.TemporaryDirectory() as directory:
                retrieval.KNOWLEDGE_DIR = Path(directory)
                self.assertEqual(retrieval.list_documents()["documents"], [])
                self.assertEqual(retrieval.search_knowledge("policy")["results"], [])
                document = Path(directory) / "policy.md"
                document.write_text("\n".join(f"Policy line {i}" for i in range(45)), encoding="utf-8")
                chunks, _ = retrieval.load_chunks()
                self.assertEqual([(c["start_line"], c["end_line"]) for c in chunks], [(1, 20), (17, 36), (33, 45)])
                document.write_text("Updated benefit: bicycle allowance", encoding="utf-8")
                self.assertIn("bicycle", retrieval.search_knowledge("bicycle")["results"][0]["content"])
                (Path(directory) / "outside.md").symlink_to(MODULE)
                self.assertNotIn("outside.md", retrieval.list_documents()["documents"])
        finally:
            retrieval.KNOWLEDGE_DIR = original


if __name__ == "__main__":
    unittest.main()
