from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """Модель пользователя."""

    MAX_LENGTH = 150
    REQUIRED_FIELDS = ['first_name', 'last_name']
    username_validator = UnicodeUsernameValidator()

    phone_number = PhoneNumberField(
        unique=True,
        blank=True,
        null=True,
        verbose_name='номер телефона',
    )
    username = models.CharField(
        'имя пользователя',
        max_length=MAX_LENGTH,
        unique=True,
        help_text=(
            f"Required. {MAX_LENGTH} characters or fewer. "
            "Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": "A user with that username already exists.",
        },
    )
    first_name = models.CharField('имя', max_length=MAX_LENGTH, blank=False)
    last_name = models.CharField('фамилия', max_length=MAX_LENGTH, blank=False)
    email = models.EmailField('электронная почта', blank=True, null=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
