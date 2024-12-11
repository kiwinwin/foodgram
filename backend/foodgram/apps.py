from django.apps import AppConfig


class FoodgramConfig(AppConfig):
    "Class of foodgram app config."

    default_auto_field = "django.db.models.BigAutoField"
    name = "foodgram"
    verbose_name = "Фудграм"
