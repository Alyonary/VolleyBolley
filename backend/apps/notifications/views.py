import time

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.constants import (
    Notification,
    NotificationTypes,
)
from apps.notifications.models import Device
from apps.notifications.push_service import PushService
from apps.notifications.serializers import FCMTokenSerializer


class FCMTokenView(APIView):
    '''
    View for handling FCM device tokens.
    Allows users to register or update their device tokens.
    '''
    permission_classes = [IsAuthenticated]
    http_method_names = ['put',]

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

### TEST VIEW / DELETE IN PROD ###
@api_view(['GET'])
def test_notifications(request):
    """
    Test view to send all notification types for game ID 1
    with a 1-second delay between notifications.
    """
    push_service = PushService()
    if not push_service:
        return Response(
            {'error': 'Push service not available.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    all_tokens = list(
        Device.objects.filter(is_active=True).values_list('token', flat=True)
    )
    if not all_tokens:
        return Response(
            {'error': 'No active devices found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    results = []
    for notification_type in NotificationTypes.CHOICES:
        notification = Notification(notification_type=notification_type)
        try:
            if notification_type == NotificationTypes.IN_GAME:
                result = push_service.send_push_notifications(
                    tokens=all_tokens,
                    notification=notification,
                    game_id=1
                )
            else:
                result = push_service.send_push_notifications(
                    tokens=all_tokens,
                    notification=notification,
                )
            results.append({
                'type': notification_type,
                'success': result is not None,
                'devices_count': len(all_tokens),
                'status': 'Sent successfully' if result else 'Failed to send'
            })
                
        except Exception as e:
            results.append({
                'type': notification_type,
                'success': False,
                'devices_count': len(all_tokens),
                'status': f'Error: {str(e)}'
            })
        time.sleep(1)
    return Response({
        'notifications_sent': len(results),
        'devices_count': len(all_tokens),
        'results': results
    })

