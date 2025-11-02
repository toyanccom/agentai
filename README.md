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

## WordPress: fastest way to go live

Expose the assistant without writing boilerplate by launching the bundled
webhook server:

```bash
python -m src.servers wordpress --host 0.0.0.0 --port 8080 --shared-secret your-wordpress-secret
```

The server expects JSON payloads containing `intent`, `language` (or `locale`),
and optional `context` values. Pair it with one of these turnkey WordPress
configurations:

1. **WP Webhooks** – Create a "Send Data" action pointing to your server.
   - Method: `POST`
   - Headers: `X-Assistant-Signature: <shared-secret>`
   - Body (JSON):

     ```json
     {
       "intent": "order_status",
       "locale": "en-US",
       "context": {"order_id": "A1234", "status": "on the way", "eta": "May 18"}
     }
     ```

2. **Custom plugin** – Drop the snippet below into `functions.php` or a small
   plugin to forward contact form submissions:

   ```php
   add_action('wp_ajax_nopriv_support_assistant', 'forward_to_assistant');
   add_action('wp_ajax_support_assistant', 'forward_to_assistant');

   function forward_to_assistant() {
       $response = wp_remote_post('https://your-server.example.com', [
           'headers' => [
               'Content-Type' => 'application/json',
               'X-Assistant-Signature' => 'your-wordpress-secret',
           ],
           'body' => wp_json_encode([
               'intent' => sanitize_text_field($_POST['intent']),
               'language' => get_locale(),
               'context' => ['order_id' => sanitize_text_field($_POST['order_id'])],
           ]),
       ]);

       wp_send_json(wp_remote_retrieve_body($response));
   }
   ```

The shared secret protects the webhook via the `X-Assistant-Signature` header,
while the adapter returns a JSON response ready to display in your WordPress
theme or plugin UI.

## Shopify: instant storefront integration

Launch the Shopify-ready server with a single command:

```bash
python -m src.servers shopify --host 0.0.0.0 --port 8080 --shared-secret your-shopify-secret
```

Connect it to a custom app proxy or theme extension:

1. **App proxy** – In the Shopify Partner dashboard, point the proxy URL to the
   server endpoint. Shopify automatically signs requests with
   `X-Shopify-Hmac-Sha256` using the shared secret you configure above.
2. **Theme app extension** – Issue a `fetch` call from your extension block:

   ```javascript
   fetch('https://your-server.example.com', {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'X-Shopify-Hmac-Sha256': Shopify.context.hmac,
     },
     body: JSON.stringify({
       intent: 'shipping_options',
       customer_locale: Shopify.locale,
       context: { days: 3 }
     })
   })
     .then((res) => res.json())
     .then((payload) => {
       renderAssistantResponse(payload.reply);
     });
   ```

Incoming Shopify requests expose `locale`, `customer_locale`, or `shop_locale`
values that the adapter normalizes to the assistant's language codes. The
response mirrors the CLI payload so you can render it directly in your theme or
storefront app.

## Running tests

```bash
pytest
```
