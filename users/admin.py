from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'display_name', 'telegram_id', 'bio')}),
        (
            'Permissions',
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('username', 'display_name', 'telegram_id', 'bio', 'password1', 'password2'),
            },
        ),
    )
    list_display = ('username', 'email', 'get_display_name', 'get_telegram_id', 'is_staff')
    search_fields = ('username', 'email', 'display_name', 'telegram_id')

    @admin.display(description='Display name', ordering='display_name')
    def get_display_name(self, obj):
        return obj.display_name

    @admin.display(description='Telegram ID', ordering='telegram_id')
    def get_telegram_id(self, obj):
        return obj.telegram_id
