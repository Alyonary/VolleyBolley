import logging

from django.contrib.auth.models import AnonymousUser
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.core.permissions import IsRegisteredPlayer
from apps.notifications.constants import NotificationTypes
from apps.notifications.models import Device, Notifications, NotificationsBase
from apps.notifications.push_service import PushService
from apps.notifications.serializers import (
    FCMTokenSerializer,
    NotificationListSerializer,
    NotificationSerializer,
)
from apps.players.models import Player

logger = logging.getLogger(__name__)


class NotificationsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for notifications:
    - GET /notifications/ : list active notifications for current user
    - PATCH /notifications/ : mark notifications as read (bulk)
    - PUT /notifications/fcm-auth : register/update device FCM token
    """

    permission_classes = [IsRegisteredPlayer]
    serializer_class = NotificationListSerializer
    http_method_names = ['get', 'put', 'patch',]

    def get_queryset(self):
        return Notifications.objects.filter(
            player=self.request.user.player, is_read=False
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'fcm_auth':
            return FCMTokenSerializer
        return NotificationListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if not isinstance(user, AnonymousUser):
            context.update({
                'player': Player.objects.get(user=user)
            })
        return context

    @swagger_auto_schema(
        tags=['notifications'],
        operation_summary="list of active notifications for current player",
        operation_description="""
        **Returns:** a list of active notifications for the current player.
        """,
        responses={
            200: openapi.Response('Success', NotificationListSerializer),
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer({'notifications': queryset})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['notifications'],
        method='put',
        operation_summary="Register FCM device token for current player",
        operation_description="""
        **Returns:** empty body response.
        """,
        request_body=FCMTokenSerializer,
        responses={
            200: 'Token updated',
            201: 'Token created',
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['put'],
        detail=False,
        url_path='fcm-auth',
        serializer_class=FCMTokenSerializer,
    )
    def fcm_auth(self, request):
        """
        Registers or updates FCM device token for current user.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            token = serializer.validated_data['token']
            current_player = request.user.player
            device, created = Device.objects.update_or_create_token(
                token=token,
                player=current_player,
                platform=serializer.validated_data.get('platform', None),
            )
            if created:
                return Response(status=status.HTTP_201_CREATED)
            return Response(status=status.HTTP_200_OK)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @swagger_auto_schema(
        tags=['notifications'],
        operation_summary="Mark list of notifications as read",
        operation_description="""
        Mark a list of the notifications for the current player as read

        **Returns:** empty body response.
        """,
        request_body=NotificationListSerializer,
        responses={
            200: 'Success',
            400: 'Bad request',
            401: 'Unauthorized',
            403: 'Forbidden',
        },
        security=[{'Bearer': []}, {'JWT': []}],
    )
    @action(
        methods=['patch'],
        detail=False,
        url_path='',
        url_name='mark-read',
        serializer_class=NotificationListSerializer,
    )
    def mark_read(self, request):
        """
        Bulk mark notifications as read.
        PATCH /api/notifications/
        """
        notifications_from_request = request.data.get('notifications')
        instances = Notifications.objects.filter(
            pk__in=[
                item['notification_id'] for item in notifications_from_request
            ]
        )
        for instance in instances:
            serializer = NotificationSerializer(
                instance=instance,
                data={'notification_id': instance.pk},
                context=self.get_serializer_context()
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(status=status.HTTP_200_OK)

    # TEST ACTION VIEW - DELETE IN PROD
    @action(
        methods=['get'],
        detail=False,
        url_path='fcm-test',
        permission_classes=[AllowAny],
    )
    def fcm_test(self, request):
        """
        Test view to send all notification types for game ID 1.
        Just creates notification tasks and returns response.
        """
        push_service = PushService()
        if not push_service:
            push_service.reconnect()
            if not push_service:
                return Response(
                    {'error': 'Push service not available.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
        all_tokens = list(
            Device.objects.filter(is_active=True).values_list(
                'token', flat=True
            )
        )
        if not all_tokens:
            return Response(
                {'error': 'No active devices found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        for notification_type in NotificationTypes.CHOICES:
            if notification_type in [
                NotificationTypes.GAME_REMINDER,
                NotificationTypes.TOURNEY_REMINDER,
            ]:
                continue
            notification = NotificationsBase(
                notification_type=notification_type
            )
            if notification_type == NotificationTypes.GAME_REMINDER:
                push_service.send_push_notifications(
                    tokens=all_tokens, notification=notification, game_id=1
                )
            else:
                push_service.send_push_notifications(
                    tokens=all_tokens,
                    notification=notification,
                )
        return Response(
            {
                'status': 'Notification tasks created',
                'devices_count': len(all_tokens),
            }
        )
