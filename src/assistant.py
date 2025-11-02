"""Multilingual customer support assistant utilities.

This module exposes the :class:`MultilingualSupportAssistant` class which can be
embedded inside customer support tools.  It keeps a lightweight, in-memory
knowledge base of templated answers across multiple languages and falls back to a
preferred language when a translation is unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Mapping, MutableMapping, Optional


@dataclass
class ResponseTemplate:
    """A templated response that can be rendered with contextual data."""

    text: str

    def render(self, **context: str) -> str:
        """Render the template with a defensive fallback.

        Missing keys are left unsubstituted instead of raising ``KeyError``.
        This makes it easier to stream partially filled responses during a live
        chat session.
        """

        rendered = self.text
        for key, value in context.items():
            placeholder = "{" + key + "}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered


@dataclass
class MultilingualSupportAssistant:
    """Provide canned responses for common customer support intents.

    Parameters
    ----------
    responses:
        Optional pre-populated mapping with the schema
        ``{intent: {language_code: ResponseTemplate}}``.  The assistant ships
        with a compact set of defaults that cover order status, shipping, and
        return questions across English, Spanish, Mandarin Chinese, and French.
    fallback_language:
        ISO language code used whenever a translation for the requested
        language is missing.
    """

    responses: MutableMapping[str, MutableMapping[str, ResponseTemplate]] = field(
        default_factory=dict
    )
    fallback_language: str = "en"

    def __post_init__(self) -> None:
        if not self.responses:
            self.responses.update(_build_default_responses())

    def register_response(
        self,
        intent: str,
        language: str,
        template: str,
    ) -> None:
        """Register or overwrite a response template for an intent."""

        intent_map = self.responses.setdefault(intent, {})
        intent_map[language.lower()] = ResponseTemplate(template)

    def respond(self, intent: str, language: str, **context: str) -> str:
        """Return the best available response for an intent.

        If the language is not supported, a fallback language is used.  When the
        intent has never been seen before a generic clarification prompt is
        returned so human agents can step in gracefully.
        """

        intent_map = self.responses.get(intent)
        if not intent_map:
            return self._clarification_message(language)

        language = language.lower()
        template = intent_map.get(language)

        if template is None:
            template = intent_map.get(self.fallback_language)
            if template is None:
                # If the fallback language is also missing, defer to the first
                # translation available to avoid leaving the user without any
                # assistance.
                template = next(iter(intent_map.values()))

        return template.render(**context)

    def supported_languages(self, intent: Optional[str] = None) -> Iterable[str]:
        """Return supported language codes.

        When ``intent`` is provided, only the languages for that intent are
        returned.  Otherwise the union of all languages across the knowledge base
        is produced.
        """

        if intent:
            return tuple(sorted(self.responses.get(intent, {}).keys()))

        languages = {lang for intent_map in self.responses.values() for lang in intent_map}
        return tuple(sorted(languages))

    def _clarification_message(self, language: str) -> str:
        """Return a polite clarification message in the requested language."""

        language = language.lower()
        message = _CLARIFICATION_MESSAGES.get(language)
        if message is None:
            message = _CLARIFICATION_MESSAGES.get(self.fallback_language)
        return message


def _build_default_responses() -> Dict[str, Dict[str, ResponseTemplate]]:
    """Construct default multilingual responses for common intents."""

    def wrap(translations: Mapping[str, str]) -> Dict[str, ResponseTemplate]:
        return {lang: ResponseTemplate(text) for lang, text in translations.items()}

    return {
        "order_status": wrap(
            {
                "en": "Your order {order_id} is currently {status}. You can expect delivery by {eta}.",
                "es": "Tu pedido {order_id} está actualmente {status}. La entrega está prevista para {eta}.",
                "zh": "您的订单 {order_id} 目前处于 {status} 状态，预计在 {eta} 送达。",
                "fr": "Votre commande {order_id} est actuellement {status}. La livraison est prévue pour {eta}.",
            }
        ),
        "shipping_options": wrap(
            {
                "en": "We offer standard and express shipping. Express deliveries arrive within {days} days.",
                "es": "Ofrecemos envíos estándar y exprés. Las entregas exprés llegan en {days} días.",
                "zh": "我们提供标准和快速配送服务。快速配送可在 {days} 天内送达。",
                "fr": "Nous proposons une livraison standard et express. L'express arrive sous {days} jours.",
            }
        ),
        "return_policy": wrap(
            {
                "en": "Items can be returned within {window} days in their original condition for a refund.",
                "es": "Los artículos pueden devolverse dentro de {window} días en su estado original para un reembolso.",
                "zh": "商品可在 {window} 天内保持完好进行退货退款。",
                "fr": "Les articles peuvent être retournés sous {window} jours dans leur état d'origine pour un remboursement.",
            }
        ),
        "store_hours": wrap(
            {
                "en": "Our support agents are available 24/7 through this assistant.",
                "es": "Nuestros agentes de soporte están disponibles 24/7 mediante este asistente.",
                "zh": "我们的支持团队通过此助手提供全天候服务。",
                "fr": "Nos agents d'assistance sont disponibles 24h/24 et 7j/7 via cet assistant.",
            }
        ),
    }


_CLARIFICATION_MESSAGES: Dict[str, str] = {
    "en": "I'm sorry, I didn't understand that request. Could you rephrase it?",
    "es": "Lo siento, no entendí la solicitud. ¿Podrías reformularla?",
    "zh": "抱歉，我未能理解您的请求。可以换种说法吗？",
    "fr": "Je suis désolé, je n'ai pas compris votre demande. Pourriez-vous la reformuler ?",
}


def build_default_assistant() -> MultilingualSupportAssistant:
    """Return a ready-to-use assistant populated with default responses."""

    return MultilingualSupportAssistant()


def demo_conversation() -> Mapping[str, str]:
    """Return sample replies across languages for documentation examples."""

    assistant = build_default_assistant()
    return {
        "english": assistant.respond(
            "order_status", "en", order_id="A1234", status="on the way", eta="May 18"
        ),
        "spanish": assistant.respond(
            "return_policy", "es", window=30
        ),
        "mandarin": assistant.respond(
            "shipping_options", "zh", days=3
        ),
        "fallback": assistant.respond("loyalty_program", "de"),
    }


def main() -> None:
    """Entry point for the command line demonstration."""

    import argparse
    import json

    assistant = build_default_assistant()

    parser = argparse.ArgumentParser(description="Multilingual support assistant demo")
    parser.add_argument("intent", help="Intent to query, e.g. order_status")
    parser.add_argument(
        "--language", "-l", default="en", help="Language code such as en, es, zh, fr"
    )
    parser.add_argument(
        "--context",
        "-c",
        nargs="*",
        default=(),
        metavar="KEY=VALUE",
        help="Context variables to inject into the template",
    )

    args = parser.parse_args()

    context: Dict[str, str] = {}
    for item in args.context:
        if "=" not in item:
            parser.error(f"Invalid context assignment: {item}")
        key, value = item.split("=", 1)
        context[key] = value

    response = assistant.respond(args.intent, args.language, **context)
    payload = {
        "intent": args.intent,
        "language": args.language,
        "response": response,
        "supported_languages": assistant.supported_languages(args.intent),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
