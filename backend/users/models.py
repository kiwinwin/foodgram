from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """CustomUser class."""

    email = models.EmailField(max_length=254,
                              unique=True)
    avatar = models.ImageField(
        null=True,
        upload_to="users/")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name", "password"]

    class Meta:

        ordering = ["username"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username
