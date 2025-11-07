from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.event.enums import EventIntEnums
from apps.event.models import Game, GameInvitation, Tourney, TourneyTeam
from apps.event.permissions import IsHostOrReadOnly, IsPlayerOrReadOnly
from apps.event.serializers import (
    GameDetailSerializer,
    GameInviteSerializer,
    GameSerializer,
    GameShortSerializer,
    TourneyDetailSerializer,
    TourneySerializer,
    TourneyShortSerializer,
)
from apps.event.utils import procces_rate_players_request


class InvitePlayersMixin:
    @action(
            methods=['post'],
            detail=True,
            url_path='invite-players',
            permission_classes=[IsAuthenticated,]
        )
    def invite_players(self, request, *args, **kwargs):
        """
        Creates invitations to the game/tournament for players on the list.
        """
        obj = self.get_object()
        host_id = request.user.player.id
        content_type = ContentType.objects.get_for_model(obj.__class__)
        invited_list = request.data.get('players')
        if invited_list:
            for invited in request.data['players']:
                serializer = self.get_serializer(
                    data={
                        'host': host_id,
                        'invited': invited,
                        "content_type": content_type.id,
                        "object_id": obj.id
                    },
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(
            data={'players': 'Must be a list of players id'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['delete'],
        detail=True,
        url_path='invites',
        permission_classes=[IsAuthenticated,]
    )
    def delete_invitation(self, request, *args, **kwargs):
        event = self.get_object()
        player = request.user.player
        delete_count, dt = event.event_invites.filter(invited=player).delete()
        if not delete_count:
            return Response(
                data={'error': _('The invitation does not exist!')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class RatePlayersMixin:

    @action(
        methods=['get', 'post'],
        detail=True,
        url_path='rate-players',
        permission_classes=[IsPlayerOrReadOnly]
    )
    def rate_players(self, request, *args, **kwargs):
        """
        Allows a player to rate other players in a game.
        POST: Submits ratings for the specified players.
        GET: Retrieves a list of players available for rating.
        """
        return procces_rate_players_request(self, request, *args, **kwargs)


class GameViewSet(GenericViewSet,
                  CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin,
                  InvitePlayersMixin,
                  RatePlayersMixin):
    """Provides CRUD operations for the Game model."""
    permission_classes = (IsHostOrReadOnly,)
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        player = getattr(self.request.user, 'player', None)
        if (player is None or
                player.country is None or
                self.action in ('joining_game', 'delete_invitation')):
            return Game.objects.all().select_related(
                'host', 'court').prefetch_related('players')
        return Game.objects.player_located_games(player).select_related(
            'host', 'court').prefetch_related('players')

    def get_serializer_class(self, *args, **kwargs):
        if self.action in (
                'retrieve',
                'joining_game'):
            return GameDetailSerializer

        elif self.action == 'invite_players':
            return GameInviteSerializer

        elif self.action in (
                'my_games',
                'archive_games',
                'invited_games',
                'upcoming_games'):
            return GameShortSerializer
        else:
            return GameSerializer

    @action(
        methods=['get'],
        detail=False,
        url_path='preview'
    )
    def preview(self, request, *args, **kwargs):
        """Returns the time of the next game and the number of invitations."""

        upcoming_game = Game.objects.nearest_game(request.user.player)
        upcoming_tourney = Tourney.objects.nearest_game(request.user.player)
        nearest_event_time_list = sorted([
            obj.start_time for obj in (
                upcoming_game, upcoming_tourney) if obj])
        if len(nearest_event_time_list) == 0:
            upcoming_game_time = None
        else:
            upcoming_game_time = nearest_event_time_list[0]

        invites = GameInvitation.objects.count_events(request.user.player)
        return Response(
            data={'upcoming_game_time': upcoming_game_time,
                  'invites': invites}, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='my-games'
    )
    def my_games(self, request, *args, **kwargs):
        """Retrieves the list of games created by the user."""

        my_games = Game.objects.my_upcoming_games(request.user.player)
        game_serializer = self.get_serializer(my_games, many=True)

        my_tourneys = Tourney.objects.my_upcoming_games(request.user.player)
        tourney_serializer = TourneyShortSerializer(my_tourneys, many=True)
        wrapped_data = {'games': game_serializer.data,
                        'tournaments': tourney_serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='archive'
    )
    def archive_games(self, request, *args, **kwargs):
        """Retrieves the list of archived games related to user."""

        archived_games = Game.objects.archive_games(request.user.player)
        game_serializer = self.get_serializer(archived_games, many=True)

        archived_tourneys = Tourney.objects.archive_games(request.user.player)
        tourney_serializer = TourneyShortSerializer(
            archived_tourneys, many=True)

        wrapped_data = {'games': game_serializer.data,
                        'tournaments': tourney_serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='invites'
    )
    def invited_games(self, request, *args, **kwargs):
        """Retrieving upcoming games to which the player has been invited."""

        invited_games = Game.objects.invited_games(request.user.player)
        game_serializer = self.get_serializer(invited_games, many=True)

        archived_tourneys = Tourney.objects.invited_games(request.user.player)
        tourney_serializer = TourneyShortSerializer(
            archived_tourneys, many=True
        )

        wrapped_data = {'games': game_serializer.data,
                        'tournaments': tourney_serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='upcoming'
    )
    def upcoming_games(self, request, *args, **kwargs):
        """Retrieving upcoming games that the player participates in."""

        upcomming_games = Game.objects.upcomming_games(request.user.player)
        game_serializer = self.get_serializer(upcomming_games, many=True)

        archived_tourneys = Tourney.objects.upcomming_games(
            request.user.player
        )
        tourney_serializer = TourneyShortSerializer(
            archived_tourneys, many=True
        )

        wrapped_data = {'games': game_serializer.data,
                        'tournaments': tourney_serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['post'],
        detail=True,
        url_path='join-game',
        permission_classes=[IsAuthenticated]
    )
    def joining_game(self, request, *args, **kwargs):
        """Adding a user to the game and removing the invitation."""

        game = self.get_object()
        player = request.user.player
        if game.max_players > game.players.count():
            is_joined = {'is_joined': True}
            game.players.add(player)
            game.event_invites.filter(invited=player).delete()
        else:
            is_joined = {'is_joined': False}
        serializer = self.get_serializer(
            game, context={'request': request})
        data = serializer.data.copy()
        data.update(is_joined)
        return Response(data=data, status=status.HTTP_200_OK)


class TourneyViewSet(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    InvitePlayersMixin,
    RatePlayersMixin
):
    """CRUD for tournaments."""
    permission_classes = (IsHostOrReadOnly,)
    http_method_names = ['get', 'post', 'delete']
    queryset = Tourney.objects.all()

    def get_queryset(self):
        player = getattr(self.request.user, 'player', None)
        if player is None or player.country is None:
            return Tourney.objects.all().select_related(
                'host', 'court').prefetch_related('teams', 'teams__players')
        return Tourney.objects.filter(
            court__location__country=player.country
        ).select_related('host', 'court'
                         ).prefetch_related('teams', 'teams__players')

    def get_serializer_class(self):
        if self.action in ('retrieve', 'joining_tournament'):
            return TourneyDetailSerializer
        elif self.action == 'invite_players':
            return GameInviteSerializer
        return TourneySerializer

    @action(
        methods=['post'],
        detail=True,
        url_path='join-tournament',
        permission_classes=[IsAuthenticated]
    )
    def joining_tournament(self, request, *args, **kwargs):
        """Adding a user to the tourney and removing the invitation."""

        tourney = self.get_object()
        player = request.user.player
        team_id = request.data.get('team_id')
        team = TourneyTeam.objects.filter(pk=team_id, tourney=tourney).first()
        capacity = EventIntEnums.TOURNEY_TEAM_CAPACITY.value
        if not team:
            return Response(
                data={'team_id': 'This team is not exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif TourneyTeam.objects.filter(
                tourney=tourney, players=player).exists():
            return Response(
                data={
                    'team_id': (
                        'The player is already participate in tournament.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif (
            (tourney.is_individual and
             tourney.max_players > team.players.count()) or
            (not tourney.is_individual and
             capacity > team.players.count())
        ):
            is_joined = {'is_joined': True}
            team.players.add(player)
            tourney.event_invites.filter(invited=player).delete()
        else:
            is_joined = {'is_joined': False}
        serializer = self.get_serializer(
            tourney, context={'request': request})
        data = serializer.data.copy()
        data.update(is_joined)
        return Response(data=data, status=status.HTTP_200_OK)

    # @action(methods=['get'], detail=False, url_path='my-tournaments')
    # def my_tournaments(self, request, *args, **kwargs):
    #     """List of tournaments created by the current user."""
    #     tournaments = Tourney.objects.filter(host=request.user.player)
    #     serializer = self.get_serializer(tournaments, many=True)
    #     return Response(
    # {'tournaments': serializer.data}, status=status.HTTP_200_OK)

    # @action(methods=['get'], detail=False, url_path='archive')
    # def archive(self, request, *args, **kwargs):
    #     """List of past tournaments (already finished)."""
    #     tournaments = Tourney.objects.filter(end_time__lte=timezone.now())
    #     serializer = self.get_serializer(tournaments, many=True)
    #     return Response(
    # {'tournaments': serializer.data}, status=status.HTTP_200_OK)

    # @action(methods=['get'], detail=False, url_path='upcoming')
    # def upcoming(self, request, *args, **kwargs):
    #     """List of upcoming tournaments (not started yet)."""
    #     tournaments = Tourney.objects.filter(
    #         players=request.user.player,
    #         start_time__gte=timezone.now()
    #     )
    #     serializer = self.get_serializer(tournaments, many=True)
    #     return Response(
    # {'tournaments': serializer.data}, status=status.HTTP_200_OK)

    # @action(
    #     methods=['post'],
    #     detail=True,
    #     url_path='join-tournament',
    #     permission_classes=[IsAuthenticated],
    # )
    # def join_tournament(self, request, *args, **kwargs):
    #     """Join the tournament as a player."""
    #     tourney = self.get_object()
    #     player = request.user.player
    #     if tourney.max_players > tourney.players.count():
    #         tourney.players.add(player)
    #         is_joined = True
    #     else:
    #         is_joined = False
    #     serializer = self.get_serializer(
    # tourney, context={'request': request})
    #     data = serializer.data.copy()
    #     data.update({'is_joined': is_joined})
    #     return Response(data, status=status.HTTP_200_OK)
