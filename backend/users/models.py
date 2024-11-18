from django.contrib.auth.models import AbstractUser

from django.db import models
#from foodgram.models import Subscription


class CustomUser(AbstractUser):
    """Класс пользователя."""

    email = models.EmailField(max_length=254,
                              unique=True)
    avatar = models.ImageField(
        null=True,
        upload_to='users/')
    '''is_subscribed = models.BooleanField(
        null=True,
        blank=True)'''
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']

    class Meta:
        ordering = ["username"]
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.username

'''    @property
    def is_subscribed(self):
        if Subscription.objects.filter(user=self.request.user.id,
                                       following=self.id) is not None:
            return True
        return False'''