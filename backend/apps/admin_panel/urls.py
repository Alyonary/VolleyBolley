from django.urls import path

from apps.admin_panel.views import upload_file

app_name = 'admin_panel'

urlpatterns = [
    path(
        'data_upload/',
        upload_file,
        name='upload_file',
    ),
]
