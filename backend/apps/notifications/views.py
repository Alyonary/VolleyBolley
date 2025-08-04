from backend.apps.notifications.constants import FCMTokenAction
from backend.apps.notifications.models import Device
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import FCMTokenSerializer


class FCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FCMTokenSerializer
    http_method_names = ['put']

    def put(self, request):
        '''
        Handles PUT requests to update FCM device tokens.
        Validates the provided tokens and performs the appropriate action
        based on the actions:
        - 'update' - updates the existing token,
        - 'set' - creates a new token,
        - 'deactivate' - deactivates the existing token.
        Returns a 200 OK response on success, or a 400 Bad Request response.
        '''
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            action = serializer.validated_data.get('action')
            data = serializer.validated_data
            if action is None:
                return Response(
                    {'detail': 'No action specified.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if action == FCMTokenAction.SET:
                Device.objects.create(
                    token=data['new_token'],
                    player=request.player,
                )
            elif action == FCMTokenAction.UPDATE:
                device = Device.objects.filter(
                    token=data['old_token'],
                    player=request.player
                ).first()
                if not device:
                    return Response(
                        {'detail': 'Device not found.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                device.token = data['new_token']
                device.save()
            elif action == FCMTokenAction.DEACTIVATE:
                device = Device.objects.filter(
                    token=data['old_token'],
                    player=request.player
                ).first()
                if not device:
                    return Response(
                        {'detail': 'Device not found.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                device.is_active = False
                device.save()
            return Response(status=status.HTTP_200_OK)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )