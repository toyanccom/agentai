from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Sequence

from .models import Article, GeneratedImage
from .storage import JSONStateStore

logger = logging.getLogger(__name__)


if TYPE_CHECKING:  # pragma: no cover
    from .image import ImageGenerator


class DistributionDispatcher:
    """Dispatches articles to configured social media platform clients."""

    def __init__(
        self,
        platforms: Sequence["BasePlatform"],
        state: JSONStateStore,
        dry_run: bool = False,
        image_generator: "ImageGenerator" | None = None,
    ) -> None:
        self.platforms = platforms
        self.state = state
        self.dry_run = dry_run
        self.image_generator = image_generator

    async def distribute(self, articles: Iterable[Article]) -> None:
        """Send articles to each configured platform."""

        for article in articles:
            if self.state.has_been_posted(article.identifier):
                logger.debug("Skipping %s because it is already posted", article.identifier)
                continue
            await self._share_article(article)
            self.state.mark_posted([article.identifier])
        self.state.save()

    async def _share_article(self, article: Article) -> None:
        image: GeneratedImage | None = None
        if self.image_generator:
            try:
                image = await self.image_generator.generate_for_article(article)
                if image:
                    logger.debug("Generated image for %s using prompt: %s", article.title, image.prompt)
            except Exception:  # pragma: no cover - unexpected provider failure
                logger.exception("Image generation failed for article '%s'", article.title)
        tasks = [
            platform.share(article, image=image, dry_run=self.dry_run)
            for platform in self.platforms
            if platform.enabled
        ]
        if not tasks:
            logger.info("No platforms enabled, skipping article: %s", article.title)
            return
        await asyncio.gather(*tasks, return_exceptions=False)


class BasePlatform:
    """Base class for all social platform implementations."""

    name: str = "base"

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    async def share(
        self,
        article: Article,
        *,
        image: GeneratedImage | None = None,
        dry_run: bool = False,
    ) -> None:  # pragma: no cover - to be implemented
        raise NotImplementedError

    def _truncate(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + "…"
