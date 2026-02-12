"""Web search and real-time data tools for Mimi.

Uses DuckDuckGo (free, no API key) for web search, news, and answers.
Includes dedicated Reddit and X/Twitter search tools.
"""

import httpx
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


# ---------------------------------------------------------------------------
# Reddit search (free JSON API + DuckDuckGo fallback)
# ---------------------------------------------------------------------------

def reddit_search(query, subreddit=None, sort="relevance", max_results=8):
    """Search Reddit for posts. Optionally filter by subreddit. Returns titles, URLs, scores, and comments."""
    try:
        # Try Reddit's free JSON API first
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {"q": query, "sort": sort, "limit": max_results, "restrict_sr": "on"}
        else:
            url = "https://www.reddit.com/search.json"
            params = {"q": query, "sort": sort, "limit": max_results}

        resp = httpx.get(url, params=params, headers={"User-Agent": "MimiBot/1.0"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        posts = []
        for child in data.get("data", {}).get("children", []):
            p = child.get("data", {})
            posts.append({
                "title": p.get("title", ""),
                "subreddit": p.get("subreddit_name_prefixed", ""),
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "score": p.get("score", 0),
                "comments": p.get("num_comments", 0),
                "selftext": (p.get("selftext", "") or "")[:300],
                "created": p.get("created_utc", 0),
            })

        if posts:
            return posts
    except Exception:
        pass

    # Fallback: DuckDuckGo site search
    try:
        site_query = f"site:reddit.com {query}"
        if subreddit:
            site_query = f"site:reddit.com/r/{subreddit} {query}"
        results = DDGS().text(site_query, max_results=max_results)
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in (results or [])
        ] or "No Reddit results found."
    except Exception as e:
        return f"Reddit search error: {e}"


def reddit_read_thread(url, max_comments=10):
    """Read a Reddit thread's top comments. Pass a full Reddit URL."""
    try:
        # Normalize URL to JSON endpoint
        clean = url.rstrip("/")
        if not clean.endswith(".json"):
            clean += ".json"

        resp = httpx.get(clean, headers={"User-Agent": "MimiBot/1.0"}, params={"limit": max_comments}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # First item is the post, second is comments
        post_data = data[0]["data"]["children"][0]["data"]
        result = {
            "title": post_data.get("title", ""),
            "selftext": (post_data.get("selftext", "") or "")[:1000],
            "score": post_data.get("score", 0),
            "subreddit": post_data.get("subreddit_name_prefixed", ""),
            "comments": [],
        }

        for child in data[1]["data"]["children"][:max_comments]:
            c = child.get("data", {})
            if c.get("body"):
                result["comments"].append({
                    "author": c.get("author", "[deleted]"),
                    "score": c.get("score", 0),
                    "body": c["body"][:500],
                })

        return result
    except Exception as e:
        return f"Error reading thread: {e}"


# ---------------------------------------------------------------------------
# X/Twitter search (via DuckDuckGo — X API is $100/mo)
# ---------------------------------------------------------------------------

def x_search(query, max_results=8):
    """Search X (Twitter) for recent posts and discussions."""
    try:
        results = DDGS().text(f"site:x.com {query}", max_results=max_results)
        if not results:
            # Try twitter.com as fallback (some results still indexed under old domain)
            results = DDGS().text(f"site:twitter.com {query}", max_results=max_results)
        if not results:
            return "No X/Twitter results found."
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in results
        ]
    except Exception as e:
        return f"X search error: {e}"


def x_news(query, max_results=5):
    """Search for news articles about X/Twitter discussions on a topic."""
    try:
        results = DDGS().news(f"{query} twitter OR x.com", max_results=max_results)
        if not results:
            return "No X-related news found."
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
        return f"X news search error: {e}"
