from __future__ import annotations

import logging

import httpx

from ..config import TikTokSettings
from ..dispatcher import BasePlatform
from ..models import Article, GeneratedImage

logger = logging.getLogger(__name__)


class TikTokPlatform(BasePlatform):
    """Publishes promotional videos to TikTok via the Business API."""

    name = "tiktok"

    def __init__(self, settings: TikTokSettings) -> None:
        super().__init__(enabled=settings.enabled)
        self.settings = settings

    async def share(self, article: Article, *, image: GeneratedImage | None = None, dry_run: bool = False) -> None:
        if not self.enabled:
            return
        caption = self._truncate(f"{article.title} {article.url}", 2200)
        if dry_run:
            if image:
                logger.info(
                    "[DRY RUN][TikTok] %s | generated_image=%s",
                    caption,
                    image.remote_url or (image.file_path and str(image.file_path)) or "<binary>",
                )
            else:
                logger.info("[DRY RUN][TikTok] %s", caption)
            return
        if not self.settings.access_token or not self.settings.advertiser_id:
            logger.warning("TikTok integration requires access_token and advertiser_id.")
            return
        video_url = self.settings.extra.get("video_url") if self.settings.extra else None
        if not video_url:
            if image and image.remote_url:
                logger.warning(
                    "TikTok requires a video asset. Consider transforming the generated image at %s into a video and set video_url in configuration.",
                    image.remote_url,
                )
            elif image and image.has_local_file():
                logger.warning(
                    "TikTok requires a video asset. Convert the generated image at %s into a video and expose it via video_url.",
                    image.file_path,
                )
            else:
                logger.warning("TikTok post skipped because no video_url is configured in extra settings.")
            return
        headers = {
            "Authorization": f"Bearer {self.settings.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "advertiser_id": self.settings.advertiser_id,
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
            "text": caption,
        }
        async with httpx.AsyncClient(base_url=self.settings.api_base, timeout=30.0) as client:
            response = await client.post("/post/publish/content/", json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Shared article on TikTok: %s", article.title)
