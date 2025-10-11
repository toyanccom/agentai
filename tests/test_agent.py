from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from social_agent.agent import SocialMediaAgent
from social_agent.config import AgentConfig, ImageServiceSettings, WordPressConfig
from social_agent.models import Article


@pytest.mark.asyncio
async def test_run_once_filters_and_sorts_new_articles(tmp_path):
    config = AgentConfig(
        wordpress=WordPressConfig(
            site_url="https://yenifikirler.org",
            poll_interval=60,
            max_items=10,
        ),
        state_file=tmp_path / "state.json",
        images=ImageServiceSettings(enabled=False, persist_to_disk=False),
    )
    agent = SocialMediaAgent(config)

    now = datetime.now(timezone.utc)
    existing_article = Article(
        identifier="existing",
        title="Existing",
        url="https://yenifikirler.org/existing",
        summary="Existing article",
        published=now - timedelta(days=3),
    )
    older_article = Article(
        identifier="older",
        title="Older",
        url="https://yenifikirler.org/older",
        summary="Older article",
        published=now - timedelta(days=2),
    )
    newer_article = Article(
        identifier="newer",
        title="Newer",
        url="https://yenifikirler.org/newer",
        summary="Newer article",
        published=now - timedelta(days=1),
    )

    agent.wordpress_client.fetch = AsyncMock(return_value=[newer_article, existing_article, older_article])
    agent.dispatcher.distribute = AsyncMock()
    agent.state.posted_ids = {existing_article.identifier}

    await agent.run_once()

    agent.dispatcher.distribute.assert_awaited_once()
    (articles,), _ = agent.dispatcher.distribute.await_args
    assert [article.identifier for article in articles] == [older_article.identifier, newer_article.identifier]


@pytest.mark.asyncio
async def test_run_once_skips_when_no_new_articles(tmp_path):
    config = AgentConfig(
        wordpress=WordPressConfig(site_url="https://yenifikirler.org"),
        state_file=tmp_path / "state.json",
        images=ImageServiceSettings(enabled=False, persist_to_disk=False),
    )
    agent = SocialMediaAgent(config)

    agent.wordpress_client.fetch = AsyncMock(return_value=[])
    agent.dispatcher.distribute = AsyncMock()

    await agent.run_once()

    agent.dispatcher.distribute.assert_not_called()
