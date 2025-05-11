from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
    )
    first_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=150,
        blank=False,
        verbose_name='Фамилия',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username',]
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['username',]

    def __str__(self):
        return self.email


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик',
    )

    class Meta:
        unique_together = (
            'user',
            'following',
        )
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ['user__username',]

    def clean(self):
        if self.user == self.following:
            raise ValidationError(
                "Нельзя подписаться на самого себя."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
