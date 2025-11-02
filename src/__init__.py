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

__all__ = [
    "IntegrationError",
    "IntegrationResponse",
    "MultilingualSupportAssistant",
    "PayloadValidationError",
    "ResponseTemplate",
    "ShopifyAppProxyAdapter",
    "SignatureVerificationError",
    "WordPressWebhookAdapter",
    "build_default_assistant",
    "demo_conversation",
]
