from __future__ import annotations

import asyncio
from typing import Iterable

import feedparser

from .models import Article


class WordPressClient:
    """Fetches articles from a WordPress feed."""

    def __init__(self, feed_url: str, max_items: int = 10) -> None:
        self.feed_url = feed_url
        self.max_items = max_items

    async def fetch(self) -> list[Article]:
        """Fetch and parse the feed returning Article objects."""

        return await asyncio.to_thread(self._parse_feed)

    def _parse_feed(self) -> list[Article]:
        parsed = feedparser.parse(self.feed_url)
        entries: Iterable[dict] = parsed.get("entries", [])[: self.max_items]
        return [Article.from_feed_entry(entry) for entry in entries]
