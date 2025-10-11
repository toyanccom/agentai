from __future__ import annotations

import logging

import httpx

from ..config import PinterestSettings
from ..dispatcher import BasePlatform
from ..models import Article, GeneratedImage

logger = logging.getLogger(__name__)


class PinterestPlatform(BasePlatform):
    """Creates a new Pin linking to the article."""

    name = "pinterest"

    def __init__(self, settings: PinterestSettings) -> None:
        super().__init__(enabled=settings.enabled)
        self.settings = settings

    async def share(self, article: Article, *, image: GeneratedImage | None = None, dry_run: bool = False) -> None:
        if not self.enabled:
            return
        description = self._truncate(article.summary, 500)
        if dry_run:
            if image:
                logger.info(
                    "[DRY RUN][Pinterest] %s | image=%s",
                    article.url,
                    image.remote_url or (image.file_path and str(image.file_path)) or "<binary>",
                )
            else:
                logger.info("[DRY RUN][Pinterest] %s", article.url)
            return
        if not self.settings.access_token or not self.settings.board_id:
            logger.warning("Pinterest integration requires access_token and board_id.")
            return
        image_url = image.remote_url if image else None
        if not image_url and image and image.has_local_file():
            logger.warning(
                "Generated Pinterest image stored at %s must be uploaded to a public URL before publishing.",
                image.file_path,
            )
        if not image_url:
            logger.warning("Pinterest post skipped because no publicly accessible image URL is available.")
            return
        payload = {
            "title": self._truncate(article.title, 100),
            "link": article.url,
            "board_id": self.settings.board_id,
            "description": description,
            "media_source": {
                "source_type": "image_url",
                "url": image_url,
            },
        }
        headers = {
            "Authorization": f"Bearer {self.settings.access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(base_url=self.settings.api_base, timeout=30.0) as client:
            response = await client.post("/pins", json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Shared article on Pinterest: %s", article.title)
