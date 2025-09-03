from django.db.models import Q
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.event.models import Game, GameInvitation
from apps.event.permissions import IsHostOrReadOnly
from apps.event.serializers import (
    GameDetailSerializer,
    GameInviteSerializer,
    GameSerializer,
    GameShortSerializer,
)


class GameViewSet(ModelViewSet):
    """Provides CRUD operations for the Game model."""
    permission_classes = (IsHostOrReadOnly, IsAuthenticated)

    def get_queryset(self):
        if self.action in ('list', 'retrieve'):
            player = getattr(self.request.user, 'player', None)
            if player is None or player.country is None:
                return Game.objects.all()
            return Game.objects.filter(
                court__location__country=player.country, is_private=False)
        else:
            return Game.objects.all()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GameDetailSerializer
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
            serializer = GameInviteSerializer(
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
        player = request.user.player
        current_time = now()
        upcoming_game = Game.objects.filter(
            Q(host=player) | Q(players=player)
        ).filter(start_time__gt=current_time).order_by('start_time').first()
        if upcoming_game is not None:
            upcoming_game_time = upcoming_game.start_time.strftime(
                format='iso-8601')
        else:
            upcoming_game_time = None
        invites = GameInvitation.objects.filter(
            invited=player).values('game').distinct().count()
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
        current_time = now()
        my_games = Game.objects.filter(
            host=request.user.player).filter(
                start_time__gt=current_time).select_related('host', 'court')
        serializer = GameShortSerializer(my_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='archive'
    )
    def archive_games(self, request, *args, **kwargs):
        """Retrieves the list of archived games related to user."""
        current_time = now()
        my_games = Game.objects.filter(end_time__lt=current_time).filter(
            Q(host=request.user.player) | Q(players=request.user.player)
        ).select_related('host', 'court')
        serializer = GameShortSerializer(my_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='invites'
    )
    def invited_games(self, request, *args, **kwargs):
        """Retrieving upcoming games to which the player has been invited."""
        my_invitations = GameInvitation.objects.filter(
            invited=request.user.player).select_related('game')
        current_time = now()
        my_games = [
            invitation.game
            for invitation in my_invitations
            if invitation.game.start_time > current_time
        ]
        serializer = GameShortSerializer(my_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='upcoming'
    )
    def upcoming_games(self, request, *args, **kwargs):
        """Retrieving upcoming games to which the player has been invited."""
        current_time = now()
        my_games = Game.objects.filter(start_time__gt=current_time).filter(
            Q(host=request.user.player) | Q(players=request.user.player)
        ).select_related('host', 'court')
        serializer = GameShortSerializer(my_games, many=True)
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
        invitation = GameInvitation.objects.filter(
            Q(game=game) & Q(invited=player)).first()
        if invitation is not None and game.max_players > game.players.count():
            is_joined = {'is_joined': True}
            game.players.add(player)
            invitation.delete()
        else:
            is_joined = {'is_joined': False}
        serializer = GameDetailSerializer(game, context={'request': request})
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
