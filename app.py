import os
import sys
import traceback
from datetime import datetime

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import run_research_pipeline  # noqa: E402

st.set_page_config(page_title="ResearchIQ", page_icon="🧠", layout="wide")

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}

    .app-header {
        padding: 1.75rem 2rem;
        border-radius: 14px;
        background: linear-gradient(135deg, #4338CA 0%, #6D28D9 100%);
        margin-bottom: 1.5rem;
    }
    .app-header h1 {
        color: white;
        font-weight: 700;
        margin-bottom: 0.15rem;
        font-size: 1.9rem;
    }
    .app-header p {
        color: rgba(255,255,255,0.85);
        margin: 0;
        font-size: 0.95rem;
    }

    .pill {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .pill-ok { background: #DCFCE7; color: #166534; }
    .pill-bad { background: #FEE2E2; color: #991B1B; }

    div[data-testid="stMetric"] {
        background: rgba(127,127,127,0.06);
        border: 1px solid rgba(127,127,127,0.15);
        border-radius: 12px;
        padding: 0.9rem 1rem;
    }

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.4rem;
    }

    .stTextInput > div > div > input {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <h1>🧠 ResearchIQ</h1>
        <p>Multi-agent research pipeline — search, read, write, and self-critique.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""

EXAMPLE_TOPICS = [
    "Impact of AI on the IT industry",
    "Future of remote work",
    "Quantum computing in cybersecurity",
]

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Pipeline")
    st.caption("Search agent → Reader agent → Writer → Critic")

    tavily_ok = bool(os.getenv("TAVILY_API_KEY"))
    openrouter_ok = bool(os.getenv("OPENROUTER_API_KEY"))
    st.markdown(
        f"""
        <span class="pill {'pill-ok' if tavily_ok else 'pill-bad'}">TAVILY {'OK' if tavily_ok else 'MISSING'}</span>
        <span class="pill {'pill-ok' if openrouter_ok else 'pill-bad'}">OPENROUTER {'OK' if openrouter_ok else 'MISSING'}</span>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Keys are read from your `.env` file.")

    st.divider()
    st.subheader("History")
    if not st.session_state.history:
        st.caption("No runs yet this session.")
    else:
        for i, item in enumerate(st.session_state.history):
            if st.button(f"📄 {item['topic'][:28]}", key=f"hist_{i}", use_container_width=True):
                st.session_state.selected_index = i
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.session_state.selected_index = 0
            st.rerun()

if "selected_index" not in st.session_state:
    st.session_state.selected_index = 0

# ---------------------------------------------------------------------------
# Input card
# ---------------------------------------------------------------------------

def _set_topic(value):
    # Runs BEFORE the widget below is re-instantiated on the next run, so this is allowed.
    st.session_state.topic_input = value


with st.container(border=True):
    st.markdown("**Research topic**")
    topic = st.text_input(
        "Research topic",
        key="topic_input",
        placeholder="e.g. Impact of AI on healthcare diagnostics",
        label_visibility="collapsed",
    )

    cols = st.columns(len(EXAMPLE_TOPICS) + 1)
    for i, ex in enumerate(EXAMPLE_TOPICS):
        cols[i].button(ex, key=f"ex_{i}", use_container_width=True, on_click=_set_topic, args=(ex,))

    run = st.button("▶ Run Research Pipeline", type="primary", disabled=not topic.strip())

# ---------------------------------------------------------------------------
# Run pipeline with live step status
# ---------------------------------------------------------------------------
if run and topic.strip():
    try:
        with st.status("Starting pipeline...", expanded=True) as status:

            def on_step(step_name, message):
                status.update(label=step_name)
                status.write(message)

            result = run_research_pipeline(topic.strip(), on_step=on_step)
            status.update(label="Pipeline complete", state="complete")

        st.session_state.history.insert(
            0,
            {
                "topic": topic.strip(),
                "result": result,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            },
        )
        st.session_state.selected_index = 0
        st.rerun()
    except Exception as e:
        st.error(f"Pipeline failed: {e}")
        with st.expander("Error details"):
            st.code(traceback.format_exc())

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if st.session_state.history:
    idx = min(st.session_state.selected_index, len(st.session_state.history) - 1)
    current = st.session_state.history[idx]
    res = current["result"]

    st.markdown(f"### Results — {current['topic']}")
    st.caption(f"Run at {current['time']}")

    report_text = res.get("report", "") or ""
    sources = res.get("sources_found", []) or []

    m1, m2, m3 = st.columns(3)
    m1.metric("Report length", f"{len(report_text.split())} words")
    m2.metric("Sources found", len(sources))
    m3.metric("Status", "Complete" if "failed" not in report_text.lower() else "Check errors")

    tab_report, tab_critique, tab_search, tab_scraped = st.tabs(
        ["📄 Report", "🧪 Critique", "🔍 Search Results", "📚 Scraped Content"]
    )

    with tab_report:
        with st.container(border=True):
            st.markdown(report_text or "No report generated.")
        st.download_button(
            "⬇ Download report (.md)",
            data=report_text,
            file_name=f"report_{current['topic'][:30].replace(' ', '_')}.md",
            mime="text/markdown",
        )

    with tab_critique:
        with st.container(border=True):
            st.markdown(res.get("evaluation", "No evaluation generated."))

    with tab_search:
        with st.container(border=True):
            st.text(res.get("search_results", "No search results captured."))

    with tab_scraped:
        with st.container(border=True):
            if sources:
                st.caption("Scraped from: " + sources[0])
            st.text(res.get("scrapped_content", "No scraped content captured."))
else:
    st.info("Enter a topic above — or pick an example — and click **Run Research Pipeline**.")