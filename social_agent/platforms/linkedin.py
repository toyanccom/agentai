from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from ..config import LinkedInSettings
from ..dispatcher import BasePlatform
from ..models import Article, GeneratedImage

logger = logging.getLogger(__name__)


class LinkedInPlatform(BasePlatform):
    """Publishes articles to LinkedIn using the UGC API."""

    name = "linkedin"

    def __init__(self, settings: LinkedInSettings) -> None:
        super().__init__(enabled=settings.enabled)
        self.settings = settings

    async def share(self, article: Article, *, image: GeneratedImage | None = None, dry_run: bool = False) -> None:
        if not self.enabled:
            return
        if dry_run:
            if image:
                logger.info(
                    "[DRY RUN][LinkedIn] %s | image=%s",
                    article.url,
                    image.remote_url or (image.file_path and str(image.file_path)) or "<binary>",
                )
            else:
                logger.info("[DRY RUN][LinkedIn] %s", article.url)
            return
        if not self.settings.access_token or not self.settings.organization_urn:
            logger.warning("LinkedIn integration missing access token or organization URN.")
            return
        headers = {
            "Authorization": f"Bearer {self.settings.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        media_entry: dict[str, object] = {
            "status": "READY",
            "originalUrl": article.url,
            "title": {"text": article.title},
        }
        if image and image.remote_url:
            media_entry["thumbnails"] = [{"resolvedUrl": image.remote_url}]
        payload = {
            "author": self.settings.organization_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": f"{article.title}\n{article.summary}"[:1300]},
                    "shareMediaCategory": "ARTICLE",
                    "media": [media_entry],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            "created": {
                "time": int(datetime.now(tz=timezone.utc).timestamp() * 1000),
            },
        }
        if image and image.remote_url is None and image.has_local_file():
            logger.warning("LinkedIn requires a hosted image URL; generated file %s must be uploaded separately.", image.file_path)
        async with httpx.AsyncClient(base_url=self.settings.api_base, timeout=30.0) as client:
            response = await client.post("/ugcPosts", json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Shared article on LinkedIn: %s", article.title)
