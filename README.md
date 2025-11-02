# Multilingual Customer Support Assistant

A lightweight reference implementation of a multilingual customer support bot
that can serve global customers 24/7. The assistant understands and responds in
multiple languages, helping businesses remove language barriers without hiring
regional teams.

## Key capabilities

- **Language-aware responses** – Ships with curated answers across the ten most
  widely used languages (Arabic, Bengali, English, French, Hindi, Mandarin
  Chinese, Portuguese, Russian, Spanish, and Urdu) for high-volume intents such
  as order status, shipping options, return policy, and agent availability.
- **Graceful fallbacks** – Politely prompts for clarification when the bot does
  not understand an intent and falls back to a primary language when a
  translation is unavailable.
- **Extensible knowledge base** – Developers can register additional intents or
  languages at runtime using the `MultilingualSupportAssistant.register_response`
  method.

## Why it matters

Global retailers can embed this assistant in their help centers to handle
questions about orders, products, and returns in local languages and time zones.
Automating those conversations keeps response times low, boosts customer
satisfaction, and frees human agents to focus on edge cases.

## Getting started

1. Install dependencies (for testing):

   ```bash
   pip install -r requirements-dev.txt
   ```

   The project intentionally has no runtime dependencies beyond the Python
   standard library.

2. Explore the demo conversation in a Python shell:

   ```python
   >>> from src.assistant import demo_conversation
   >>> demo_conversation()
   {
       'english': 'Your order A1234 is currently on the way. You can expect delivery by May 18.',
       'spanish': 'Los artículos pueden devolverse dentro de 30 días en su estado original para un reembolso.',
       'mandarin': '我们提供标准和快速配送服务。快速配送可在 3 天内送达。',
       'arabic': 'نقدم شحنًا عاديًا وسريعًا. تصل الشحنات السريعة خلال 3 أيام.',
       'hindi': 'हमारे समर्थन एजेंट इस सहायक के माध्यम से 24/7 उपलब्ध हैं।',
       'fallback': "I'm sorry, I didn't understand that request. Could you rephrase it?"
   }
   ```

3. Run the command line demo for ad-hoc queries:

   ```bash
   python -m src.assistant order_status -l es -c order_id=A1234 status="en camino" eta="18 de mayo"
   ```

   Example output:

   ```json
   {
     "intent": "order_status",
     "language": "es",
     "response": "Tu pedido A1234 está actualmente en camino. La entrega está prevista para 18 de mayo.",
     "supported_languages": [
       "ar",
       "bn",
       "en",
       "es",
       "fr",
       "hi",
       "pt",
       "ru",
       "ur",
       "zh"
     ]
  }
  ```

## Embedding in WordPress

Use the `WordPressWebhookAdapter` to expose the assistant through a lightweight
Python endpoint that your WordPress site can call from a custom plugin or a
no-code automation tool like WP Webhooks.

```python
from http.server import BaseHTTPRequestHandler, HTTPServer

from src import WordPressWebhookAdapter

adapter = WordPressWebhookAdapter(shared_secret="super-secret-token")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        response = adapter.dispatch(body, headers=self.headers)

        payload = response.to_http()
        self.send_response(payload["status_code"])
        for header, value in payload["headers"].items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(payload["body"].encode("utf-8"))


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
```

Configure your WordPress automation to send a JSON payload with `intent`,
`language` (or `locale`), and optional `context` values. The shared secret is
used to sign requests via the `X-Assistant-Signature` header and prevents
unauthorized calls.

## Embedding in Shopify

Shopify app proxies and theme extensions can call the
`ShopifyAppProxyAdapter` in a similar fashion. Shopify signs requests via the
`X-Shopify-Hmac-Sha256` header so you only need to provide the shared secret
issued to your custom app.

```python
from http.server import BaseHTTPRequestHandler, HTTPServer

from src import ShopifyAppProxyAdapter

adapter = ShopifyAppProxyAdapter(shared_secret="shopify-shared-secret")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        response = adapter.dispatch(body, headers=self.headers)

        payload = response.to_http()
        self.send_response(payload["status_code"])
        for header, value in payload["headers"].items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(payload["body"].encode("utf-8"))


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
```

Incoming Shopify requests include `locale`, `customer_locale`, or
`shop_locale` fields that are automatically mapped to the assistant's
language codes. Provide the request context (for example, `{"order_id": "A1"}`)
to personalize the reply. The response body mirrors the CLI payload and can be
rendered directly within your theme or storefront app.

## Running tests

```bash
pytest
```
