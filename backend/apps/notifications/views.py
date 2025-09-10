import logging

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Device, Notifications
from apps.notifications.notifications import Notification, NotificationTypes
from apps.notifications.push_service import PushService
from apps.notifications.serializers import (
    FCMTokenSerializer,
    NotificationSerializer,
)

logger = logging.getLogger(__name__)


class NotificationsViewSet(
    mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    ViewSet for notifications:
    - GET /notifications/ : list active notifications for current user
    - PATCH /notifications/ : mark notifications as read (bulk)
    - PUT /notifications/fcm-auth : register/update device FCM token
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'put', 'patch']

    def get_queryset(self):
        return Notifications.objects.filter(
            player=self.request.user.player, is_read=False
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'PUT' and getattr(
            self, 'action', None
        ) == 'fcm_auth':
            return FCMTokenSerializer
        return NotificationSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"notifications": serializer.data})

    @action(
        methods=['put', 'patch'],
        detail=False,
        url_path='fcm-auth',
        serializer_class=FCMTokenSerializer,
    )
    def fcm_auth(self, request):
        """
        Registers or updates FCM device token for current user.
        """
        if request.method == 'PATCH':
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
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
            else:
                return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        """
        Bulk mark notifications as read.
        PATCH /api/notifications/
        """
        notifications_data = request.data.get('notifications', [])
        updated: list[int] = []
        not_found: list[int] = []
        for item in notifications_data:
            notification_id = item.get('notification_id')
            try:
                notification = Notifications.objects.get(
                    id=notification_id, player=request.user.player
                )
                notification.is_read = True
                notification.save()
                updated.append(notification_id)
            except Notifications.DoesNotExist:
                not_found.append(notification_id)
        logger.info(
            f'Notifications marked as read: {updated}, not found: {not_found}'
        )
        return Response(status=status.HTTP_200_OK)

    ###TEST ACTION VIEW - DELETE IN PROD
    @action(
        methods=['post'],
        detail=False,
        url_path='fcm-test',
        permission_classes=[IsAuthenticated],
    )
    def fcm_test(self, request):
        """
        Test view to send all notification types for game ID 1.
        Just creates notification tasks and returns response.
        """
        push_service = PushService()
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
            notification = Notification(notification_type=notification_type)
            if notification_type == NotificationTypes.IN_GAME:
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
                'notifications_types': NotificationTypes.CHOICES,
                'devices_count': len(all_tokens),
            }
        )
