from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from .models import Game
from .serializers import GameCreateSerializer, GameDetailSerializer


class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.all()

    # permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        serializer_action_classes = {
            'create': GameCreateSerializer,
            'list': GameDetailSerializer,
            'retrieve': GameDetailSerializer,
        }
        return serializer_action_classes.get(self.action, GameDetailSerializer)

    @swagger_auto_schema(
        operation_description='Создать новую игру',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                'title', 'message', 'date', 'start_time', 'end_time',
                'court', 'gender', 'player_levels', 'max_players',
                'price_per_person', 'payment_type', 'payment_value',
                'is_private', 'players'
            ],
            properties={
                'title': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Название игры',
                    example='Вечерний матч'
                ),
                'message': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Описание/сообщение',
                    example='Играем в 20:00. Все приходим заранее!'
                ),
                'date': openapi.Schema(
                    type=openapi.TYPE_STRING, format='date-time',
                    description='Дата и время (ISO 8601)',
                    example='2025-07-28T19:45:00Z'
                ),
                'start_time': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='time',
                    description='Время начала (HH:MM)',
                    example='19:45:00'
                ),
                'end_time': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='time',
                    description='Время окончания (HH:MM)',
                    example='21:00:00'
                ),
                'court': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID площадки',
                    example=1
                ),
                'gender': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID пола участников',
                    example=1
                ),
                'player_levels': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description='Список ID уровней (справочник)',
                    example=[1, 2]
                ),
                'max_players': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Максимальное число игроков',
                    example=8
                ),
                'price_per_person': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format='decimal',
                    description='Стоимость с человека',
                    example=3.0
                ),
                'payment_type': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID типа оплаты',
                    example=1),
                'payment_value': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Комментарий к оплате',
                    example='Наличными'
                ),
                'tag_list': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description='Список ID тегов',
                    example=[1, 2]
                ),
                'is_private': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Приватная игра',
                    example=False
                ),
                'players': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description='ID игроков, которые участвуют в игре',
                    example=[2, 3]
                ),
            }
        )
    )
    def create(self, request, *args, **kwargs):
        """Создать новую игру."""
        return super().create(request, *args, **kwargs)
