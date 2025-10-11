from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, HttpUrl, validator


class WordPressConfig(BaseModel):
    """Configuration for the WordPress source."""

    site_url: HttpUrl = Field(..., description="Base URL of the WordPress site")
    feed_path: str = Field("/feed", description="Path to the RSS/Atom feed")
    poll_interval: int = Field(300, description="How often to poll the feed in seconds")
    max_items: int = Field(10, description="Maximum number of feed entries to process per poll")

    @property
    def feed_url(self) -> str:
        return f"{str(self.site_url).rstrip('/')}{self.feed_path}"


class PlatformSettings(BaseModel):
    """Generic platform configuration shared across services."""

    enabled: bool = Field(False, description="Whether the integration is active")
    access_token: str | None = Field(None, description="Access token or API key")
    client_id: str | None = None
    client_secret: str | None = None
    page_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class XComSettings(PlatformSettings):
    api_base: str = Field("https://api.x.com/2", description="Base URL for the X REST API")


class LinkedInSettings(PlatformSettings):
    api_base: str = Field("https://api.linkedin.com/v2", description="Base URL for LinkedIn API")
    organization_urn: str | None = Field(None, description="URN of the organization or user")


class FacebookSettings(PlatformSettings):
    api_base: str = Field("https://graph.facebook.com/v18.0", description="Graph API base URL")


class InstagramSettings(PlatformSettings):
    api_base: str = Field("https://graph.facebook.com/v18.0", description="Graph API base URL")
    ig_user_id: str | None = Field(None, description="Instagram Business Account ID")


class PinterestSettings(PlatformSettings):
    api_base: str = Field("https://api.pinterest.com/v5", description="Pinterest API base URL")
    board_id: str | None = None


class TikTokSettings(PlatformSettings):
    api_base: str = Field("https://open.tiktokapis.com/v2", description="TikTok Business API base URL")
    advertiser_id: str | None = None


class ImageServiceSettings(BaseModel):
    """Configuration for the AI image generation provider."""

    enabled: bool = Field(False, description="Whether to request AI generated images")
    api_base: HttpUrl = Field("https://api.openai.com/v1", description="Base URL for the image provider")
    endpoint: str = Field("/images/generations", description="Endpoint to request image generations")
    api_key: str | None = Field(None, description="API key or token for the provider")
    model: str = Field("gpt-image-1", description="Model identifier to request")
    size: str = Field("1024x1024", description="Requested image size")
    quality: str | None = Field(None, description="Optional quality hint (e.g. 'high')")
    style_preset: str | None = Field(None, description="Optional style preset or identifier")
    prompt_template: str = Field(
        "A vibrant illustration for the article titled '{title}'. Summary: {summary}. Highlight themes: {categories}.",
        description="Template used to craft the text prompt. Placeholders: title, summary, categories, url.",
    )
    alt_text_template: str = Field(
        "Illustration accompanying the article '{title}' highlighting {categories} themes.",
        description="Template for accessibility alt text using the same placeholders as the prompt template.",
    )
    summary_max_length: int = Field(400, description="Maximum characters from the article summary to include in prompts")
    negative_prompt: str | None = Field(None, description="Optional negative prompt to steer the image away from elements")
    persist_to_disk: bool = Field(True, description="Persist generated images locally for reuse")
    download_remote_assets: bool = Field(True, description="Download provider hosted images when available")
    output_dir: Path = Field(Path("./generated_images"), description="Directory to save generated images")
    timeout: float = Field(60.0, description="HTTP timeout for API calls in seconds")
    extra_params: dict[str, Any] = Field(default_factory=dict, description="Additional provider-specific request fields")

    @validator("output_dir", pre=True)
    def _expand_output_dir(cls, value: Any) -> Path:
        return Path(value).expanduser().resolve()

    @validator("endpoint")
    def _normalize_endpoint(cls, value: str) -> str:
        if not value.startswith("/"):
            return f"/{value}"
        return value


class AgentConfig(BaseModel):
    """Top level agent configuration."""

    wordpress: WordPressConfig
    xcom: XComSettings = Field(default_factory=XComSettings)
    linkedin: LinkedInSettings = Field(default_factory=LinkedInSettings)
    facebook: FacebookSettings = Field(default_factory=FacebookSettings)
    instagram: InstagramSettings = Field(default_factory=InstagramSettings)
    pinterest: PinterestSettings = Field(default_factory=PinterestSettings)
    tiktok: TikTokSettings = Field(default_factory=TikTokSettings)
    images: ImageServiceSettings = Field(default_factory=ImageServiceSettings)
    state_file: Path = Field(Path(".agent_state.json"), description="Where to persist article state")
    dry_run: bool = Field(False, description="If True do not post, just log actions")

    @validator("state_file", pre=True)
    def _expand_state_file(cls, value: Any) -> Path:
        return Path(value).expanduser().resolve()


def load_config(path: str | Path) -> AgentConfig:
    """Load a YAML configuration file."""

    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw_text = os.path.expandvars(path.read_text())
    raw = yaml.safe_load(raw_text) or {}
    return AgentConfig(**raw)
