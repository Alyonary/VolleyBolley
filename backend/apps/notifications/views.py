import logging

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from apps.notifications.models import Device, Notifications
from apps.notifications.notifications import Notification, NotificationTypes
from apps.notifications.push_service import PushService
from apps.notifications.serializers import (
    FCMTokenSerializer,
    NotificationSerializer,
)

logger = logging.getLogger(__name__)


class NotificationsViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet for notifications:
    - GET /notifications/ : list active notifications for current user
    - PUT /notifications/ : mark notifications as read
    - PUT /notifications/fcm-auth : register/update device FCM token
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        return Notifications.objects.filter(
            player=self.request.user.player,
            is_read=False
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'PUT' and self.action == 'fcm_auth':
            return FCMTokenSerializer
        return NotificationSerializer

    def list(self, request, *args, **kwargs):
        """
        Returns all unread notifications for the current user.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Marks notifications as read.
        Expects:
        {
            "notifications": [
                {"notification_id": 1},
                {"notification_id": 2}
            ]
        }
        """
        notifications_data = request.data.get('notifications', [])
        updated: list[int] = []
        not_found: list[int] = []
        for item in notifications_data:
            notification_id = item.get('notification_id')
            try:
                notification = Notifications.objects.get(
                    id=notification_id,
                    player=request.user.player
                )
                serializer = self.get_serializer(
                    notification,
                    data={},
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save(is_read=True)
                updated.append(notification_id)
            except Notifications.DoesNotExist:
                not_found.append(notification_id)
            except ValidationError:
                not_found.append(notification_id)
        logger.info(
            f'Notifications marked as read: {updated}, not found: {not_found}'
        )
        return Response(
            {
                'updated': updated,
                'not_found': not_found,
                'message': 'Notifications marked as read.'
            },
            status=status.HTTP_200_OK
        )

    @action(
        methods=['put'],
        detail=False,
        url_path='fcm-auth',
        serializer_class=FCMTokenSerializer
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
                return Response(
                    {'message': 'New device token registered.'},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'message': 'Device token updated.'},
                    status=status.HTTP_200_OK
                )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
###TEST ACTION VIEW - DELETE IN PROD
    @action(
        methods=['post'],
        detail=False,
        url_path='fcm-test',
        permission_classes=[IsAuthenticated]
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
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        all_tokens = list(
            Device.objects.filter(
                is_active=True
            ).values_list('token', flat=True)
        )
        if not all_tokens:
            return Response(
                {'error': 'No active devices found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        for notification_type in NotificationTypes.CHOICES:
            notification = Notification(notification_type=notification_type)
            if notification_type == NotificationTypes.IN_GAME:
                push_service.send_push_notifications(
                    tokens=all_tokens,
                    notification=notification,
                    game_id=1
                )
            else:
                push_service.send_push_notifications(
                    tokens=all_tokens,
                    notification=notification,
                )
        return Response({
            'status': 'Notification tasks created',
            'notifications_types': NotificationTypes.CHOICES,
            'devices_count': len(all_tokens)
        })
