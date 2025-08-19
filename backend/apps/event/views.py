from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.models import GameInvitation

from .models import Game
from .permissions import IsHostOrReadOnly
from .serializers import (
    GameDetailSerializer,
    GameInviteSerializer,
    GameSerializer,
    ShortGameSerializer
)

User = get_user_model()


class GameViewSet(ModelViewSet):
    '''Provides CRUD operations for the Game model.'''
    queryset = Game.objects.all()
    permission_classes = (IsHostOrReadOnly,)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GameDetailSerializer
        else:
            return GameSerializer

    def perform_create(self, serializer):
        game = serializer.save(
            host=self.request.user)
        game.players.add(self.request.user)

    @action(
        methods=['post'],
        detail=True,
        url_path='invite-players',
    )
    def invite_players(self, request, *args, **kwargs):
        '''Создает приглашения на игру для игроков из списка.'''
        game = self.get_object().id
        user = request.user.id
        for id in request.data['players']:
            serializer = GameInviteSerializer(
                    data={
                        'host': user,
                        'invited': id,
                        'game': game
                    }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(
        methods=['get'],
        detail=False,
        url_path='preview',
    )
    def preview(self, request, *args, **kwargs):
        '''Returns the time of the next game and the number of invitations.'''
        user = request.user
        current_time = now()
        upcoming_game = Game.objects.filter(
            Q(host=user) | Q(players=user)
        ).filter(start_time__gt=current_time).order_by('start_time').first()
        upcoming_game_time = upcoming_game.start_time.strftime(
            '%Y-%m-%d %H:%M')
        invites = GameInvitation.objects.filter(
            invited=user).values('game').distinct().count()
        return Response(
                data={'upcoming_game_time': upcoming_game_time,
                      'invites': invites}, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        url_path='my-games',
    )
    def my_games(self, request, *args, **kwargs):
        '''Retrieves the list of games created by the user.'''
        user = request.user
        my_games = Game.objects.filter(host=user)
        serializer = ShortGameSerializer(my_games, many=True)
        wrapped_data = {'games': serializer.data}
        return Response(data=wrapped_data, status=status.HTTP_200_OK)
