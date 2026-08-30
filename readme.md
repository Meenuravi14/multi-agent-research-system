# 🧠 ResearchIQ — Multi-Agent Research Assistant

A multi-agent research pipeline that searches the web, reads the most relevant source, drafts a structured report, and critiques its own output — with a Streamlit UI on top.

Built as a hands-on exploration of agentic AI systems: tool-calling agents, prompt chaining, and self-evaluation, using LangChain / LangGraph.

---

## Architecture

The pipeline runs four stages in sequence:

```
   ┌───────────────┐     ┌────────────────┐     ┌────────────┐     ┌────────────┐
   │  Search Agent │ --> │  Reader Agent  │ --> │   Writer   │ --> │   Critic   │
   │  (Tavily API) │     │ (BeautifulSoup)│     │   Chain    │     │   Chain    │
   └───────────────┘     └────────────────┘     └────────────┘     └────────────┘
     finds sources          reads + summarizes     drafts report      scores + reviews
```

1. **Search Agent** — a tool-calling LangGraph agent that queries the Tavily API for recent, relevant sources on the topic.
2. **Reader Agent** — receives a *pre-validated* URL (see design notes below) and summarizes its scraped content.
3. **Writer Chain** — an LLM prompt chain that drafts a structured report (Introduction, Key Findings, Conclusion, Sources) from the combined research.
4. **Critic Chain** — reviews the report and returns a score, strengths, areas to improve, and a one-line verdict.

This maps to two patterns from Anthropic's "Building Effective Agents": the overall flow is a **prompt chain**, and the writer→critic step is a small **evaluator-optimizer** loop.

---

## Features

- Web search via the Tavily API
- Automatic multi-URL scraping fallback — tries several candidate sources until one yields real content, instead of trusting the first result
- Structured, sectioned report generation
- Automated self-critique with a numeric score and specific feedback
- Streamlit UI with live per-step progress, run history, source/word-count metrics, and a Markdown download of the final report
- Runs equally well from the command line or the UI

---

## Tech Stack

| Layer | Tool |
|---|---|
| Agent framework | LangChain + LangGraph (`create_agent`) |
| LLM provider | OpenRouter (`ChatOpenRouter`) |
| Web search | Tavily API |
| Scraping | `requests` + BeautifulSoup |
| UI | Streamlit |
| Config | `python-dotenv` |

---

## Design Decisions & Trade-offs

Documenting the reasoning, not just the code — these were deliberate calls, each with a known limitation:

- **Regex URL extraction instead of LLM-picked URLs.** Early versions asked the reader agent to *find* a URL inside raw search text itself; smaller/free models frequently failed at this and asked the user for a link instead of acting. URLs are now extracted with a regex in plain Python — deterministic and free-model-friendly — and the agent is only asked to summarize content it's already been handed.
- **Multi-URL fallback for scraping.** A single scrape attempt is unreliable (dead links, bot blocks, thin pages). The pipeline now tries up to 5 candidate URLs in order and keeps the first one that returns at least 200 characters of real text, rather than failing on the first bad source.
- **`requests` + BeautifulSoup over a headless browser.** This can't render JavaScript-heavy pages (SPAs, some paywalled news sites), so those sources will fail to scrape. A headless browser (Playwright) would fix this but adds significant weight and slowdown; the trade-off was made deliberately in favor of simplicity, with graceful fallback rather than a hard crash when a source can't be read.
- **Free-tier OpenRouter models.** Chosen for cost, with the accepted trade-off of variable latency and occasionally weaker tool-calling reliability (mitigated with explicit system prompts and a raised `recursion_limit`).
- **`recursion_limit` on agent calls.** LangGraph's default step budget can be exhausted by an indecisive model looping on tool calls; this is set explicitly (with room for a few retries) rather than left uncapped, so failures surface quickly instead of hanging.

---

## Project Structure

```
Multi Agent System/
├── agents.py          # LLM setup + agent/chain builders (search, reader, writer, critic)
├── tool.py            # web_search and scrape_url tool definitions
├── pipeline.py         # Orchestrates the 4-stage pipeline end-to-end
├── streamlit_app.py    # Streamlit UI
├── requirements.txt
└── .env                # API keys (not committed)
```

---

## Setup & Installation

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd "Multi Agent System"

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API keys
echo "TAVILY_API_KEY=your_key_here" >> .env
echo "OPENROUTER_API_KEY=your_key_here" >> .env
```

You'll need free API keys from [Tavily](https://tavily.com) and [OpenRouter](https://openrouter.ai).

---

## Usage

**Command line:**
```bash
python pipeline.py
```

**Streamlit UI:**
```bash
streamlit run streamlit_app.py
```

---

## Known Limitations

- Cannot scrape JavaScript-rendered pages (SPAs, some paywalled sites) — falls back to the next candidate URL, but if all sources are JS-rendered the scrape step will report no usable content.
- Free-tier LLM responses can be slow or occasionally rate-limited.
- Only one source is deeply read per run; the report otherwise relies on search snippets.

## Possible Future Improvements

- Swap in Playwright for JS-rendered pages
- Add a RAG layer (vector store) for multi-document synthesis instead of single-source reading
- LangSmith tracing and a small eval suite for regression-testing agent behavior
- Summarize and cite multiple scraped sources instead of one