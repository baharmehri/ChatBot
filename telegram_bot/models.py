from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_SYSTEM = "system"

    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
        (ROLE_SYSTEM, "System"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        help_text="Associated Django user for this chat session.",
    )
    external_user_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Identifier supplied by Telegram for the chat user.",
    )
    session_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Telegram chat/session identifier.",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        help_text="Message author role.",
    )
    message = models.TextField(help_text="Full message content.")
    metadata = models.JSONField(
        blank=True,
        null=True,
        help_text="Optional metadata captured alongside the message.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.session_id} [{self.role}] @ {self.created_at:%Y-%m-%d %H:%M:%S}"
