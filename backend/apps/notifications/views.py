from pyfcm.errors import FCMError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.constants import Notification
from apps.notifications.push_service import send_push_notification
from apps.notifications.serializers import FCMTokenSerializer


class FCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
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
        serializer = FCMTokenSerializer(data=request.data)
        if serializer.is_valid():
            # Device.objects.create(
            #     token=serializer.validated_data['token'],
            #     player=request.user.player
            # )
            print(serializer.validated_data)
            try:
                send_push_notification(
                    ['AIzaSyAq3C3SDMMHMTR_5LiG0pQ2mM638txx0xk'],
                    Notification('joinGame')
                )
            except FileNotFoundError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except FCMError as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'message': 'Token processed successfully.'},
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )