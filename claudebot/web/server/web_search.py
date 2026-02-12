"""Web search and real-time data tools for Mimi.

Uses DuckDuckGo (free, no API key) for web search, news, and answers.
Can be upgraded to Tavily/SerpAPI later for better results.
"""

from ddgs import DDGS


def web_search(query, max_results=5):
    """Search the web and return results with titles, URLs, and snippets."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as e:
        return f"Search error: {e}"


def web_news(query, max_results=5):
    """Search for recent news articles."""
    try:
        results = DDGS().news(query, max_results=max_results)
        if not results:
            return "No news found."
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "source": r.get("source", ""),
                "date": r.get("date", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except Exception as e:
        return f"News search error: {e}"


def web_answers(query):
    """Get instant answers (like stock prices, weather, definitions)."""
    try:
        results = DDGS().answers(query)
        if not results:
            return "No instant answer available."
        return [
            {
                "text": r.get("text", ""),
                "url": r.get("url", ""),
            }
            for r in results
        ]
    except Exception as e:
        return f"Answers error: {e}"
