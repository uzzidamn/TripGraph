"""
Web search for live travel data enrichment.
Primary:  Anthropic built-in web_search_20250305 (uses existing ANTHROPIC_API_KEY).
Fallback: DuckDuckGo (duckduckgo-search package, no API key needed).
"""
import os


def web_search(query: str) -> str:
    """Return a text summary of top web results, or '' if all backends fail.

    Uses DuckDuckGo (no API key, no rate limits) as primary.
    Anthropic built-in search is kept as fallback but is NOT called by default
    to avoid consuming the shared Claude token budget before the planning step.
    """
    result = _ddg_search(query)
    if result:
        return result
    return _anthropic_search(query)


# ---------------------------------------------------------------------------
# Backend 1 – Anthropic built-in web search
# ---------------------------------------------------------------------------

def _anthropic_search(query: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ""
    try:
        import anthropic  # already installed (llm_client uses it)

        client = anthropic.Anthropic(api_key=api_key)
        model = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")

        messages = [
            {
                "role": "user",
                "content": (
                    f"Search for: {query}. "
                    "Summarise hotel names and prices, activities and costs, "
                    "transport options and travel times, and any current weather or events."
                ),
            }
        ]

        # Tool-use loop: Anthropic executes the search server-side;
        # we send empty tool_result to acknowledge each tool_use block.
        for _ in range(6):
            response = client.messages.create(
                model=model,
                max_tokens=1500,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=messages,
                extra_headers={"anthropic-beta": "web-search-2025-03-05"},
            )

            texts, tool_uses = [], []
            for block in response.content:
                btype = getattr(block, "type", None)
                if btype == "text":
                    texts.append(block.text)
                elif btype == "tool_use":
                    tool_uses.append(block)

            if response.stop_reason == "end_turn" or not tool_uses:
                return "\n".join(texts)

            # Acknowledge tool calls so the model can continue
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": t.id, "content": ""}
                    for t in tool_uses
                ],
            })

        return ""

    except Exception as e:
        print(f"  ⚠️  Anthropic web search failed ({type(e).__name__}: {e})")
        return ""


# ---------------------------------------------------------------------------
# Backend 2 – DuckDuckGo (no API key)
# ---------------------------------------------------------------------------

def _ddg_search(query: str) -> str:
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return ""

        parts = []
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            if title or body:
                parts.append(f"{title}: {body}")
        return "\n\n".join(parts)

    except Exception as e:
        print(f"  ⚠️  DuckDuckGo search failed ({type(e).__name__}: {e})")
        return ""
