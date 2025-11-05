from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_user_id', models.CharField(db_index=True, help_text='Identifier supplied by Telegram for the chat user.', max_length=255)),
                ('session_id', models.CharField(db_index=True, help_text='Telegram chat/session identifier.', max_length=255)),
                ('role', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')], default='user', help_text='Message author role.', max_length=20)),
                ('message', models.TextField(help_text='Full message content.')),
                ('metadata', models.JSONField(blank=True, help_text='Optional metadata captured alongside the message.', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(help_text='Associated Django user for this chat session.', on_delete=django.db.models.deletion.CASCADE, related_name='chat_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
