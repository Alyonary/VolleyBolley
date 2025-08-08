from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """User model."""

    MAX_LENGTH = 150
    REQUIRED_FIELDS = ['first_name', 'last_name']
    username_validator = UnicodeUsernameValidator()

    phone_number = PhoneNumberField(
        unique=True,
        blank=True,
        null=True,
        default=None,
        verbose_name=_('Phone number'),
    )
    username = models.CharField(
        _('Username'),
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
    first_name = models.CharField(
        _('First name'), max_length=MAX_LENGTH, blank=False
    )
    last_name = models.CharField(
        _('Last name'), max_length=MAX_LENGTH, blank=False
    )
    email = models.EmailField(
        _('email'), blank=True, null=True
    )

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
