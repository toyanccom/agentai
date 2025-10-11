from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


class JSONStateStore:
    """Persist article identifiers to avoid double posting."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.posted_ids: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            raw = {}
        posted = raw.get("posted_ids", []) if isinstance(raw, dict) else []
        self.posted_ids = {str(item) for item in posted}

    def mark_posted(self, article_ids: Iterable[str]) -> None:
        self.posted_ids.update(article_ids)

    def has_been_posted(self, article_id: str) -> bool:
        return article_id in self.posted_ids

    def save(self) -> None:
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"posted_ids": sorted(self.posted_ids)}, indent=2, ensure_ascii=False))
