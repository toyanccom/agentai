from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import logging
from pathlib import Path
from typing import Any

import httpx

from .config import ImageServiceSettings
from .models import Article, GeneratedImage

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generate illustrative imagery for articles using an AI provider."""

    def __init__(self, settings: ImageServiceSettings) -> None:
        self.settings = settings
        if settings.persist_to_disk:
            settings.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        return self.settings.enabled and bool(self.settings.api_key)

    async def generate_for_article(self, article: Article) -> GeneratedImage | None:
        """Generate an illustration for the provided article."""

        if not self.enabled:
            logger.debug("Image generation skipped because the integration is disabled or missing credentials.")
            return None
        prompt = self._build_prompt(article)
        alt_text = self._build_alt_text(article)
        payload = self._build_payload(prompt)
        headers = {"Content-Type": "application/json"}
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        try:
            async with httpx.AsyncClient(base_url=str(self.settings.api_base), timeout=self.settings.timeout) as client:
                response = await client.post(self.settings.endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("Failed to generate image for '%s': %s", article.title, exc)
            return None

        image_info = self._extract_image_payload(data)
        if image_info is None:
            logger.warning("Image provider returned an empty response for '%s'.", article.title)
            return None

        file_path: Path | None = None
        remote_url = image_info.get("url")
        if image_info.get("b64_json"):
            file_path = await self._write_base64_image(image_info["b64_json"], article)
        elif self.settings.persist_to_disk and remote_url:
            file_path = await self._download_image(remote_url, article)

        return GeneratedImage(prompt=prompt, alt_text=alt_text, file_path=file_path, remote_url=remote_url)

    def _build_prompt(self, article: Article) -> str:
        categories = ", ".join(article.categories) if article.categories else "general interest"
        summary = self._truncate(article.summary, self.settings.summary_max_length)
        return self.settings.prompt_template.format(
            title=article.title.strip(),
            summary=summary.strip(),
            categories=categories,
            url=article.url,
        )

    def _build_alt_text(self, article: Article) -> str:
        categories = ", ".join(article.categories) if article.categories else "general interest"
        summary = self._truncate(article.summary, 200)
        return self.settings.alt_text_template.format(
            title=article.title.strip(),
            summary=summary.strip(),
            categories=categories,
            url=article.url,
        )

    def _build_payload(self, prompt: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": self.settings.model,
            "size": self.settings.size,
        }
        if self.settings.negative_prompt:
            payload["negative_prompt"] = self.settings.negative_prompt
        if self.settings.quality:
            payload["quality"] = self.settings.quality
        if self.settings.style_preset:
            payload["style_preset"] = self.settings.style_preset
        if self.settings.extra_params:
            payload.update(self.settings.extra_params)
        return payload

    def _extract_image_payload(self, response_data: dict[str, Any]) -> dict[str, Any] | None:
        images = response_data.get("data")
        if not images:
            return None
        first = images[0]
        if isinstance(first, dict):
            return first
        return None

    async def _write_base64_image(self, b64_data: str, article: Article) -> Path | None:
        try:
            binary = base64.b64decode(b64_data)
        except (ValueError, binascii.Error):
            logger.exception("Failed to decode base64 image payload for '%s'.", article.title)
            return None
        suffix = ".png"
        filename = self._build_filename(article, suffix)
        path = self.settings.output_dir / filename
        await asyncio.to_thread(path.write_bytes, binary)
        return path

    async def _download_image(self, url: str, article: Article) -> Path | None:
        try:
            async with httpx.AsyncClient(timeout=self.settings.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Unable to download generated image for '%s': %s", article.title, exc)
            return None
        suffix = self._suffix_from_content_type(response.headers.get("content-type"))
        filename = self._build_filename(article, suffix)
        path = self.settings.output_dir / filename
        await asyncio.to_thread(path.write_bytes, response.content)
        return path

    def _build_filename(self, article: Article, suffix: str) -> str:
        safe_title = "-".join(filter(None, [self._sanitize(article.title)[:40], self._hash_identifier(article.identifier)]))
        if not suffix.startswith("."):
            suffix = f".{suffix}"
        return f"{safe_title}{suffix}"

    @staticmethod
    def _sanitize(value: str) -> str:
        cleaned = [ch.lower() if ch.isalnum() else "-" for ch in value.strip()]
        slug = "".join(cleaned).strip("-")
        return slug or "image"

    @staticmethod
    def _hash_identifier(identifier: str) -> str:
        return hashlib.sha1(identifier.encode("utf-8")).hexdigest()[:10]

    @staticmethod
    def _suffix_from_content_type(content_type: str | None) -> str:
        if not content_type:
            return ".png"
        if "png" in content_type:
            return ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            return ".jpg"
        if "webp" in content_type:
            return ".webp"
        return ".png"

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        truncated = text[: limit - 1].rsplit(" ", 1)[0]
        return truncated + "…"
