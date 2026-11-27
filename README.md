# Agentic AI Demo

Six Python demos built with Google's Agent Development Kit (ADK) and Gemini. Each shows how an AI agent can use tools to gather information, perform calculations, and produce a useful response.

The examples cover tool calling, subagent delegation, retrieval-augmented generation (RAG), parallel workflows, shared state, and test-driven debugging.

## Demos at a glance

| Demo | What it does | Tools and data |
| --- | --- | --- |
| PDF and invoice analysis | Reads a local PDF and summarizes or calculates statistics from its contents | `pypdf`, `read_pdf`, `calculate_stats` |
| Web research | Basic research-agent definition for exploring ADK configuration | Gemini; search integration is incomplete |
| Stock research | Combines a market snapshot, period return, and recent company news | `yfinance`, Google Search, a delegated news agent |
| [Agentic RAG](rag_demo/README.md) | Searches local policy documents, verifies context, and answers with source citations | Offline BM25 retrieval, document reading, Gemini |
| [Enterprise RAG team](enterprise_rag_demo/README.md) | Plans a procurement comparison, runs specialists in parallel, calculates costs, reviews evidence, and revises a cited brief | Seven LLM agents, sequential/parallel workflows, RAG, shared state, calculation and citation tools |
| [Software engineering team](software_engineering_demo/README.md) | Investigates a task-tracker bug, retrieves code/contracts, tests repair hypotheses, and reviews a patch | Parallel subagents, code RAG, real unittest runs, temporary repair experiments, code review |

**For CS students:** start with the [CampusTasks debugging lab](software_engineering_demo/README.md). It includes a deliberately buggy Python service, a classroom walkthrough, and real before/after test results. Run `adk web` from `software_engineering_demo` and select `dev_team` after configuring Gemini credentials.

Each demo has its own examples and instructions. The RAG and software engineering demos also include offline tests.

## Repository structure

```text
agentic-ai-demo/
├── invoice_demo/
│   └── invoice_agent/
│       └── agent.py             # PDF reading and numeric statistics
├── research_demo/
│   └── researh_agent/
│       └── agent.py             # Custom web search wrapper
├── stock_demo/
│   └── stock_researcher/
│       ├── __init__.py
│       └── agent.py             # Market tools and delegated news analysis
├── rag_demo/                    # Local knowledge-base RAG
├── enterprise_rag_demo/         # Procurement team with parallel specialists
├── software_engineering_demo/   # Code RAG and regression-test experiments
├── .gitignore
└── README.md
```

**Path note:** `researh_agent` is the folder's current spelling. Use it exactly as shown in commands.

## Setup

### 1. Create a Python environment

Use a Python version supported by the installed Google ADK release. Run these commands from the repository root on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install google-adk google-genai pypdf yfinance
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Configure Gemini access

Create an API key in [Google AI Studio](https://aistudio.google.com/apikey). In the terminal where you will start ADK, set:

```bash
export GOOGLE_GENAI_USE_VERTEXAI=FALSE
export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
```

For PowerShell:

```powershell
$env:GOOGLE_GENAI_USE_VERTEXAI = "FALSE"
$env:GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY"
```

Alternatively, follow the [ADK Python quickstart](https://github.com/google/adk-docs/blob/main/docs/get-started/python.md) to configure a local `.env` file for each agent. `.env` files are ignored by Git. Keep real credentials out of source files and commits.

### 3. Check agent package entry files

Before running the invoice and research demos, ensure each agent folder contains an `__init__.py` with:

```python
from . import agent
```

The files should be located at:

- `invoice_demo/invoice_agent/__init__.py`
- `research_demo/researh_agent/__init__.py`

This follows the [ADK agent package convention](https://github.com/google/adk-python/blob/main/.agents/skills/adk-agent-builder/references/getting-started.md).

### 4. Confirm model access

The source currently configures these model IDs:

| Demo | Model |
| --- | --- |
| PDF analysis | `gemini-3.5-flash` |
| Web research | `gemini-3.5-flash` |
| Stock researcher and news analyst | `gemini-3.5-flash-lite` |
| Agentic RAG | `gemini-3.5-flash` (`RAG_MODEL`) |
| Enterprise RAG team | `gemini-3.5-flash` (`ENTERPRISE_RAG_MODEL`) |
| Software engineering team | `gemini-3.5-flash` (`SOFTWARE_DEMO_MODEL`) |

Model availability depends on your API access. If a configured model is unavailable, update its ID in the corresponding `agent.py` to a model supported by your account and tools. The invoice, research, and stock demos configure models directly in `agent.py`. The other demos support the environment-variable overrides listed above.

## Run a demo

Activate your environment and configure credentials first. Run each demo from its parent directory so ADK can discover the agent package.

| Demo | Directory command | Terminal chat command |
| --- | --- | --- |
| PDF analysis | `cd invoice_demo` | `adk run invoice_agent` |
| Web research | `cd research_demo` | `adk run researh_agent` |
| Stock research | `cd stock_demo` | `adk run stock_researcher` |
| Agentic RAG | `cd rag_demo` | `adk run knowledge_agent` |
| Enterprise RAG team | `cd enterprise_rag_demo` | `adk run solution_team` |
| Software engineering team | `cd software_engineering_demo` | `adk run dev_team` |

Each directory command above starts from the repository root. To use the browser interface, run `adk web` in the selected demo directory instead, then open the URL printed in the terminal and select the agent. See the [ADK quickstart](https://github.com/google/adk-docs/blob/main/docs/get-started/python.md) for the CLI and web interface.

### PDF and invoice analysis

Example prompts:

```text
Read /absolute/path/to/invoice.pdf and summarize the invoice details.
```

```text
Read /absolute/path/to/invoice.pdf and calculate the total, average,
minimum, and maximum of the line-item amounts. Exclude tax and subtotal rows.
```

The agent calls `read_pdf(file_path)` to extract text from all pages. The tool returns a status, page count, and text content, or an error message. When calculations are needed, the agent selects numbers from the extracted text and passes them to `calculate_stats(numbers)`.

The statistics tool returns the count, total, average, minimum, and maximum. Total and average are rounded to two decimal places. Use an absolute path to avoid confusion about the process's working directory.

### Web research

Example prompt:

```text
Research how AI agents use tools and summarize the main ideas with sources.
```

The research demo currently defines an agent and a search helper, but the helper is not connected to the agent. As a practical exercise, complete the instructions and integrate a supported search tool. See the stock demo’s `news_analyst` for an example using the built-in `google_search` tool.

### Stock research

Example prompts:

```text
Research NVDA: show its current snapshot, six-month performance,
and three recent news catalysts with dates and key risks.
```

```text
Give me an educational research brief on TCS.NS, including its
one-year price performance and recent company developments.
```

The main agent combines three tools:

1. `get_stock_snapshot(ticker)` retrieves the company name, currency, price, market capitalization, trailing P/E, and 52-week range when available.
2. `get_period_return(ticker, period="6mo")` calculates percentage change between the first and last returned historical closing prices. Documented periods include `1mo`, `3mo`, `6mo`, and `1y`.
3. `AgentTool(agent=news_analyst)` delegates news research to an agent with Google Search access.

The requested response format is **Snapshot, Performance, Catalysts, Risks**. Both stock agents share a Gemini configuration with up to five retry attempts for HTTP 429 and 503 responses, an initial delay of two seconds, and exponential backoff.

Use Yahoo Finance ticker symbols, such as `NVDA` or `TCS.NS`. Market data may be delayed or incomplete. Period performance uses the historical data returned by `yfinance`; it is not a separately implemented total-return calculation. The agent is instructed to avoid buy/sell advice and end with an educational disclaimer.

## Known limitations

- **PDF extraction is text-based.** There is no OCR pipeline for scanned invoices. Complex tables may lose their layout during extraction.
- **Number selection is model-driven.** The PDF tool does not parse invoice fields or distinguish line items from subtotals; the agent makes that selection before calculating statistics.
- **Local PDF contents enter the model context.** Use documents appropriate for your configured model service.
- **Web research is incomplete.** Connect a supported search tool before expecting web-grounded answers.
- **External services are required.** Gemini calls, search, and stock data depend on network access, service availability, access permissions, and quotas.
- **Results need review.** Missing financial fields can be returned as `None`, and a successful tool call does not guarantee a complete or accurate generated answer.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| `adk: command not found` | Activate `.venv` and install `google-adk` in that environment. |
| `ModuleNotFoundError` | Install the dependencies using the same Python environment that runs ADK. |
| Agent is missing from the web interface | Start `adk web` from the demo's parent directory and check the package's `__init__.py`. |
| Authentication or model error | Check your API key, model ID, account access, and selected Gemini backend. |
| Research returns a search error | Review the custom search wrapper against the installed ADK API. |
| PDF file not found | Supply an existing absolute path accessible to the running Python process. |
| PDF text is empty | Check whether the PDF is scanned or image-only; this demo does not perform OCR. |
| Stock data is missing | Check the ticker symbol, exchange suffix, network access, and data-provider response. |

## Run the offline tests

From the repository root:

```bash
python3 -m unittest discover -s rag_demo/tests -v
python3 -m unittest discover -s enterprise_rag_demo/tests -v
python3 -m unittest discover -s software_engineering_demo/tests -v
```

These tests run without Gemini credentials. The software engineering lab checks intentionally failing fixture tests and successful repair experiments; run its lab suite above to verify expected behavior.

## Practice exercises

- Add OCR or structured field extraction to the invoice demo.
- Connect a supported search tool to the research agent.
- Add documents to the RAG knowledge base and inspect the retrieved citations.
- Compare sequential and parallel specialist execution in the enterprise demo.
- Add regression cases to the software engineering lab and evaluate the repair candidates.

## References

- [Google ADK documentation](https://google.github.io/adk-docs/)
- [Google ADK Python source](https://github.com/google/adk-python)
- [Google Gen AI Python SDK](https://github.com/googleapis/python-genai)
- [pypdf documentation](https://pypdf.readthedocs.io/)
- [yfinance documentation](https://ranaroussi.github.io/yfinance/)
