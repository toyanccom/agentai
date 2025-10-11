from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence

from .config import AgentConfig
from .dispatcher import DistributionDispatcher
from .image import ImageGenerator
from .models import Article
from .platforms import (
    FacebookPlatform,
    InstagramPlatform,
    LinkedInPlatform,
    PinterestPlatform,
    TikTokPlatform,
    XComPlatform,
)
from .storage import JSONStateStore
from .wordpress import WordPressClient

logger = logging.getLogger(__name__)


class SocialMediaAgent:
    """Coordinates fetching articles and sharing them across networks."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.wordpress_client = WordPressClient(
            feed_url=config.wordpress.feed_url,
            max_items=config.wordpress.max_items,
        )
        self.state = JSONStateStore(config.state_file)
        self.image_generator = ImageGenerator(config.images)
        self.dispatcher = DistributionDispatcher(
            self._build_platforms(),
            self.state,
            dry_run=config.dry_run,
            image_generator=self.image_generator,
        )

    def _build_platforms(self) -> Sequence:
        return (
            XComPlatform(self.config.xcom),
            LinkedInPlatform(self.config.linkedin),
            FacebookPlatform(self.config.facebook),
            InstagramPlatform(self.config.instagram),
            PinterestPlatform(self.config.pinterest),
            TikTokPlatform(self.config.tiktok),
        )

    async def run_forever(self) -> None:
        interval = self.config.wordpress.poll_interval
        logger.info("Starting agent with polling interval %s seconds", interval)
        while True:
            await self.run_once()
            await asyncio.sleep(interval)

    async def run_once(self) -> None:
        articles = await self.wordpress_client.fetch()
        new_articles = [article for article in articles if not self.state.has_been_posted(article.identifier)]
        if not new_articles:
            logger.info("No new articles to share.")
            return
        # Sort by publish date ascending so older posts share first.
        new_articles.sort(key=lambda article: article.published)
        await self.dispatcher.distribute(new_articles)

    async def share_articles(self, articles: Sequence[Article]) -> None:
        await self.dispatcher.distribute(articles)
