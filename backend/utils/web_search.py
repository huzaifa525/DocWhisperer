from duckduckgo_search import DDGS
from typing import List
import logging

logger = logging.getLogger(__name__)

class WebSearchTool:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 3) -> List[str]:
        try:
            results = []
            for r in self.ddgs.text(query, max_results=max_results):
                results.append(f"Title: {r['title']}\nContent: {r['body']}")
            return results
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []