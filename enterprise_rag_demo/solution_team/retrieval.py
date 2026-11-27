"""Small, offline BM25 retriever with stable, line-based citations."""

import math
import re
from collections import Counter
from pathlib import Path


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge_base"
STOPWORDS = set("a an the is are was were of to for in on and or with how what can i my do does it me about".split())


def tokens(text):
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS]


def load_chunks():
    """Rebuild the small in-memory index on each call so edits appear immediately."""
    chunks = []
    warnings = []
    for path in sorted(KNOWLEDGE_DIR.rglob("*")):
        # Do not follow links to documents outside the demo's knowledge directory.
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
            continue
        if KNOWLEDGE_DIR.resolve() not in path.resolve().parents:
            continue
        source = path.relative_to(KNOWLEDGE_DIR).as_posix()
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            warnings.append({"source": source, "error": str(exc)})
            continue
        # Overlapping windows preserve nearby context and bound tool response size.
        for start in range(0, len(lines), 16):
            end = min(start + 20, len(lines))
            content = "\n".join(lines[start:end]).strip()
            if not content:
                continue
            chunks.append({
                "source": source,
                "start_line": start + 1,
                "end_line": end,
                "citation": f"[{source}:L{start + 1}-L{end}]",
                "content": content,
            })
            if end == len(lines):
                break
    return chunks, warnings


def list_documents() -> dict:
    """List available local knowledge documents before planning searches."""
    chunks, warnings = load_chunks()
    return {"documents": sorted({chunk["source"] for chunk in chunks}),
            "chunk_count": len(chunks), "warnings": warnings}


def search_knowledge(query: str, top_k: int = 4) -> dict:
    """Retrieve relevant passages using BM25 keyword ranking.

    Args:
        query: Specific search terms; try alternate wording if evidence is missing.
        top_k: Maximum passages to return, between 1 and 8.
    """
    if not query.strip():
        return {"status": "error", "message": "Provide a nonempty search query."}
    chunks, warnings = load_chunks()
    terms = set(tokens(query))
    counts = [Counter(tokens(chunk["content"])) for chunk in chunks]
    lengths = [sum(count.values()) for count in counts]
    average = sum(lengths) / len(lengths) if lengths else 1
    results = []
    for chunk, count, length in zip(chunks, counts, lengths):
        score = 0.0
        for term in terms:
            frequency = count[term]
            if not frequency:
                continue
            document_frequency = sum(term in other for other in counts)
            idf = math.log(1 + (len(chunks) - document_frequency + 0.5) / (document_frequency + 0.5))
            score += idf * frequency * 2.5 / (frequency + 1.5 * (0.25 + 0.75 * length / (average or 1)))
        if score > 0:
            results.append(dict(chunk, score=round(score, 4)))
    results.sort(key=lambda result: (-result["score"], result["source"], result["start_line"]))
    return {"status": "success", "query": query, "retrieval": "BM25 lexical search",
            "results": results[:max(1, min(top_k, 8))], "warnings": warnings,
            "message": "" if results else "No matching evidence. Try different keywords or report missing information."}


def read_document(source: str, start_line: int = 1, end_line: int = 60) -> dict:
    """Read up to 80 lines of a retrieved source to check surrounding context.

    Args:
        source: Relative document name returned by list_documents or search_knowledge.
        start_line: First line to read (one-based).
        end_line: Last line to read (inclusive).
    """
    root = KNOWLEDGE_DIR.resolve()
    path = (root / source).resolve()
    if root not in path.parents or path.suffix.lower() not in {".md", ".txt"}:
        return {"status": "error", "message": "Only knowledge-base Markdown and text documents can be read."}
    if start_line < 1 or end_line < start_line:
        return {"status": "error", "message": "Use a valid one-based line range."}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return {"status": "error", "message": str(exc)}
    if start_line > len(lines):
        return {"status": "error", "message": "Start line exceeds document length."}
    end = min(end_line, start_line + 79, len(lines))
    return {"status": "success", "source": source, "start_line": start_line,
            "end_line": end, "citation": f"[{source}:L{start_line}-L{end}]",
            "content": "\n".join(lines[start_line - 1:end])}
