from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    display_name = models.CharField(max_length=255, blank=True)
    telegram_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    telegram_username = models.CharField(max_length=255, blank=True)
    telegram_language_code = models.CharField(max_length=10, blank=True)

    def __str__(self) -> str:
        return self.display_name or self.get_full_name() or self.username
