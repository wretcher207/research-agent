# tools.py
# Defines the tools available to the agent.
# Each tool is a plain Python function + a schema dict the LLM uses to decide when to call it.

import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# ── Tavily client ──────────────────────────────────────────────────────────────
_tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))


def web_search(query: str) -> str:
    """
    Runs a web search and returns a formatted string of results.
    The agent calls this when it needs current or factual information.
    """
    print(f"\n  🔍 Searching: {query}")

    try:
        response = _tavily.search(
            query=query,
            search_depth="basic",   # "basic" = 1 credit, "advanced" = 2 credits
            max_results=5
        )

        results = response.get("results", [])

        if not results:
            return "No results found for that query."

        # Format results into a readable block the LLM can reason over
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"[{i}] {r['title']}\n"
                f"    URL: {r['url']}\n"
                f"    {r['content'][:300]}..."
            )

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Search error: {str(e)}"


# ── Tool registry ──────────────────────────────────────────────────────────────
# This is what gets passed to the LLM so it knows what tools exist.
# The LLM reads the "description" field to decide when to use each tool.

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information, news, facts, or any topic "
                "you don't already know with confidence. Use this whenever the user "
                "asks about recent events, specific facts, or anything that requires "
                "up-to-date information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up. Be specific and concise."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Map tool names to their actual Python functions
TOOL_FUNCTIONS = {
    "web_search": web_search
}