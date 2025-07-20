from django.contrib.auth import get_user_model
from django.db import models

from .enums import PlayerEnum

User = get_user_model()


class PlayerLocation(models.Model):
    """Модель локации игрока."""

    country = models.CharField(
        'страна', max_length=PlayerEnum.LOCATION_MAX_LENGTH.value
    )
    city = models.CharField(
        'город', max_length=PlayerEnum.LOCATION_MAX_LENGTH.value
    )

    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'


class Player(models.Model):
    """Модель игрока."""

    class Gender(models.TextChoices):
        """Класс перечисления пола игрока."""

        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'        

    class Level(models.TextChoices):
        """Класс перечисления уровней навыков игрока."""

        LIGHT = 'light', 'Beginner'
        MEDIUM = 'medium', 'Confident amateur'
        HARD = 'hard', 'Advanced'
        PRO = 'pro', 'Professional'

    user = models.ForeignKey(
        User,
        related_name='player',
        verbose_name='игрок',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    gender = models.CharField(
        max_length=PlayerEnum.GENDER_MAX_LENGTH.value,
        choices=Gender.choices,
        blank=False,
        default=Gender.MALE,
        verbose_name='пол'
    )
    level = models.CharField(
        max_length=PlayerEnum.LEVEL_MAX_LENGTH.value,
        choices=Level.choices,
        default=Level.LIGHT,
        verbose_name='уровень',
    )
    avatar = models.ImageField(
        upload_to='players/avatars/',
        null=True,
        blank=True,
        default=None,
        verbose_name='аватар',
    )
    location = models.ForeignKey(
        PlayerLocation,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='локация',
    )
    rating = models.PositiveIntegerField(
        default=PlayerEnum.DEFAULT_RATING.value,
        verbose_name='рейтинг',
    )

    class Meta:
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'
