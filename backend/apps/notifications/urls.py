from django.urls import path

from apps.notifications.views import NotificationsViewSet

app_name = 'notifications'


urlpatterns = [
    path(
        '',
        NotificationsViewSet.as_view({'get': 'list', 'patch': 'mark_read'}),
        name='list',
    ),
    path(
        'fcm-auth/',
        NotificationsViewSet.as_view(
            {
                'put': 'fcm_auth',
            }
        ),
        name='fcm-auth',
    ),
    path(
        'fcm-test/',
        NotificationsViewSet.as_view(
            {
                'get': 'fcm_test',
            }
        ),
        name='fcm-test',
    ),
]
