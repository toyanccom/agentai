import base64
import hashlib
import hmac
import json

import pytest

from src import (
    PayloadValidationError,
    ShopifyAppProxyAdapter,
    SignatureVerificationError,
    WordPressWebhookAdapter,
    build_default_assistant,
)


def _wordpress_headers(secret: str, body: bytes) -> dict:
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return {"X-Assistant-Signature": signature}


def _shopify_headers(secret: str, body: bytes) -> dict:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode("utf-8")
    return {"X-Shopify-Hmac-Sha256": signature}


def test_wordpress_adapter_renders_supported_intent():
    assistant = build_default_assistant()
    adapter = WordPressWebhookAdapter(assistant=assistant, shared_secret="secret")

    payload = {
        "intent": "order_status",
        "language": "es",
        "context": {"order_id": "A12", "status": "en camino", "eta": "mañana"},
    }
    body = json.dumps(payload).encode("utf-8")

    response = adapter.dispatch(body, headers=_wordpress_headers("secret", body))

    assert response.status_code == 200
    assert response.body["intent"] == "order_status"
    assert "en camino" in response.body["reply"]


def test_wordpress_adapter_rejects_bad_signature():
    assistant = build_default_assistant()
    adapter = WordPressWebhookAdapter(assistant=assistant, shared_secret="secret")

    body = json.dumps({"intent": "order_status"}).encode("utf-8")

    with pytest.raises(SignatureVerificationError):
        adapter.dispatch(body, headers={"X-Assistant-Signature": "invalid"})


def test_shopify_adapter_uses_locale_when_language_missing():
    assistant = build_default_assistant()
    adapter = ShopifyAppProxyAdapter(assistant=assistant, shared_secret="shop_secret")

    payload = {
        "intent": "return_policy",
        "locale": "fr-CA",
        "context": {"window": 45},
    }
    body = json.dumps(payload).encode("utf-8")

    response = adapter.dispatch(body, headers=_shopify_headers("shop_secret", body))

    assert response.body["language"] == "fr"
    assert "45" in response.body["reply"]


def test_shopify_adapter_requires_intent():
    assistant = build_default_assistant()
    adapter = ShopifyAppProxyAdapter(assistant=assistant)

    payload = {"locale": "en"}
    body = json.dumps(payload).encode("utf-8")

    with pytest.raises(PayloadValidationError):
        adapter.dispatch(body, headers=None)
