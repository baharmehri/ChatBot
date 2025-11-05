# ChatBot

ChatBot is a Django-based backend that powers a Persian-language medical assistant. The project wires together a Telegram bot, a custom LLM agent built on top of `google-adk`, and structured medical data stored in JSON files. Conversations are persisted in the database, allowing the agent to answer follow-up questions while staying grounded in the available records.

## Features
- Persian medical assistant with strict, data-grounded responses.
- Telegram integration with `/start`, `/reset`, and free-form chat handling.
- Session-aware LLM agent backed by `google-adk` runners and LiteLLM.
- Django admin and custom user model for tracking Telegram users.
- Structured medical data ingestion from configurable JSON files.

## Requirements
- Python 3.10 or later.
- A virtual environment (recommended).
- Access credentials for your LLM provider (set via environment variables).
- Telegram bot token (from BotFather).

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Configuration
Create a `.env` file in the project root (`BASE_DIR` in Django settings) and define the variables you need. Common settings include:

```dotenv
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (defaults to SQLite db.sqlite3 if omitted)
DJANGO_DB_ENGINE=django.db.backends.sqlite3
DJANGO_DB_NAME=db.sqlite3

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-token

# LLM / google-adk
OPENAI_MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.your-provider.com/v1

# Optional: point the agent to a different medical data file
USER_MEDICAL_DATA_PATH=/absolute/path/to/user_data.json
```

The agent reads structured medical information from the JSON file returned by `USER_MEDICAL_DATA_PATH`. If the variable is not set, the default file `user_test_data.json` in the project root is used. Update or replace the JSON file to serve different users.

## Database Setup
Apply migrations before running the project:

```bash
python manage.py migrate
```

Create a superuser if you want to access the Django admin:

```bash
python manage.py createsuperuser
```

## Running the Services

### Django application
Start the Django development server:

```bash
python manage.py runserver
```

The server exposes the admin site and stores chat transcripts via the `telegram_bot.ChatMessage` model.

### Telegram bot
Run the long-polling Telegram bot (requires `TELEGRAM_BOT_TOKEN`):

```bash
python manage.py runtelegrambot
```

The bot will connect to Telegram, listen for incoming messages, and route conversations to `PersianMedicalAgent`.

## Telegram Commands
- `/start` – Greets the user and explains the bot.
- `/reset` – Clears the current chat session and forgets previous context.
- Free-form text – Forwarded to the medical agent for a grounded answer.

All user and assistant messages are logged to the database with metadata for auditing.

## Development Tips
- Use `/reset` before starting a new medical query if you want to ignore previous answers.
- When swapping the underlying JSON medical data file, restart the bot or clear the cached data with:

  ```python
  from chatbot_agent import medical_tools
  medical_tools._load_data.cache_clear()
  ```

- Run tests with `python manage.py test`.
- Logs are stored in the `logs/` directory by default; adjust via `DJANGO_LOG_DIR`.

## Repository Layout
- `ChatBot/` – Django project settings and URLs.
- `chatbot_agent/` – Agent definitions, prompts, and medical data helpers.
- `telegram_bot/` – Telegram integration, commands, and bot runtime.
- `users/` – Custom Django user model for Telegram accounts.
- `*.json` – Sample medical data files used by the agent.

Feel free to expand the README with deployment notes or additional provider-specific instructions as your setup evolves.
