# tools.py
# Defines the tools available to the agent.
# Each tool is a plain Python function + a schema dict the LLM uses to decide when to call it.

import os
import html
import requests
from html.parser import HTMLParser
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


def read_url(url: str) -> str:
    """
    Fetches a webpage and returns its plain-text content (up to 8000 chars).
    Use this to read the full contents of a specific URL found via web_search.
    """
    print(f"\n  🌐 Reading: {url}")

    class _TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self._parts = []
            self._skip = False

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self._skip = True

        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self._skip = False

        def handle_data(self, data):
            if not self._skip:
                self._parts.append(data)

        def get_text(self):
            return " ".join(self._parts)

    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        parser = _TextExtractor()
        parser.feed(response.text)
        text = html.unescape(parser.get_text())

        # Collapse whitespace
        text = " ".join(text.split())

        return text[:8000]

    except Exception as e:
        return f"Error fetching URL: {e}"


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
    },
    {
        "type": "function",
        "function": {
            "name": "read_url",
            "description": (
                "Fetch and read the full text content of a specific webpage URL. "
                "Use this after web_search when you need more detail from a particular "
                "result, or when the user provides a URL they want you to read."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the page to fetch and read."
                    }
                },
                "required": ["url"]
            }
        }
    }
]

# Map tool names to their actual Python functions
TOOL_FUNCTIONS = {
    "web_search": web_search,
    "read_url": read_url
}