from backend.apps.notifications.constants import (
    Notification,
    NotificationTypes,
)
from backend.apps.notifications.push_service import (
    send_push_notification,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Device
from apps.notifications.serializers import FCMTokenSerializer


class FCMTokenView(APIView):
    '''
    View for handling FCM device tokens.
    Allows users to register or update their device tokens.
    '''
    permission_classes = [IsAuthenticated]
    http_method_names = ['put', 'post'] # delete post on production

    def put(self, request):
        '''
        Handles PUT requests to update FCM device tokens.
        If token already exists but belongs to another player,
        updates the player association to the current user.
        If token doesn't exist, creates a new device for the player.
        '''
        serializer = FCMTokenSerializer(data=request.data)
        
        if serializer.is_valid():
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

##### TEST VIEW #####
    def post(self, request):
        '''
        Test post view for fcm token.
        Sends a push notification to the device.
        For authenticated users,
        body:
        {
            "type": "rate" | "joinGame" | "removed",
        }
        '''
        devices = Device.objects.filter(
            player=request.user.player,
        )
        notification_type = request.data.get('type', NotificationTypes.RATE)
        if notification_type not in NotificationTypes.CHOICES:
            return Response(
                {'message': 'Invalid notification type.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        tokens = devices.values_list('token', flat=True)
        if not tokens:
            return Response(
                {'message': 'No active devices found for the player.'},
                status=status.HTTP_404_NOT_FOUND
            )
        if notification_type == NotificationTypes.IN_GAME:
            game_id = 1
        notification = Notification(type=notification_type)
        send_push_notification(
            tokens=tokens,
            notification=notification,
            game_id=game_id
        )
        return Response(
            {
                'message': f'Notifications processed for type: '
                f'{notification_type}'
            },
            status=status.HTTP_200_OK
        )
