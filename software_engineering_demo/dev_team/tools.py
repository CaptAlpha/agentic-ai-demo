"""Allowlisted experiments on a disposable copy of the teaching fixture."""

import difflib
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from .retrieval import KNOWLEDGE_DIR, read_document

SORT_LINE = '    ordered = sorted(tasks, key=lambda task: task["created_at"])'
FILTER_SORT = '    ordered = sorted((task for task in tasks if task["owner"] == owner), key=lambda task: task["created_at"])'
STABLE_SORT = '    ordered = sorted(tasks, key=lambda task: (task["created_at"], task["id"]))'
COMBINED_SORT = '    ordered = sorted((task for task in tasks if task["owner"] == owner), key=lambda task: (task["created_at"], task["id"]))'
VARIANTS = {"baseline": None, "filter_first": FILTER_SORT,
            "stable_sort": STABLE_SORT, "combined": COMBINED_SORT}


def list_experiments() -> dict:
    """Describe the predefined repair hypotheses available for test experiments."""
    return {"experiments": {
        "baseline": "Run unchanged task_service.py.",
        "filter_first": "Filter by owner before pagination; keep timestamp-only sorting.",
        "stable_sort": "Add ID tie-breaker; keep global pagination before owner filtering.",
        "combined": "Filter by owner first and sort by (created_at, id).",
    }, "scope": "Pre-authored one-line repair candidates, not arbitrary code generation. No project files are changed."}


def evaluate_fix(fix_variant: str = "baseline") -> dict:
    """Run the trusted regression suite against one predefined repair in a temp copy.

    Args:
        fix_variant: baseline, filter_first, stable_sort, or combined.
    """
    if fix_variant not in VARIANTS:
        return {"status": "error", "message": "Choose an experiment from list_experiments."}
    try:
        original = (KNOWLEDGE_DIR / "task_service.py").read_text(encoding="utf-8")
        test_source = (KNOWLEDGE_DIR / "tests" / "test_task_service.py").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {"status": "error", "message": str(exc)}
    replacement = VARIANTS[fix_variant]
    if replacement is not None and original.count(SORT_LINE) != 1:
        return {"status": "error", "message": "Fixture changed: expected exactly one baseline sort statement. Update the predefined experiments before running a repair."}
    candidate = original if replacement is None else original.replace(SORT_LINE, replacement, 1)
    diff = "".join(difflib.unified_diff(original.splitlines(keepends=True),
                                     candidate.splitlines(keepends=True),
                                     fromfile="a/task_service.py", tofile="b/task_service.py"))
    # Only the two explicit fixture files are copied; no student repo shell commands.
    with tempfile.TemporaryDirectory(prefix="campus_tasks_") as directory:
        root = Path(directory)
        (root / "tests").mkdir()
        (root / "task_service.py").write_text(candidate, encoding="utf-8")
        (root / "tests" / "test_task_service.py").write_text(test_source, encoding="utf-8")
        command = [sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]
        try:
            result = subprocess.run(command, cwd=root, env={"PATH": os.defpath},
                                    capture_output=True, text=True, timeout=15)
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Regression suite exceeded 15 seconds.", "variant": fix_variant}
    output = result.stdout + result.stderr
    return {"status": "success", "variant": fix_variant, "tests_passed": result.returncode == 0,
            "exit_code": result.returncode, "test_output": output[:16000],
            "output_truncated": len(output) > 16000, "patch": diff,
            "baseline_sha256": hashlib.sha256(original.encode()).hexdigest(),
            "test_suite_sha256": hashlib.sha256(test_source.encode()).hexdigest(),
            "files_modified": False,
            "scope": "Only the bundled unit tests were executed in a temporary copy; not a proof of production correctness."}


def validate_citations(answer: str) -> dict:
    """Validate code/document citations and return their source text for review.

    Args:
        answer: Draft containing citations like [task_service.py:L4-L13].
    """
    citations = re.findall(r"\[([^\[\]\n:]+):L(\d+)-L(\d+)\]", answer)
    results = []
    for source, start, end in dict.fromkeys(citations):
        passage = read_document(source, int(start), int(end))
        valid = passage.get("status") == "success" and passage.get("end_line") == int(end)
        results.append({"citation": f"[{source}:L{start}-L{end}]", "valid": valid,
                        "content": passage.get("content", "") if valid else ""})
    return {"citation_count": len(results), "all_valid": bool(results) and all(item["valid"] for item in results),
            "citations": results, "limitation": "Valid line ranges do not establish that a cited claim is supported."}
