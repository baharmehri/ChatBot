from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_bot", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConversationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_user_id", models.CharField(db_index=True, help_text="Identifier supplied by Telegram for the chat user.", max_length=255)),
                ("session_id", models.CharField(db_index=True, help_text="Telegram chat/session identifier.", max_length=255)),
                ("state", models.JSONField(help_text="Serialized ConversationState JSON for the session.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "unique_together": {("external_user_id", "session_id")},
            },
        ),
    ]
