from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.event.models import Game, GameInvitation, Tourney
from apps.event.permissions import IsHostOrReadOnly
from apps.event.serializers import (
    GameDetailSerializer,
    GameInviteSerializer,
    GameSerializer,
    GameShortSerializer, TourneySerializer, TourneyShortSerializer, TourneyDetailSerializer,
)


class GameViewSet(GenericViewSet,
                  CreateModelMixin,
                  RetrieveModelMixin,
                  DestroyModelMixin):
    """Provides CRUD operations for the Game model."""
    permission_classes = (IsHostOrReadOnly, IsAuthenticated)
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
                'archive',
                'invites',
                'upcoming'):
            return GameShortSerializer
        else:
            return GameSerializer

    @action(
        methods=['post'],
        detail=True,
        url_path='invite-players',
    )
    def invite_players(self, request, *args, **kwargs):
        """Creates invitations to the game for players on the list."""
        game_id = self.get_object().id
        host_id = request.user.player.id
        for id in request.data['players']:
            serializer = self.get_serializer(
                data={
                    'host': host_id,
                    'invited': id,
                    'game': game_id
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(
        methods=['get'],
        detail=False,
        url_path='preview'
    )
    def preview(self, request, *args, **kwargs):
        """Returns the time of the next game and the number of invitations."""

        upcoming_game = Game.objects.nearest_game(request.user.player)
        if upcoming_game is not None:
            upcoming_game_time = upcoming_game.start_time
        else:
            upcoming_game_time = None
        invites = GameInvitation.objects.filter(
            invited=request.user.player).values('game').distinct().count()
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
        serializer = self.get_serializer(my_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='archive'
    )
    def archive_games(self, request, *args, **kwargs):
        """Retrieves the list of archived games related to user."""

        archived_games = Game.objects.archive_games(request.user.player)
        serializer = self.get_serializer(archived_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='invites'
    )
    def invited_games(self, request, *args, **kwargs):
        """Retrieving upcoming games to which the player has been invited."""

        invited_games = Game.objects.invited_games(request.user.player)
        serializer = self.get_serializer(invited_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='upcoming'
    )
    def upcoming_games(self, request, *args, **kwargs):
        """Retrieving upcoming games that the player participates in."""

        upcomming_games = Game.objects.upcomming_games(request.user.player)
        serializer = self.get_serializer(upcomming_games, many=True)
        wrapped_data = {'games': serializer.data}
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
            GameInvitation.objects.filter(
                Q(game=game) & Q(invited=player)).delete()
        else:
            is_joined = {'is_joined': False}
        serializer = self.get_serializer(
            game, context={'request': request})
        data = serializer.data.copy()
        data.update(is_joined)
        return Response(data=data, status=status.HTTP_200_OK)

    @action(
        methods=['delete'],
        detail=True,
        url_path='invites',
        permission_classes=[IsAuthenticated]
    )
    def delete_invitation(self, request, *args, **kwargs):
        game = self.get_object()
        player = request.user.player
        delete_count, dt = GameInvitation.objects.filter(
            Q(game=game) & Q(invited=player)).delete()
        if not delete_count:
            return Response(
                data={'error': _('The invitation does not exist!')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TourneyViewSet(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin
):
    """CRUD for tournaments."""
    permission_classes = (IsHostOrReadOnly, IsAuthenticated)
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        player = getattr(self.request.user, 'player', None)
        if player is None or player.country is None:
            return Tourney.objects.all().select_related(
                'host', 'court').prefetch_related('players')
        return Tourney.objects.filter(
            court__location__country=player.country
        ).select_related('host', 'court').prefetch_related('players')

    def get_serializer_class(self):
        if self.action in ('retrieve', 'join_tournament'):
            return TourneyDetailSerializer
        elif self.action in ('my_tournaments', 'archive', 'invites', 'upcoming'):
            return TourneyShortSerializer
        else:
            return TourneySerializer

    @action(methods=['get'], detail=False, url_path='my-tournaments')
    def my_tournaments(self, request, *args, **kwargs):
        """List of tournaments created by the current user."""
        tournaments = Tourney.objects.filter(host=request.user.player)
        serializer = self.get_serializer(tournaments, many=True)
        return Response({'tournaments': serializer.data}, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='archive')
    def archive(self, request, *args, **kwargs):
        """List of past tournaments (already finished)."""
        tournaments = Tourney.objects.filter(end_time__lte=timezone.now())
        serializer = self.get_serializer(tournaments, many=True)
        return Response({'tournaments': serializer.data}, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, url_path='upcoming')
    def upcoming(self, request, *args, **kwargs):
        """List of upcoming tournaments (not started yet)."""
        tournaments = Tourney.objects.filter(
            players=request.user.player,
            start_time__gte=timezone.now()
        )
        serializer = self.get_serializer(tournaments, many=True)
        return Response({'tournaments': serializer.data}, status=status.HTTP_200_OK)

    @action(
        methods=['post'],
        detail=True,
        url_path='join-tournament',
        permission_classes=[IsAuthenticated],
    )
    def join_tournament(self, request, *args, **kwargs):
        """Join the tournament as a player."""
        tourney = self.get_object()
        player = request.user.player
        if tourney.max_players > tourney.players.count():
            tourney.players.add(player)
            is_joined = True
        else:
            is_joined = False
        serializer = self.get_serializer(tourney, context={'request': request})
        data = serializer.data.copy()
        data.update({'is_joined': is_joined})
        return Response(data, status=status.HTTP_200_OK)
