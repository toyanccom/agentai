"""Integration helpers for popular commerce platforms."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, MutableMapping, Optional

from .assistant import MultilingualSupportAssistant, build_default_assistant


class IntegrationError(RuntimeError):
    """Base class for integration related errors."""


class SignatureVerificationError(IntegrationError):
    """Raised when an HMAC signature cannot be verified."""


class PayloadValidationError(IntegrationError):
    """Raised when an integration request payload is invalid."""


@dataclass
class IntegrationResponse:
    """Normalized HTTP response returned to platform webhooks."""

    status_code: int
    body: Dict[str, Any]
    headers: MutableMapping[str, str] = field(
        default_factory=lambda: {"Content-Type": "application/json; charset=utf-8"}
    )

    def to_http(self) -> Dict[str, Any]:
        """Return a serializable HTTP response representation."""

        payload = {
            "status_code": self.status_code,
            "headers": dict(self.headers),
            "body": json.dumps(self.body, ensure_ascii=False),
        }
        return payload


def _load_payload(body: bytes) -> Dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:  # pragma: no cover - defensive
        raise PayloadValidationError("Request body must be valid UTF-8 JSON") from exc

    if not isinstance(payload, Mapping):
        raise PayloadValidationError("JSON payload must be an object")
    return dict(payload)


def _extract_language(payload: Mapping[str, Any], fallback: str = "en") -> str:
    for key in ("language", "locale", "customer_locale", "shop_locale"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.split("-")[0].lower()
    return fallback


def _extract_context(payload: Mapping[str, Any]) -> Dict[str, Any]:
    context = payload.get("context")
    if context is None:
        return {}
    if not isinstance(context, Mapping):
        raise PayloadValidationError("Context must be an object of key/value pairs")
    return {str(key): value for key, value in context.items()}


def _intent_from_payload(payload: Mapping[str, Any]) -> str:
    intent = payload.get("intent")
    if not isinstance(intent, str) or not intent.strip():
        raise PayloadValidationError("Intent is required and must be a string")
    return intent


def _default_assistant(assistant: Optional[MultilingualSupportAssistant]) -> MultilingualSupportAssistant:
    return assistant if assistant is not None else build_default_assistant()


@dataclass
class WordPressWebhookAdapter:
    """Handle webhook requests from WordPress sites."""

    assistant: Optional[MultilingualSupportAssistant] = None
    shared_secret: Optional[str] = None
    signature_header: str = "X-Assistant-Signature"

    def dispatch(
        self, body: bytes, headers: Optional[Mapping[str, str]] = None
    ) -> IntegrationResponse:
        payload = _load_payload(body)
        self._verify_signature(body, headers)
        assistant = _default_assistant(self.assistant)

        intent = _intent_from_payload(payload)
        language = _extract_language(payload)
        context = _extract_context(payload)

        reply = assistant.respond(intent, language, **context)
        response_body = {
            "intent": intent,
            "language": language,
            "reply": reply,
            "supported_languages": assistant.supported_languages(intent),
        }
        return IntegrationResponse(status_code=200, body=response_body)

    def _verify_signature(
        self, body: bytes, headers: Optional[Mapping[str, str]]
    ) -> None:
        if not self.shared_secret:
            return
        if not headers:
            raise SignatureVerificationError("Missing headers for signature validation")

        header_key = self.signature_header.lower()
        signature = None
        for key, value in headers.items():
            if key.lower() == header_key:
                signature = value
                break

        if not signature:
            raise SignatureVerificationError("Missing integration signature header")

        expected = hmac.new(
            self.shared_secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            raise SignatureVerificationError("Signature mismatch for WordPress webhook")


@dataclass
class ShopifyAppProxyAdapter:
    """Handle Shopify App Proxy requests using shared secret verification."""

    assistant: Optional[MultilingualSupportAssistant] = None
    shared_secret: Optional[str] = None
    signature_header: str = "X-Shopify-Hmac-Sha256"

    def dispatch(
        self, body: bytes, headers: Optional[Mapping[str, str]] = None
    ) -> IntegrationResponse:
        payload = _load_payload(body)
        self._verify_signature(body, headers)
        assistant = _default_assistant(self.assistant)

        intent = _intent_from_payload(payload)
        language = _extract_language(payload)
        context = _extract_context(payload)

        reply = assistant.respond(intent, language, **context)
        response_body = {
            "intent": intent,
            "language": language,
            "reply": reply,
            "supported_languages": assistant.supported_languages(intent),
        }
        return IntegrationResponse(status_code=200, body=response_body)

    def _verify_signature(
        self, body: bytes, headers: Optional[Mapping[str, str]]
    ) -> None:
        if not self.shared_secret:
            return

        if not headers:
            raise SignatureVerificationError("Missing headers for signature validation")

        header_key = self.signature_header.lower()
        signature = None
        for key, value in headers.items():
            if key.lower() == header_key:
                signature = value
                break

        if not signature:
            raise SignatureVerificationError("Missing Shopify HMAC header")

        digest = hmac.new(
            self.shared_secret.encode("utf-8"), body, hashlib.sha256
        ).digest()
        expected = base64.b64encode(digest).decode("utf-8")

        if not hmac.compare_digest(expected, signature):
            raise SignatureVerificationError("Signature mismatch for Shopify app proxy")
