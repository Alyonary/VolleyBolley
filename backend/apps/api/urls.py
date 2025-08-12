from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from apps.api.views import LogoutView
from apps.courts.views import CourtViewSet
from apps.locations.views import CountryListView
from apps.notifications.views import FCMTokenView, test_notifications

app_name = 'api'

api_v1 = DefaultRouter()
api_v1.register('courts', CourtViewSet, basename='courts')

urlpatterns = [
    path('', include(api_v1.urls)),
    path('fcm-token/', FCMTokenView.as_view(), name='fcm_token'),
    path('test-fcm/', test_notifications, name='test_fcm'), # DELETE IN PROD
    path('countries/', CountryListView.as_view(), name='countries'), 
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),
]
