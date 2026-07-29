import re

from src.agents.agents import build_reader_agent, build_search_agent, writer_chain, critic_chain


def _extract_text(content) -> str:
    """
    Normalize a LangChain message's .content into plain text.
    Some models (Gemini among them) return content as a list of content
    blocks (e.g. [{"type": "text", "text": "..."}]) instead of a plain
    string. Without this, the raw block structure gets displayed as-is.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "\n".join(p for p in parts if p)
    return str(content)


def _extract_sources(messages) -> list[dict]:
    """
    Pull title/URL pairs directly from the web_search tool's raw output
    in the message trace, rather than trusting whatever the agent's
    final synthesized answer happens to mention. This is the only place
    the "Title: ... / URL: ..." format the tool actually returns is
    still intact and reliably parseable.
    """
    sources = []
    seen = set()
    for msg in messages:
        msg_type = str(getattr(msg, "type", "") or msg.__class__.__name__).lower()
        if "tool" not in msg_type:
            continue
        text = _extract_text(getattr(msg, "content", ""))
        for match in re.finditer(r"Title:\s*(.*?)\s*\nURL:\s*(\S+)", text):
            title, url = match.group(1).strip(), match.group(2).strip()
            if url not in seen:
                seen.add(url)
                sources.append({"title": title or url, "url": url})
    return sources


def _noop(stage: str, status: str, detail: str = ""):
    pass


def research_pipeline(topic: str, on_step=None) -> dict:
    """
    Runs the 4-stage research pipeline: search -> read -> write -> critique.

    on_step: optional callback(stage: str, status: str, detail: str) called
    at the start and end of each stage. status is one of
    "running" | "done" | "error". Lets a caller (e.g. a Streamlit UI)
    render live progress without parsing stdout.
    """
    notify = on_step or _noop
    state = {}

    # ---- Step 1: Search agent ----
    print("\n" + "=" * 50)
    print("Step 1 - Search agent is working...")
    print("=" * 50)
    notify("search", "running")

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    state["search_results"] = _extract_text(search_result["messages"][-1].content)
    state["sources"] = _extract_sources(search_result["messages"])
    notify("search", "done", state["search_results"])
    print("\nSearch result:\n", state["search_results"])

    # ---- Step 2: Reader agent ----
    print("\n" + "=" * 50)
    print("Step 2 - Reader agent is scraping top resources...")
    print("=" * 50)
    notify("read", "running")

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [(
            "user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}"
        )]
    })
    state["scraped_content"] = _extract_text(reader_result["messages"][-1].content)
    notify("read", "done", state["scraped_content"])
    print("\nScraped content:\n", state["scraped_content"])

    # ---- Step 3: Writer chain ----
    print("\n" + "=" * 50)
    print("Step 3 - Writer is drafting the report...")
    print("=" * 50)
    notify("write", "running")

    research_combined = (
        f"SEARCH RESULT:\n{state['search_results']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}\n\n"
        f"CONFIRMED SOURCE URLS (use these, do not invent others):\n"
        + "\n".join(f"- {s['title']}: {s['url']}" for s in state["sources"])
    )
    state["report"] = writer_chain.invoke({"topic": topic, "research": research_combined})
    notify("write", "done", state["report"])
    print("\nFinal report:\n", state["report"])

    # ---- Step 4: Critic chain ----
    print("\n" + "=" * 50)
    print("Step 4 - Critic is reviewing the report...")
    print("=" * 50)
    notify("critique", "running")

    state["feedback"] = critic_chain.invoke({"report": state["report"]})
    notify("critique", "done", state["feedback"])
    print("\nCritic feedback:\n", state["feedback"])

    return state