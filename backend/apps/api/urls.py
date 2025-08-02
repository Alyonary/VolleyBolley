from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from apps.api.views import GoogleLogin, LogoutView
from apps.courts.views import CourtViewSet
from apps.players.views import PlayerViewSet

app_name = 'api'

api_v1 = DefaultRouter()
api_v1.register(r'courts', CourtViewSet, basename='courts')
api_v1.register(r'players', PlayerViewSet, basename='players')

urlpatterns = [
    path('', include(api_v1.urls)),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/google/login/', GoogleLogin.as_view(), name='google-login'),
    path(
        'auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'
    ),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
