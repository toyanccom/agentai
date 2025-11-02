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

## Running tests

```bash
pytest
```
