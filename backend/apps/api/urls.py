from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import LogoutView
from apps.courts.views import CourtViewSet

api_v1 = DefaultRouter()
api_v1.register('courts', CourtViewSet, basename='courts')

app_name = 'api'

urlpatterns = [
    path('', include(api_v1.urls)),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),
]
