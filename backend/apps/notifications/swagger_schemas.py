from drf_yasg import openapi

from apps.notifications.serializers import (
    FCMTokenSerializer,
    NotificationListSerializer,
)

# Notifications/ GET
NOTIFICATIONS_LIST_SCHEMA = {
    'tags': ['notifications'],
    'operation_summary': 'list of active notifications for current player',
    'operation_description': """
        **Returns:** a list of active notifications for the current player.
    """,
    'responses': {
        200: openapi.Response('Success', NotificationListSerializer),
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}

#  /notifications/fcm-auth/ PUT
NOTIFICATIONS_FCM_AUTH_PUT_SCHEMA = {
    'method': 'put',
    'tags': ['notifications'],
    'operation_summary': 'Register FCM device token for current player',
    'operation_description': """
        **Returns:** empty body response.
    """,
    'request_body': FCMTokenSerializer,
    'responses': {
        200: 'Token updated',
        201: 'Token created',
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}
# notifications/ PATCH
NOTIFICATIONS_MARK_READ_PATCH_SCHEMA = {
    'method': 'patch',
    'tags': ['notifications'],
    'operation_summary': 'Mark list of notifications as read',
    'operation_description': """
        Mark a list of the notifications for the current player as read

        **Returns:** empty body response.
    """,
    'request_body': NotificationListSerializer,
    'responses': {
        200: 'Success',
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Forbidden',
    },
    'security': [{'Bearer': []}, {'JWT': []}],
}
