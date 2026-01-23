from django.urls import path

from apps.admin_panel.views import (
    dashboard_view,
    notifications_view,
    upload_file,
)

app_name = 'admin_panel'

urlpatterns = [
    path(
        'data_upload/',
        upload_file,
        name='upload_file',
    ),
    path('dashboard/', dashboard_view, name='admin_dashboard'),
    path(
        'notifications/', notifications_view, name='notifications_management'
    ),
]
