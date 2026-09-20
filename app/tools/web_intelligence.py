"""
Web Intelligence Tool
Web search and page content extraction using httpx and BeautifulSoup.
"""

import re
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from app.tools.base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the internet for up-to-date information, documentation, news, or answers. "
        "Returns titles, snippets, and source links."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search keywords or question."
            },
            "num_results": {
                "type": "integer",
                "description": "Maximum number of results to return (1-10). Default 5.",
                "default": 5
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        results = []
        try:
            # DuckDuckGo HTML search fallback (zero API token needed)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
                resp = await client.post(url, headers=headers)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.select(".result")
                    for item in links[:num_results]:
                        title_el = item.select_one(".result__title a")
                        snippet_el = item.select_one(".result__snippet")
                        url_el = item.select_one(".result__url")
                        
                        if title_el:
                            title = title_el.get_text(strip=True)
                            raw_href = title_el.get("href", "")
                            # extract actual url from DDG redirect
                            match = re.search(r"uddg=([^&]+)", raw_href)
                            actual_url = urllib.parse.unquote(match.group(1)) if match else raw_href
                            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                            results.append({
                                "title": title,
                                "url": actual_url,
                                "snippet": snippet
                            })

            if not results:
                # Secondary fallback: Wikipedia API for informative queries
                async with httpx.AsyncClient(timeout=10.0) as client:
                    wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote_plus(query)}&limit={num_results}&namespace=0&format=json"
                    wiki_resp = await client.get(wiki_url)
                    if wiki_resp.status_code == 200:
                        data = wiki_resp.json()
                        titles, descriptions, urls = data[1], data[2], data[3]
                        for t, d, u in zip(titles, descriptions, urls):
                            results.append({"title": t, "snippet": d, "url": u})

            if results:
                formatted = []
                for idx, r in enumerate(results, 1):
                    formatted.append(f"[{idx}] {r['title']}\n    URL: {r['url']}\n    Snippet: {r['snippet']}")
                return ToolResult(
                    success=True,
                    output="\n\n".join(formatted),
                    metadata={"count": len(results), "results": results}
                )
            else:
                return ToolResult(
                    success=True,
                    output=f"No results found for query: '{query}'",
                    metadata={"count": 0}
                )

        except Exception as e:
            return ToolResult(success=False, output="", error=f"Search failed: {str(e)}")


class FetchPageTool(BaseTool):
    name: str = "fetch_page"
    description: str = (
        "Fetch and read full content from a web page URL. Parses HTML and returns clean markdown text."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch."
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum character length of content to extract (default 4000).",
                "default": 4000
            }
        },
        "required": ["url"]
    }

    async def execute(self, url: str, max_length: int = 4000, **kwargs) -> ToolResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return ToolResult(success=False, output="", error=f"HTTP {resp.status_code} fetching {url}")

                soup = BeautifulSoup(resp.text, "html.parser")
                # Remove unwanted tags
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
                    tag.decompose()

                title = soup.title.get_text(strip=True) if soup.title else ""
                text = soup.get_text(separator="\n", strip=True)
                # Clean up excess newlines
                cleaned = re.sub(r"\n{3,}", "\n\n", text)
                truncated = cleaned[:max_length]
                if len(cleaned) > max_length:
                    truncated += f"\n... [Content truncated at {max_length} characters]"

                return ToolResult(
                    success=True,
                    output=f"# {title}\nURL: {url}\n\n{truncated}",
                    metadata={"url": url, "length": len(truncated), "title": title}
                )

        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to fetch {url}: {str(e)}")
