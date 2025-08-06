from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from apps.courts.views import CourtViewSet
# from apps.event.views import GameViewSet

from .views import LogoutView
from apps.locations.views import CountryListView

app_name = 'api'

api_v1 = DefaultRouter()
api_v1.register('courts', CourtViewSet, basename='courts')
# api_v1.register(r'games', GameViewSet, basename='games')

urlpatterns = [
    path('', include(api_v1.urls)),
    path('countries/', CountryListView.as_view(), name='countries'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),
]
