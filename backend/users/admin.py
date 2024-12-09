from django.contrib import admin
from users.models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    """Class for making admin zone."""

    list_display = ("username", "email",)
    search_fields = ("username", "email",)
    empty_value_display = "-пусто-"


admin.site.register(CustomUser, CustomUserAdmin)
