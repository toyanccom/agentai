from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class Article:
    """Represents a WordPress article fetched from the feed."""

    identifier: str
    title: str
    url: str
    summary: str
    published: datetime
    categories: list[str] = field(default_factory=list)

    @classmethod
    def from_feed_entry(cls, entry: dict) -> "Article":
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if published_parsed is None:
            published = datetime.now(tz=timezone.utc)
        else:
            published = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        categories: Iterable[str] = []
        if "tags" in entry and entry["tags"]:
            categories = [tag.get("term", "") for tag in entry["tags"] if tag.get("term")]
        return cls(
            identifier=str(entry.get("id") or entry.get("guid") or entry.get("link")),
            title=entry.get("title", "Untitled"),
            url=entry.get("link", ""),
            summary=entry.get("summary", ""),
            published=published,
            categories=list(categories),
        )


@dataclass(slots=True)
class GeneratedImage:
    """Represents an AI generated illustration to share with an article."""

    prompt: str
    alt_text: str
    file_path: Path | None = None
    remote_url: str | None = None

    def has_local_file(self) -> bool:
        return self.file_path is not None and self.file_path.exists()
