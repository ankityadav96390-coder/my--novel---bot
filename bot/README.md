# Gemini Telegram Bot 🤖

Python-based Telegram Bot powered by Google Gemini AI.

## Setup

### 1. Secrets Set करें

Replit के Secrets (🔒) में ये दो keys डालें:

| Key | Value |
|-----|-------|
| `TELEGRAM_TOKEN` | @BotFather से मिला token |
| `GEMINI_API_KEY` | Google AI Studio से मिली key |

### 2. Bot Token कैसे पाएं

1. Telegram पर `@BotFather` को `/newbot` भेजें
2. Bot का नाम और username दें
3. Token copy करें

### 3. Gemini API Key कैसे पाएं

1. [Google AI Studio](https://aistudio.google.com) पर जाएं
2. "Get API Key" पर click करें
3. Key copy करें

## Features

- 🗣️ हिंदी और English दोनों में बात
- 🧠 Conversation history याद रखता है
- 🔄 `/new` से नई बातचीत शुरू
- ✂️ Long responses automatically split

## Commands

- `/start` — Bot शुरू करें
- `/new` — नई बातचीत (history clear)
- `/help` — Help देखें
