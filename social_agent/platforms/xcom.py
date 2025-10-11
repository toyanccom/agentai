from __future__ import annotations

import logging

import httpx

from ..config import XComSettings
from ..dispatcher import BasePlatform
from ..models import Article, GeneratedImage

logger = logging.getLogger(__name__)


class XComPlatform(BasePlatform):
    """Posts updates to X (formerly Twitter)."""

    name = "x.com"

    def __init__(self, settings: XComSettings) -> None:
        super().__init__(enabled=settings.enabled)
        self.settings = settings

    async def share(self, article: Article, *, image: GeneratedImage | None = None, dry_run: bool = False) -> None:
        if not self.enabled:
            return
        message = self._truncate(f"{article.title} {article.url}", 280)
        if dry_run:
            if image:
                logger.info(
                    "[DRY RUN][X] %s | image=%s",
                    message,
                    image.remote_url or (image.file_path and str(image.file_path)) or "<binary>",
                )
            else:
                logger.info("[DRY RUN][X] %s", message)
            return
        if not self.settings.access_token:
            logger.warning("X integration is enabled but no access token is configured.")
            return
        headers = {
            "Authorization": f"Bearer {self.settings.access_token}",
            "Content-Type": "application/json",
        }
        payload = {"text": message}
        async with httpx.AsyncClient(base_url=self.settings.api_base, timeout=30.0) as client:
            response = await client.post("/tweets", json=payload, headers=headers)
            response.raise_for_status()
            if image:
                logger.warning(
                    "X image upload is not yet automated. Generated image located at %s should be uploaded via media API.",
                    image.remote_url or image.file_path,
                )
            logger.info("Shared article on X: %s", article.title)
