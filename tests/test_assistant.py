import json

import pytest

from src.assistant import (
    MultilingualSupportAssistant,
    ResponseTemplate,
    build_default_assistant,
    demo_conversation,
)


def test_render_keeps_missing_placeholders():
    template = ResponseTemplate("Order {order_id} ships {eta} via {carrier}.")
    rendered = template.render(order_id="A1", eta="tomorrow")
    assert rendered == "Order A1 ships tomorrow via {carrier}."


def test_default_responses_cover_core_languages():
    assistant = build_default_assistant()
    expected_languages = {"ar", "bn", "en", "es", "fr", "hi", "pt", "ru", "ur", "zh"}
    for intent in ("order_status", "shipping_options", "return_policy", "store_hours"):
        languages = assistant.supported_languages(intent)
        assert expected_languages.issubset(set(languages))


def test_fallback_language_used_when_translation_missing():
    assistant = MultilingualSupportAssistant(responses={
        "greeting": {"en": ResponseTemplate("Hello")},
    })
    assert assistant.respond("greeting", "de") == "Hello"


def test_unknown_intent_triggers_clarification():
    assistant = build_default_assistant()
    message = assistant.respond("unknown", "es")
    assert "¿Podrías" in message


def test_demo_conversation_serializable():
    conversation = demo_conversation()
    serialized = json.dumps(conversation, ensure_ascii=False)
    assert "A1234" in serialized
    assert "Lo siento" not in serialized
    assert "arabic" in conversation
    assert "urdu" in conversation
