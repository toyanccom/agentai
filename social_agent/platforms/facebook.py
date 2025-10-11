from __future__ import annotations

import logging

import httpx

from ..config import FacebookSettings
from ..dispatcher import BasePlatform
from ..models import Article, GeneratedImage

logger = logging.getLogger(__name__)


class FacebookPlatform(BasePlatform):
    """Posts links to a Facebook Page feed."""

    name = "facebook"

    def __init__(self, settings: FacebookSettings) -> None:
        super().__init__(enabled=settings.enabled)
        self.settings = settings

    async def share(self, article: Article, *, image: GeneratedImage | None = None, dry_run: bool = False) -> None:
        if not self.enabled:
            return
        message = f"{article.title}\n\n{self._truncate(article.summary, 400)}\n\n{article.url}"
        if dry_run:
            if image:
                logger.info(
                    "[DRY RUN][Facebook] %s | image=%s",
                    message,
                    image.remote_url or (image.file_path and str(image.file_path)) or "<binary>",
                )
            else:
                logger.info("[DRY RUN][Facebook] %s", message)
            return
        if not self.settings.access_token or not self.settings.page_id:
            logger.warning("Facebook integration requires access_token and page_id.")
            return
        params = {"access_token": self.settings.access_token}
        async with httpx.AsyncClient(base_url=self.settings.api_base, timeout=30.0) as client:
            if image and (image.remote_url or image.has_local_file()):
                endpoint = f"/{self.settings.page_id}/photos"
                data = {"caption": message}
                if image.remote_url:
                    data["url"] = image.remote_url
                    response = await client.post(endpoint, params=params, data=data)
                else:
                    path = image.file_path
                    assert path is not None
                    mime_type = "image/png"
                    if path.suffix.lower() in {".jpg", ".jpeg"}:
                        mime_type = "image/jpeg"
                    elif path.suffix.lower() == ".webp":
                        mime_type = "image/webp"
                    with path.open("rb") as file_handle:
                        files = {"source": (path.name, file_handle, mime_type)}
                        response = await client.post(endpoint, params=params, data=data, files=files)
                response.raise_for_status()
                logger.info("Shared article on Facebook with image: %s", article.title)
            else:
                endpoint = f"/{self.settings.page_id}/feed"
                data = {"message": message, "link": article.url}
                response = await client.post(endpoint, params=params, data=data)
                response.raise_for_status()
                logger.info("Shared article on Facebook: %s", article.title)
