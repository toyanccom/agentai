"""Utilities for the Multilingual Customer Support Assistant."""

from .assistant import (
    MultilingualSupportAssistant,
    ResponseTemplate,
    build_default_assistant,
    demo_conversation,
)
from .integrations import (
    IntegrationError,
    IntegrationResponse,
    PayloadValidationError,
    ShopifyAppProxyAdapter,
    SignatureVerificationError,
    WordPressWebhookAdapter,
)
from .servers import main as serve_cli
from .servers import serve_shopify, serve_wordpress

__all__ = [
    "IntegrationError",
    "IntegrationResponse",
    "MultilingualSupportAssistant",
    "PayloadValidationError",
    "ResponseTemplate",
    "ShopifyAppProxyAdapter",
    "SignatureVerificationError",
    "WordPressWebhookAdapter",
    "serve_cli",
    "serve_shopify",
    "serve_wordpress",
    "build_default_assistant",
    "demo_conversation",
]
