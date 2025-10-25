from django.conf import settings
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Default /start handler that confirms the bot is alive."""
    user = update.effective_user
    name = user.full_name if user else "there"
    await update.message.reply_text(f"Hi {name}! I'm your ChatBot assistant.")


def build_application(token: str | None = None):
    """Create a Telegram Application with core handlers registered."""
    bot_token = token or settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    return application
