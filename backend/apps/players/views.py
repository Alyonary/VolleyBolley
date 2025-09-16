from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.core.permissions import IsNotRegisteredPlayer, IsRegisteredPlayer
from apps.players.models import Favorite, Payment, Player
from apps.players.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    PaymentSerializer,
    PaymentsSerializer,
    PlayerBaseSerializer,
    PlayerListSerializer,
    PlayerRegisterSerializer,
)
from apps.users.models import User


class PlayerViewSet(ReadOnlyModelViewSet):

    queryset = Player.objects.all()
    serializer_class = PlayerBaseSerializer
    http_method_names = ['get', 'post', 'patch', 'put', 'delete']
    permission_classes = [IsRegisteredPlayer]

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "me":
            return PlayerBaseSerializer
        elif self.action == 'put_delete_avatar':
            return AvatarSerializer
        elif self.action == 'register':
            return PlayerRegisterSerializer
        elif self.action == 'get_put_payments':
            if self.request.method == 'GET':
                return PaymentsSerializer
            return PaymentSerializer
        elif self.action == 'list':
            return PlayerListSerializer
        elif self.action == 'favorite':
            return FavoriteSerializer
        return super().get_serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({
            'player': self.queryset.get(user=self.request.user),
            'current_user': self.request.user
        })
        return context

    def get_queryset(self):
        queryset = self.queryset
        if self.action != 'register':
            queryset = queryset.exclude(is_registered=False)

        if self.action == 'get_put_payments':
            player = self.request.user.player
            if player.is_registered:
                return Payment.objects.filter(player=self.request.user.player)

            return None

        if self.action == 'list':
            queryset = queryset.exclude(user=self.request.user)

        return queryset

    def get_object(self):
        if self.action in ['me', 'register', 'put_delete_avatar', 'favorite']:
            obj = get_object_or_404(
                self.queryset.filter(user=self.request.user)
            )
            self.check_object_permissions(self.request, obj)

            return obj

        return super().get_object()

    @swagger_auto_schema(
        tags=['players'],
        operation_summary="List all players excluding current user",
        responses={200: PlayerListSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        method='get',
        responses={200: PlayerBaseSerializer()},
        tags=['players'],
        operation_summary="Get current player info",
    )
    @swagger_auto_schema(
        method='patch',
        request_body=PlayerBaseSerializer,
        responses={200: PlayerBaseSerializer()},
        tags=['players'],
        operation_summary="Update current player info",
    )
    @swagger_auto_schema(
        method='delete',
        responses={204: 'No Content'},
        tags=['players'],
        operation_summary="Delete current player",
    )
    @action(['GET', 'PATCH', 'DELETE'], detail=False)
    def me(self, request):
        """Get, patch or delete current player."""
        instance = self.get_object()
        if self.request.method == 'DELETE':
            user = User.objects.filter(player=instance)
            if user:
                # After that corresponding player object will be deleted
                # automatically
                user.delete()

                return Response(status=status.HTTP_204_NO_CONTENT)

            else:
                raise Response(status=status.HTTP_404_NOT_FOUND)

        elif self.request.method == 'PATCH':
            serializer = self.get_serializer(
                instance, data=request.data, partial=True
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()

                return Response(status=status.HTTP_200_OK)

            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        serializer=self.get_serializer(instance)

        return Response(
            status=status.HTTP_200_OK, data=serializer.data
        )

    @swagger_auto_schema(
        method='put',
        request_body=AvatarSerializer,
        responses={200: AvatarSerializer},
        tags=['players'],
        operation_summary="Update or delete avatar",
    )
    @action(
        detail=False, methods=['PUT'], url_path='me/avatar',
        url_name='me-avatar'
    )
    def put_delete_avatar(self, request):
        """Update avatar.
        To delete avatar set its value to null.
        """
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        method='get',
        responses={200: PaymentsSerializer()},
        tags=['players'],
        operation_summary="Get payment data of player"
    )
    @swagger_auto_schema(
        method='put',
        request_body=PaymentSerializer,
        responses={200: ''},
        tags=['players'],
        operation_summary="Update payment data of player"
    )
    @action(
        detail=False, methods=['PUT', 'GET'], url_path='me/payments',
        url_name='me-payments'
    )
    def get_put_payments(self, request):
        """Get or put payment data of player."""
        if self.request.method == 'GET':
            payments = {
                'payments': self.get_queryset()
            }
            serializer = self.get_serializer(payments)

            return Response(data=serializer.data, status=status.HTTP_200_OK)

        serializer = PaymentsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.update_or_create_payments(request.user.player)

        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method='post',
        request_body=FavoriteSerializer,
        responses={201: FavoriteSerializer()},
        tags=['players'],
        operation_summary="Add player to favorite list",
    )
    @swagger_auto_schema(
        method='delete',
        responses={204: 'No Content'},
        tags=['players'],
        operation_summary="Delete player from favorite list",
    )
    @action(
        detail=True, methods=['POST', 'DELETE']
    )
    def favorite(self, request, pk=None):
        """Add or delete player from favorite list."""
        player = self.get_object()
        favorite = get_object_or_404(Player, id=pk)
        serializer = FavoriteSerializer(
            data=request.data,
            context={
                'request': request,
                'player': player, 
                'favorite': favorite
            }
        )
        serializer.is_valid(raise_exception=True)
        if request.method == 'POST':
            Favorite.objects.create(player=player, favorite=favorite)
            response_serializer = FavoriteSerializer(
                favorite,
                context={
                    'request': request,
                    'player': player,
                    'favorite': favorite
                }
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        instance = get_object_or_404(
            Favorite, player=player, favorite=favorite
        )
        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        request_body=PlayerRegisterSerializer,
        responses={200: PlayerBaseSerializer()},
        tags=['players'],
        operation_summary="Register new player"
    )
    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[IsNotRegisteredPlayer],
    )
    def register(self, request):
        """Register new player."""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance=instance, data=request.data
        )
        if serializer.is_valid():
            serializer.save()

            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
