from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models as m
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from apps.core.mixins.created_updated import CreatedUpdatedMixin
from apps.event.enums import EventIntEnums
from apps.event.mixins import EventMixin


class GameQuerySet(m.query.QuerySet):

    def player_located_games(self, player):
        country = getattr(player, 'country', None)
        city = getattr(player, 'city', None)
        if country is None or city is None:
            return self
        elif player.country.name == 'Cyprus':
            return self.filter(
                court__location__country=player.country)
        elif player.country.name == 'Thailand':
            return self.filter(court__location__city=player.city)
        return self

    def player_related_games(self, player):
        return self.player_located_games(player).filter(
            (m.Q(host=player) | m.Q(players=player))).distinct()

    def future_games(self):
        current_time = now()
        return self.filter(
            start_time__gt=current_time).order_by('start_time')

    def invited_games(self, player):
        return self.player_located_games(
            player).future_games().filter(
                event_invites__invited=player)

    def upcomming_games(self, player):
        return self.player_related_games(player).future_games()

    def my_upcoming_games(self, player):
        return self.upcomming_games(player).filter(host=player)

    def nearest_game(self, player):
        return self.upcomming_games(player).first()

    def archive_games(self, player):
        current_time = now()
        return self.player_related_games(
            player).filter(
            start_time__lt=current_time).order_by(
                '-end_time')


class TourneyQuerySet(GameQuerySet):

    def player_related_games(self, player):
        return self.player_located_games(player).filter(
            (m.Q(host=player) | m.Q(teams__players=player))).distinct()


class EventInvitesManager(m.Manager):
    def count_events(self, player):
        """
        The method retrieves the number of events which the player was invited.

        Parameters:
        - player: Player object.

        Returns:
        The number of unique objects (games and tournaments)
        for which the player has received invitations.
        """
        distinct_invites = self.filter(
            invited=player).values(
                'content_type', 'object_id').distinct().count()

        return distinct_invites


class GameManager(m.Manager):

    def get_queryset(self):
        return GameQuerySet(self.model, using=self._db)

    def player_located_games(self, player):
        """Basic queryset for games.

        Returns games from the same country as the player,
        if the player is from Cyprus.
        Returns games from the same city as the player,
        if the player is from Thailand.
        If the player's city and country are not specified,
        it returns all games.
        """
        return self.get_queryset().player_located_games(player)

    def player_related_games(self, player):
        """Returns games in which the user is a host or player."""
        return self.get_queryset().player_related_games(player)

    def invited_games(self, player):
        """Returns games in which the user was invited."""
        return self.get_queryset().invited_games(player)

    def upcomming_games(self, player):
        """Returns upcoming games in which the user is a host or player."""
        return self.get_queryset().upcomming_games(player)

    def my_upcoming_games(self, player):
        """Returns upcoming games in which the user is a host."""
        return self.get_queryset().my_upcoming_games(player)

    def archive_games(self, player):
        """Returns past games in which the user is a host or player."""
        return self.get_queryset().archive_games(player)

    def nearest_game(self, player):
        """Returns nearest upcoming game where user is a host or player."""
        return self.get_queryset().nearest_game(player)


class TourneyManager(GameManager):

    def get_queryset(self):
        return TourneyQuerySet(self.model, using=self._db)


class GameInvitation(m.Model):
    """Invitation to game or tourney model."""

    host = m.ForeignKey(
        'players.Player',
        on_delete=m.CASCADE,
        related_name='invite_host'
    )

    invited = m.ForeignKey(
        'players.Player',
        on_delete=m.CASCADE,
        related_name='invited'
    )
    content_type = m.ForeignKey(
        ContentType,
        on_delete=m.CASCADE
    )
    object_id = m.PositiveBigIntegerField()

    content_object = GenericForeignKey(
        "content_type",
        "object_id"
    )
    objects = EventInvitesManager()

    class Meta:
        verbose_name = _('Game invitation')
        verbose_name_plural = _('Game invitations')

    def __str__(self):
        discription = str(_(
            f'Invitation in {self.content_object.id} for {self.invited}'))
        return discription


class Game(EventMixin, CreatedUpdatedMixin):
    """Game model."""
    host = m.ForeignKey(
        'players.Player',
        verbose_name=_('Game organizer'),
        on_delete=m.CASCADE,
        related_name='games_host'
    )
    players = m.ManyToManyField(
        'players.Player',
        verbose_name=_('Players'),
        related_name='games_players',
        blank=True
    )
    objects = GameManager()

    def __str__(self):
        name = (
            f'{self.id}, '
            f'{self.court.location.court_name}, '
            f'{self.message}, '
            f'time: {self.start_time}'
            f'host: {self.host}, '
        )
        return name[:EventIntEnums.STR_MAX_LEN.value]

    class Meta:
        verbose_name = _('Game')
        verbose_name_plural = _('Games')
        default_related_name = 'games'


class Tourney(EventMixin, CreatedUpdatedMixin):
    """Tourney model."""

    host = m.ForeignKey(
        'players.Player',
        verbose_name=_('Tourney organizer'),
        on_delete=m.SET_NULL,
        null=True,
        blank=True,
        related_name='tournaments_host',
    )
    is_individual = m.BooleanField(
        verbose_name=_('Individual format')
    )
    maximum_teams = m.PositiveIntegerField(
        verbose_name=_('Maximum of teams'),
        blank=True,
        null=False
    )
    objects = TourneyManager()

    @property
    def players(self):
        """
        Returns a qs of players in the tourney via related TourneyTeam.
        """
        from apps.players.models import Player

        return Player.objects.filter(
            tourney_players__tourney=self
        ).distinct()

    class Meta:
        verbose_name = _('Tourney')
        verbose_name_plural = _('Tourneys')
        default_related_name = 'tournaments'

    def __str__(self):
        name = (
            f'{self.id}, '
            f'{self.court.location.court_name}, '
            f'{self.message}, '
            f'time: {self.start_time}'
            f'host: {self.host}, '
        )
        return name[:EventIntEnums.STR_MAX_LEN.value]


class TourneyTeam(m.Model):

    tourney = m.ForeignKey(
        'event.Tourney',
        verbose_name=_('Tourney is from'),
        on_delete=m.CASCADE
        )
    players = m.ManyToManyField(
        'players.Player',
        verbose_name=_('Players'),
        related_name='tourney_players',
        blank=True
    )

    class Meta:
        verbose_name = _('Tourney team')
        verbose_name_plural = _('Tourney teams')
        default_related_name = 'teams'

    def __str__(self):
        name = (
            f'Team #{self.id}, of '
            f'{self.tourney} tourney'
        )
        return name[:EventIntEnums.STR_MAX_LEN.value]
