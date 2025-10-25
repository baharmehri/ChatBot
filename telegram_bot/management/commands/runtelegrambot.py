from django.core.management.base import BaseCommand, CommandError

from telegram_bot.bot import build_application


class Command(BaseCommand):
    help = "Run the Telegram bot using long polling."

    def handle(self, *args, **options):
        try:
            application = build_application()
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Starting Telegram bot... Press Ctrl+C to stop."))
        try:
            application.run_polling(allowed_updates=[])
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Telegram bot interrupted."))
