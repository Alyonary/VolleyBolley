from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.event.models import Game, Tourney
from apps.locations.models import City, Country
from apps.players.constants import (
    Genders,
    Grades,
    LevelMarkChoices,
    Payments,
    PlayerIntEnums,
    PlayerStrEnums,
)

User = get_user_model()


def validate_birthday(value):
    if value > timezone.now().date():
        raise ValidationError(_('Date of birth cannot be in the future.'))


class PlayerQuerySet(models.QuerySet):
    """Custom QuerySet for Player model."""

    def registrations_by_month(self):
        """Returns the number of player registrations grouped by month."""
        return (
            self.annotate(month=TruncMonth('user__date_joined'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )


class PlayerManager(models.Manager):
    def get_queryset(self):
        return PlayerQuerySet(self.model, using=self._db)

    def registrations_by_month(self):
        return self.get_queryset().registrations_by_month()


class Player(models.Model):
    """Player model."""

    user = models.OneToOneField(
        User,
        related_name='player',
        verbose_name=_('User tied to player'),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    gender = models.CharField(
        verbose_name=_('Gender'),
        max_length=PlayerIntEnums.GENDER_MAX_LENGTH.value,
        choices=Genders.choices,
        blank=False,
        default=PlayerStrEnums.DEFAULT_GENDER.value,
    )
    avatar = models.ImageField(
        verbose_name=_('Avatar'),
        upload_to='players/avatars/',
        null=True,
        blank=True,
        default=None,
    )
    date_of_birth = models.DateField(
        default=PlayerStrEnums.DEFAULT_BIRTHDAY.value,
        validators=[validate_birthday],
        blank=False,
        null=False,
    )
    country = models.ForeignKey(
        Country,
        related_name='players',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Country of player'),
    )
    city = models.ForeignKey(
        City,
        related_name='players',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('City of player'),
    )
    is_registered = models.BooleanField(
        verbose_name=_('Status of player registration in app'),
        default=False,
        null=False,
    )
    objects = PlayerManager()

    class Meta:
        verbose_name = _('Player')
        verbose_name_plural = _('Players')

    def __str__(self):
        return f'Player {self.user.first_name} {self.user.last_name}'

    def clean(self):
        super().clean()
        if self.date_of_birth:
            if not isinstance(self.date_of_birth, date):
                raise ValidationError(
                    {'date_of_birth': _('Invalid date format.')}
                )
            if self.date_of_birth > timezone.now().date():
                raise ValidationError(
                    {'date_of_birth': _('Birthday cannot be in the future')}
                )

    def was_active_recently(self, days=PlayerIntEnums.PLAYER_INACTIVE_DAYS):
        """
        Checks if the player was active in the last N days.
        Returns True if the player participated in any games in last 60 days.
        """
        return Game.objects.filter(
            players=self, end_time__gte=timezone.now() - timedelta(days=days)
        ).exists()

    def get_players_to_rate(self, event: Game | Tourney):
        """
        Returns a QuerySet of players whom rater_player can still rate
        (not more than 2 ratings in the last 2 months).
        """

        period_start = timezone.now() - timedelta(
            days=PlayerIntEnums.RATING_PERIOD_DAYS
        )

        return (
            event.players.exclude(id=self.id)
            .annotate(
                votes_from_me=models.Count(
                    'received_ratings',
                    filter=models.Q(
                        received_ratings__rater=self,
                        received_ratings__created_at__gte=period_start,
                    ),
                )
            )
            .filter(votes_from_me__lt=PlayerIntEnums.PLAYER_VOTE_LIMIT.value)
        )


class Payment(models.Model):
    """Players payment model."""

    player = models.ForeignKey(
        Player,
        related_name='payments',
        verbose_name=_('Player - owner of payment'),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    payment_type = models.CharField(
        verbose_name=_('Type of payment'),
        max_length=PlayerIntEnums.PAYMENT_MAX_LENGTH.value,
        choices=Payments.choices,
        blank=False,
    )
    payment_account = models.CharField(
        verbose_name=_('Payment account of player'),
        max_length=PlayerIntEnums.PAYMENT_MAX_LENGTH.value,
        default=None,
        null=True,
        blank=True,
    )
    is_preferred = models.BooleanField(
        verbose_name=_('Players preferable payment type'),
        null=False,
        blank=False,
        default=False,
    )

    def __str__(self) -> str:
        return f'Payment data of {self.player}, type: {self.payment_type}'


class Favorite(models.Model):
    """Model of favorite players."""

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='player',
        verbose_name=_('Player'),
    )
    favorite = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='favorite',
        verbose_name=_('Players favorite'),
    )

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['player', 'favorite'], name='unique_player_favorite'
            )
        ]
        verbose_name = _('Favorite')
        verbose_name_plural = _('Favorites')

    def __str__(self) -> str:
        return f'{self.player} has {self.favorite} in favorite list'


class PlayerRating(models.Model):
    """Player rating model."""

    player = models.OneToOneField(
        Player,
        related_name='rating',
        verbose_name=_('Player'),
        on_delete=models.CASCADE,
    )
    grade = models.CharField(
        verbose_name=_('Grade of the player'),
        choices=Grades.choices,
        default=PlayerStrEnums.DEFAULT_GRADE.value,
    )
    level_mark = models.PositiveSmallIntegerField(
        verbose_name=_('Level mark of the player'),
        choices=LevelMarkChoices.choices,
        default=LevelMarkChoices.TWO.value,
    )
    value = models.SmallIntegerField(
        verbose_name=_('Change in rating'),
        default=PlayerIntEnums.DEFAULT_RATING,
    )
    updated_at = models.DateTimeField(
        verbose_name=_('Date of rating update'),
        auto_now=True,
    )

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Player rating')
        verbose_name_plural = _('Players ratings')

    def __str__(self) -> str:
        return f'Rating {self.grade} of {self.player} at {self.updated_at}'


class PlayerRatingVote(models.Model):
    """
    Model for storing player-to-player rating votes.

    Each vote is given by one player to another and affects the rated
    player's rating. A player can rate another player no more than 2 times
    within 2 months.
    Used for rating calculations and level/grade progression.
    """

    rater = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='given_ratings',
        verbose_name=_('Player who gives the rating'),
    )
    rated = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='received_ratings',
        verbose_name=_('Player who receives the rating'),
    )
    value = models.FloatField(verbose_name=_('Rating value'))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Date of rating vote creation')
    )
    is_counted = models.BooleanField(
        default=False, verbose_name=_('Is vote counted in rating calculation')
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        related_name='rating_votes',
        verbose_name=_('Game where the rating vote was made'),
        null=True,
        blank=True,
    )
    tourney = models.ForeignKey(
        'event.Tourney',
        on_delete=models.SET_NULL,
        related_name='rating_votes',
        verbose_name=_('Tourney where the rating vote was made'),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Player rating vote')
        verbose_name_plural = _('Player rating votes')
        constraints = [
            models.UniqueConstraint(
                fields=['rater', 'rated', 'game'],
                name='unique_rating_vote_per_game',
                condition=models.Q(game__isnull=False),
            ),
            models.UniqueConstraint(
                fields=['rater', 'rated', 'tourney'],
                name='unique_rating_vote_per_tourney',
                condition=models.Q(tourney__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        return (
            f'Vote {self.value} from {self.rater} to {self.rated} '
            f'on {self.created_at}'
        )
