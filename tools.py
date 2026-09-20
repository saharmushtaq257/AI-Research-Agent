"""Free tools for the research agent — no API keys needed.

1. web_search  -> DuckDuckGo search (package: ddgs)
2. read_page   -> fetches a URL and returns readable text

NOTE: the old package was called `duckduckgo-search` and you imported it with
`from duckduckgo_search import DDGS`. It was renamed to `ddgs`. If you copy code
from an older tutorial, that import will fail.
"""

import time
from typing import Type

import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from ddgs import DDGS
from pydantic import BaseModel, Field

# DuckDuckGo rate-limits aggressively, especially from cloud IPs like
# Streamlit Cloud. These retries are what keep the app usable there.
MAX_RETRIES = 3
RETRY_WAIT = 4  # seconds


# --------------------------------------------------------------------------
# Tool 1: web search
# --------------------------------------------------------------------------
class SearchInput(BaseModel):
    query: str = Field(..., description="The search query. Keep it short, 3-8 words.")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web via DuckDuckGo. Input is a short search query. "
        "Returns a numbered list of results, each with a title, URL and snippet. "
        "Snippets are short — use read_page on a URL to get the full text."
    )
    args_schema: Type[BaseModel] = SearchInput
    max_results: int = 6

    def _run(self, query: str) -> str:
        last_error = ""
        for attempt in range(MAX_RETRIES):
            try:
                # max_results is keyword-only in ddgs 9.x — positional will error.
                results = DDGS().text(query, max_results=self.max_results)
                if not results:
                    last_error = "no results"
                    time.sleep(RETRY_WAIT)
                    continue

                lines = []
                for i, r in enumerate(results, 1):
                    # Field names vary between ddgs versions — always use .get()
                    title = r.get("title", "Untitled")
                    url = r.get("href", "")
                    body = r.get("body", "")
                    lines.append(f"{i}. {title}\n   URL: {url}\n   {body}")
                return "\n\n".join(lines)

            except Exception as e:  # rate limit, timeout, network blip
                last_error = str(e)
                time.sleep(RETRY_WAIT * (attempt + 1))  # back off

        return (
            f"Search failed for '{query}' after {MAX_RETRIES} tries ({last_error}). "
            "Try a different wording, or answer from what you already found."
        )


# --------------------------------------------------------------------------
# Tool 2: read a page
# --------------------------------------------------------------------------
class ReadPageInput(BaseModel):
    url: str = Field(..., description="Full URL starting with http:// or https://")


class ReadPageTool(BaseTool):
    name: str = "read_page"
    description: str = (
        "Fetch a web page and return its main text. Use this on the 2-4 most "
        "promising URLs from web_search to get real detail instead of snippets."
    )
    args_schema: Type[BaseModel] = ReadPageInput
    char_limit: int = 5000  # keep the LLM context small so Groq stays fast

    def _run(self, url: str) -> str:
        try:
            resp = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/1.0)"},
            )
            resp.raise_for_status()
        except Exception as e:
            return f"Could not fetch {url}: {e}. Skip it and use another source."

        soup = BeautifulSoup(resp.text, "html.parser")
        for junk in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            junk.decompose()

        text = " ".join(soup.get_text(separator=" ").split())
        if not text:
            return f"{url} had no readable text (maybe JavaScript-only). Skip it."

        if len(text) > self.char_limit:
            text = text[: self.char_limit] + "... [truncated]"
        return f"Content of {url}:\n\n{text}"
