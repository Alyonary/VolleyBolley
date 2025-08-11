from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.models import Device
from apps.notifications.serializers import FCMTokenSerializer


class FCMTokenView(APIView):
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
