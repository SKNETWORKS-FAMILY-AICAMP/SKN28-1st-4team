# pyright: reportMissingImports=false

import json
from typing import Annotated

from agents import function_tool
from duckduckgo_search import DDGS


@function_tool(name_override="web_search")
def web_search(
    query: Annotated[str, "Search query for vehicle history, catalog, newsroom, or specs"],
    max_results: Annotated[int, "Maximum number of results to return"] = 5,
) -> str:
    """Search the public web and return a compact JSON array of results."""
    results: list[dict[str, str | None]] = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": item.get("title"),
                    "url": item.get("href"),
                    "snippet": item.get("body"),
                }
            )
    return json.dumps(results, ensure_ascii=False)
