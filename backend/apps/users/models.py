from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """Базовая модель пользователя."""

    class GameSkillLevel(models.TextChoices):
        """Класс перечисления уровней навыков игрока."""

        BEGINNER = 'beginner', 'Beginner'
        AMATEUR = 'amateur', 'Amateur'
        ADVANCED = 'advanced', 'Advanced'
        PRO = 'pro', 'Pro'

    phone_number = PhoneNumberField(
        unique=True,
        verbose_name='Телефон',
    )
    game_skill_level = models.CharField(
        max_length=12,
        choices=GameSkillLevel.choices,
        default=GameSkillLevel.BEGINNER,
        verbose_name='Уровень Игры',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар',
    )
    # location = models.ForeignKey(
    #     Location,
    #     on_delete=models.SET_NULL,
    #     null=True,
    # )
    rating = models.PositiveIntegerField(
        default=1000,
        verbose_name='Рейтинг',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
