from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session_id", "user", "role", "short_message", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("session_id", "external_user_id", "message", "user__username", "user__display_name")
    readonly_fields = ("created_at",)

    def short_message(self, obj):
        return (obj.message[:75] + "...") if len(obj.message) > 75 else obj.message

    short_message.short_description = "Message"
