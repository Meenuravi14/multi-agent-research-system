import re

from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

URL_PATTERN = re.compile(r'https?://[^\s\)\]"\']+')


def extract_urls(text: str, limit: int = 3) -> list:
    """Pull URLs out of raw search-result text with regex, instead of asking an LLM to find them."""
    seen = []
    for match in URL_PATTERN.findall(text or ""):
        cleaned = match.rstrip(".,;:")
        if cleaned not in seen:
            seen.append(cleaned)
        if len(seen) >= limit:
            break
    return seen


def run_research_pipeline(topic: str, on_step=None) -> dict:
    """
    Runs the search -> scrape -> write -> critique pipeline.

    on_step: optional callback(step_name: str, message: str), called right before each
    stage starts. Used by the Streamlit UI to show live progress.
    """

    def report(step, message):
        print(f"\n{'=' * 50}\n{step}\n{'=' * 50}")
        if on_step:
            on_step(step, message)

    state = {}

    # Step 1 - Search
    report("Step 1 - Searching the web", "Running the search agent...")
    try:
        search_agent = build_search_agent()
        search_result = search_agent.invoke(
            {"messages": [("user", f"find recent, reliable and detailed information about: {topic}")]},
            config={"recursion_limit": 10},
        )
        state["search_results"] = search_result["messages"][-1].content
    except Exception as e:
        state["search_results"] = f"[Search failed: {e}]"
    print("\nSearch result:", state["search_results"])

    # Step 2 - Scrape (URL picked by regex, not by the LLM)
    report("Step 2 - Reading top sources", "Extracting URLs and scraping the most relevant page...")
    urls = extract_urls(state["search_results"])
    state["sources_found"] = urls
    if not urls:
        state["scrapped_content"] = "No URLs were found in the search results to scrape."
    else:
        try:
            reader_agent = build_reader_agent()
            target_url = urls[0]
            reader_result = reader_agent.invoke(
                {
                    "messages": [
                        (
                            "user",
                            f"Scrape this URL and summarize the key content relevant to '{topic}': {target_url}",
                        )
                    ]
                },
                config={"recursion_limit": 10},
            )
            state["scrapped_content"] = reader_result["messages"][-1].content
        except Exception as e:
            state["scrapped_content"] = f"[Scraping failed: {e}]"
    print("\nScraped content:", state["scrapped_content"])

    # Step 3 - Write
    report("Step 3 - Drafting the report", "Writing the structured research report...")
    combined_research = (
        f"SEARCH RESULTS: {state['search_results']}\n"
        f"SCRAPED CONTENT: {state['scrapped_content']}\n"
    )
    try:
        state["report"] = writer_chain.invoke({"topic": topic, "research": combined_research})
    except Exception as e:
        state["report"] = f"[Report generation failed: {e}]"
    print("\nFinal report:\n", state["report"])

    # Step 4 - Critique
    report("Step 4 - Evaluating the report", "Running the critic chain...")
    try:
        state["evaluation"] = critic_chain.invoke({"report": state["report"]})
    except Exception as e:
        state["evaluation"] = f"[Evaluation failed: {e}]"
    print("\nCritic report:\n", state["evaluation"])

    return state


if __name__ == "__main__":
    topic = input("\nEnter the Research topic: ")
    run_research_pipeline(topic)