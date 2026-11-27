# Agentic RAG: local knowledge assistant

Ask a Gemini agent questions about the fictional company **Northstar Labs**. It retrieves local policy passages, decides whether to search again or read more context, and produces answers with file and line citations.

## Why this demonstrates agentic RAG

**Retrieval-augmented generation (RAG)** supplies external evidence to a language model before it answers. Here, the documents stay on disk until the agent requests passages through tools. The agent controls which queries to issue, can split a compound question across documents, and can inspect surrounding text before answering. This differs from a fixed pipeline that always runs one search and generates an answer.

```text
User question
     |
     v
Gemini / ADK agent <----> list_documents
     |             <----> search_knowledge (BM25 ranking)
     |             <----> read_document (verify context)
     |                          |
     |                    local .md / .txt files
     v
Evidence-grounded answer + [filename:Lstart-Lend] citations
```

The retrieval layer is **lexical BM25**, not embedding-based semantic search. It uses word overlap and document statistics, runs offline using Python's standard library, and needs no vector database or embedding API. Gemini generation still requires network access and an API key.

ADK exposes the Python functions as tools using its [function tools interface](https://github.com/google/adk-docs/blob/main/docs/tools-custom/function-tools.md).

## Run

From the repository root, activate the environment described in the root README. A current supported Python version (3.11 or newer recommended) and `google-adk` are needed for the agent. No additional retrieval dependencies are required.

```bash
source .venv/bin/activate
export GOOGLE_GENAI_USE_VERTEXAI=FALSE
export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
export RAG_MODEL="gemini-3.5-flash"
cd rag_demo
adk web
```

Open the URL printed by ADK and choose **knowledge_agent**. The web interface lets you inspect tool calls, queries, retrieved passages, and the final answer. Use a Gemini model available to your account; `RAG_MODEL` overrides the default.

For terminal chat, run this from `rag_demo` instead:

```bash
adk run knowledge_agent
```

## Practice questions

1. **Simple retrieval:** “How much can I claim for home office equipment, and what approval do I need?” Expect INR 15,000 and manager approval before purchase, cited to `remote_work.md`.
2. **Multiple sources:** “Can I claim a monitor and internet? Explain the separate allowances, receipt deadline, and payment timeline.” Look for searches covering both remote work and expense policies. Equipment is INR 15,000 once, internet is INR 1,000 monthly, claims are due in 30 calendar days, and payment follows Finance approval within 10 business days.
3. **Conditions and exceptions:** “Can I work abroad for 60 days?” The policy requires approval before travel but does not specify a maximum duration. The answer should identify that gap rather than approve the request.
4. **Missing evidence:** “What is the parental leave policy?” The documents contain no parental leave policy. The agent should say it cannot answer from the knowledge base.
5. **Fresh data:** Edit an allowance in a sample document, save, and ask again. Each tool call reads the files again; no separate indexing job is required. Earlier conversation messages can contain stale facts, so request a fresh search or start a new session.

Answers are generated, so exact wording and tool sequences vary. These are expected behaviors to inspect, not guarantees enforced by a citation validator.

## Files and implementation

| File | Purpose |
| --- | --- |
| `knowledge_agent/agent.py` | ADK agent, model configuration, evidence and citation instructions |
| `knowledge_agent/retrieval.py` | Document loading, overlapping chunks, BM25 scoring, bounded source reads |
| `knowledge_base/remote_work.md` | Fictional remote work and equipment policy |
| `knowledge_base/expenses.md` | Fictional reimbursement and internet policy |
| `knowledge_base/leave.md` | Fictional leave and onboarding policy |
| `tests/test_retrieval.py` | Offline retrieval, citation, boundary, and refresh checks |

The retriever creates 20-line windows with four lines of overlap. It ranks passages against non-stopword query tokens and returns up to eight positive-scoring passages. Each result carries its exact text, source, line range, score, and citation. `read_document` reads at most 80 lines and rejects paths outside the knowledge directory. Scores measure keyword relevance, not certainty.

## Add your own knowledge

Put UTF-8 `.md` or `.txt` documents inside `rag_demo/knowledge_base/`, including subdirectories. New and edited files are picked up on the next tool call. Replace the sample policies and update the agent's company-specific instructions when adapting the demo to a new topic.

Markdown files directly inside the sample knowledge directory are allowed by `.gitignore`. Other text files and nested Markdown files may need explicit ignore exceptions if you intend to commit them. Keep private documents out of public repositories.

This demo does not parse PDFs or scanned documents. Convert them into reviewed text first. Retrieved passages are sent to the configured model service when used as tool results.

## Test retrieval without an API key

From the repository root:

```bash
python3 -m unittest discover -s rag_demo/tests -v
```

These tests exercise the retriever, not live Gemini generation. No credentials, model calls, or ADK imports are needed.

## Limitations

- BM25 may miss synonyms and paraphrases with little word overlap. Try more specific terms or extend retrieval with embeddings or hybrid search.
- The index is rebuilt in memory per tool call, suitable for a small demo corpus. Larger collections need caching, incremental ingestion, and a dedicated search index.
- Line citations change when files change. There is no versioned evidence store.
- Grounding, search budgets, and rejection of instructions embedded in documents are agent instructions, not hard enforcement. Production systems need stronger validation and access controls.
- Local retrieval does not require credentials; end-to-end chat requires a working Gemini model and account quota.
