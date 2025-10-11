from __future__ import annotations

import logging

import httpx

from ..config import InstagramSettings
from ..dispatcher import BasePlatform
from ..models import Article, GeneratedImage

logger = logging.getLogger(__name__)


class InstagramPlatform(BasePlatform):
    """Creates a feed post on Instagram via the Graph API."""

    name = "instagram"

    def __init__(self, settings: InstagramSettings) -> None:
        super().__init__(enabled=settings.enabled)
        self.settings = settings

    async def share(self, article: Article, *, image: GeneratedImage | None = None, dry_run: bool = False) -> None:
        if not self.enabled:
            return
        caption = self._truncate(f"{article.title}\n{article.summary}\n{article.url}", 2200)
        if dry_run:
            if image:
                logger.info(
                    "[DRY RUN][Instagram] %s | image=%s",
                    caption,
                    image.remote_url or (image.file_path and str(image.file_path)) or "<binary>",
                )
            else:
                logger.info("[DRY RUN][Instagram] %s", caption)
            return
        token = self.settings.access_token
        ig_user_id = self.settings.ig_user_id
        if not token or not ig_user_id:
            logger.warning("Instagram integration requires access_token and ig_user_id.")
            return
        image_url = image.remote_url if image else None
        if not image_url and image and image.has_local_file():
            logger.warning(
                "Generated Instagram image stored at %s must be uploaded to a public URL before publishing.",
                image.file_path,
            )
        if not image_url:
            logger.warning("Instagram post skipped because no publicly accessible image URL is available.")
            return
        params = {
            "image_url": image_url,
            "caption": caption,
            "access_token": token,
        }
        async with httpx.AsyncClient(base_url=self.settings.api_base, timeout=30.0) as client:
            creation = await client.post(f"/{ig_user_id}/media", params=params)
            creation.raise_for_status()
            container_id = creation.json().get("id")
            if not container_id:
                logger.warning("Instagram did not return a media container id.")
                return
            publish_params = {"creation_id": container_id, "access_token": token}
            publish = await client.post(f"/{ig_user_id}/media_publish", params=publish_params)
            publish.raise_for_status()
            logger.info("Shared article on Instagram: %s", article.title)
