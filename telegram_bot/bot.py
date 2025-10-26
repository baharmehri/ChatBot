import logging

from django.conf import settings
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.error import TimedOut as TelegramTimedOut

from chatbot_agent.medical_agent import PersianMedicalAgent

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Default /start handler that confirms the bot is alive."""
    user = update.effective_user
    name = user.full_name if user else "there"
    await update.message.reply_text(
        f"سلام {name}! من دستیار پزشکی فارسی هستم. سوالات پزشکی خود را بپرس."
    )


async def medical_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Relay user questions to the Persian medical agent."""
    message = update.message
    if not message or not message.text:
        return

    text = message.text.strip()
    if not text:
        await message.reply_text("لطفاً سوال خود را به صورت متن ارسال کنید.")
        return

    user = update.effective_user
    user_id = str(user.id if user else message.chat_id)
    session_id = str(message.chat_id)

    try:
        agent = await PersianMedicalAgent.create(user_id=user_id, session_id=session_id)
        reply = await agent.call_agent_async(text)
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Medical agent error for chat %s", session_id)
        reply = "در حال حاضر خطایی رخ داده است، لطفاً بعداً دوباره تلاش کنید."

    try:
        await message.reply_text(reply)
    except TelegramTimedOut:
        logger.warning("Failed to send reply to chat %s due to Telegram timeout.", session_id)


def build_application(token: str | None = None):
    """Create a Telegram Application with core handlers registered."""
    bot_token = token or settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, medical_chat))
    return application
