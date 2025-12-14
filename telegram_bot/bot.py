import logging
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.error import TimedOut as TelegramTimedOut

from asgiref.sync import sync_to_async

from chatbot_agent.agents.medical_runtime_agent import PersianMedicalAgent
from .models import ChatMessage

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Default /start handler that confirms the bot is alive."""
    user = update.effective_user
    name = user.full_name if user else "there"
    await update.message.reply_text(
        f"سلام {name}! من دستیار پزشکی فارسی هستم. سوالات پزشکی خود را بپرس."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the current conversation session for the chat."""
    message = update.message
    if not message:
        return

    user = update.effective_user
    user_id = str(user.id if user else message.chat_id)
    session_id = str(message.chat_id)
    text = message.text or "/reset"
    user_metadata = _build_user_metadata(user, message.chat_id)

    django_user = await _get_or_create_user(user, message.chat_id)

    await _store_chat_message(
        role=ChatMessage.ROLE_USER,
        user=django_user,
        external_user_id=user_id,
        session_id=session_id,
        text=text,
        metadata=dict(user_metadata),
    )

    reply = "گفتگو پاک شد. لطفاً سوال جدیدی ارسال کنید."
    try:
        agent = await PersianMedicalAgent.create(user_id=user_id, session_id=session_id)
        await agent.reset_session(session_id=session_id)
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to reset session %s", session_id)
        reply = "در بازنشانی گفتگو خطایی رخ داد، لطفاً بعداً دوباره تلاش کنید."

    try:
        await message.reply_text(reply)
    except TelegramTimedOut:
        logger.warning("Failed to send reset reply to chat %s due to Telegram timeout.", session_id)
    finally:
        await _store_chat_message(
            role=ChatMessage.ROLE_ASSISTANT,
            user=django_user,
            external_user_id=user_id,
            session_id=session_id,
            text=reply,
            metadata=dict(user_metadata),
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
    user_metadata = _build_user_metadata(user, message.chat_id)

    django_user = await _get_or_create_user(user, message.chat_id)

    await _store_chat_message(
        role=ChatMessage.ROLE_USER,
        user=django_user,
        external_user_id=user_id,
        session_id=session_id,
        text=text,
        metadata=dict(user_metadata),
    )

    reply = ""
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
    finally:
        await _store_chat_message(
            role=ChatMessage.ROLE_ASSISTANT,
            user=django_user,
            external_user_id=user_id,
            session_id=session_id,
            text=reply,
            metadata=dict(user_metadata),
        )


def build_application(token: str | None = None):
    """Create a Telegram Application with core handlers registered."""
    bot_token = token or settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, medical_chat))
    return application


def _build_user_metadata(user, chat_id: int) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {"chat_id": chat_id}
    if user:
        if user.username:
            metadata["username"] = user.username
        if user.first_name:
            metadata["first_name"] = user.first_name
        if user.last_name:
            metadata["last_name"] = user.last_name
        if user.language_code:
            metadata["language_code"] = user.language_code
        metadata["is_bot"] = user.is_bot
    return metadata


async def _store_chat_message(
        *,
        role: str,
        user,
        external_user_id: str,
        session_id: str,
        text: str,
        metadata: Dict[str, Any] | None = None,
) -> None:
    try:
        await sync_to_async(ChatMessage.objects.create)(
            user=user,
            external_user_id=external_user_id,
            session_id=session_id,
            role=role,
            message=text,
            metadata=metadata,
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to persist %s message for session %s", role, session_id)


async def _get_or_create_user(telegram_user, chat_id: int):
    return await sync_to_async(_get_or_create_user_sync)(telegram_user, chat_id)


def _get_or_create_user_sync(telegram_user, chat_id: int):
    UserModel = get_user_model()
    telegram_id: Optional[str] = None
    if telegram_user:
        telegram_id = str(telegram_user.id)
        user = UserModel.objects.filter(telegram_id=telegram_id).first()
    else:
        user = None

    display_name = _derive_display_name(telegram_user, chat_id)
    first_name = getattr(telegram_user, "first_name", "") or ""
    last_name = getattr(telegram_user, "last_name", "") or ""
    telegram_username = getattr(telegram_user, "username", "") or ""
    telegram_language_code = getattr(telegram_user, "language_code", "") or ""

    if user:
        fields_to_update: list[str] = []
        field_updates = {
            "display_name": display_name,
            "first_name": first_name,
            "last_name": last_name,
            "telegram_username": telegram_username,
            "telegram_language_code": telegram_language_code,
        }
        for field, value in field_updates.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                fields_to_update.append(field)
        if fields_to_update:
            user.save(update_fields=fields_to_update)
        return user

    base_username = telegram_username or f"telegram_{telegram_id or chat_id}"
    username = _generate_unique_username(UserModel, base_username)

    user = UserModel(
        username=username,
        display_name=display_name,
        first_name=first_name,
        last_name=last_name,
        telegram_id=telegram_id,
        telegram_username=telegram_username,
        telegram_language_code=telegram_language_code,
    )
    user.set_unusable_password()
    user.save()
    return user


def _generate_unique_username(user_model, base: str) -> str:
    sanitized = base.replace(" ", "_")
    sanitized = sanitized[:150] or "telegram_user"
    username = sanitized
    counter = 1
    while user_model.objects.filter(username=username).exists():
        suffix = f"_{counter}"
        username = f"{sanitized[:150 - len(suffix)]}{suffix}"
        counter += 1
    return username


def _derive_display_name(telegram_user, chat_id: int) -> str:
    if telegram_user:
        full_name = getattr(telegram_user, "full_name", "") or ""
        if full_name.strip():
            return full_name.strip()
        username = getattr(telegram_user, "username", "") or ""
        if username:
            return username
    return f"Telegram chat {chat_id}"
