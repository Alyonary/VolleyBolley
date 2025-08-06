from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import Game
from .serializers import GameCreateSerializer, GameResponseSerializer


class GameViewSet(viewsets.ModelViewSet):
    """CRUD для игр."""
    queryset = Game.objects.all()

    # permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return (
            GameCreateSerializer
            if self.action == 'create' else GameResponseSerializer
        )

    @swagger_auto_schema(
        operation_description='Создать новую игру',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=[
                'message', 'start_time', 'end_time', 'court', 'gender',
                'levels', 'maximum_players', 'price_per_person',
                'payment_type', 'payment_account', 'is_private'
            ],
            properties={
                'message': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Описание/сообщение',
                    example='Играем в 20:00. Все приходим заранее!'
                ),
                'start_time': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='date-time',
                    description='Дата-время начала (ISO 8601)',
                    example='2025-07-28T19:45:00Z'
                ),
                'end_time': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='date-time',
                    description='Дата-время окончания (ISO 8601)',
                    example='2025-07-28T21:00:00Z'
                ),
                'court': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID площадки',
                    example=1
                ),
                'gender': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Пол участников (MEN/WOMEN/MIXED)',
                    example='MEN'
                ),
                'levels': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='Список уровней (slug-и, например PRO)',
                    example=['PRO']
                ),
                'maximum_players': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='Максимальное число игроков',
                    example=8
                ),
                'price_per_person': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    format='decimal',
                    description='Стоимость с человека',
                    example=5.0
                ),
                'payment_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Тип оплаты (например REVOLUT, CASH)',
                    example='REVOLUT'
                ),
                'payment_account': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Реквизиты/комментарий к оплате',
                    example='1234?'
                ),
                'is_private': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description='Приватная игра',
                    example=False
                ),
                'players': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description='ID игроков, которые сразу участвуют',
                    example=[2, 3]
                ),
            }
        ),
        responses={201: GameResponseSerializer}
    )
    def create(self, request, *args, **kwargs):
        """Создаёт игру и сразу возвращает JSON."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        game = serializer.save()
        resp_data = GameResponseSerializer(
            game,
            context={'request': request},
        ).data
        headers = self.get_success_headers(resp_data)
        return Response(
            resp_data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
