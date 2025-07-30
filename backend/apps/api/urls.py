from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from apps.core.views import PaymentViewSet
from apps.courts.views import CourtViewSet
from apps.event.views import GameViewSet

from .views import LogoutView

app_name = 'api'

api_v1 = DefaultRouter()
api_v1.register('courts', CourtViewSet, basename='courts')
api_v1.register('games', GameViewSet, basename='games')
api_v1.register('payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(api_v1.urls)),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),
]
