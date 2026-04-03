"""Provider-agnostic web search using DuckDuckGo (free, no API key)."""

import json


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information.

    Args:
        query: The search query to look up
        max_results: Maximum number of results to return
    """
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        formatted = [
            {
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
                "url": r.get("href", ""),
            }
            for r in results
        ]
        return json.dumps(formatted, indent=2)

    except ImportError:
        return json.dumps(
            {
                "error": (
                    "Web search unavailable. "
                    "Install with: pip install duckduckgo-search"
                ),
                "query": query,
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e), "query": query})
