from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from apps.api.views import (
    FacebookLogin,
    GoogleLogin,
    LogoutView,
    PhoneNumberLogin,
)
from apps.courts.views import CourtViewSet
from apps.event.views import GameViewSet
from apps.locations.views import CountryListView
from apps.notifications.views import NotificationsViewSet
from apps.players.views import PlayerViewSet

app_name = 'api'

api_v1 = DefaultRouter()
api_v1.register(r'courts', CourtViewSet, basename='courts')
api_v1.register(r'players', PlayerViewSet, basename='players')
api_v1.register(r'games', GameViewSet, basename='games')
api_v1.register(
    r'notifications',
    NotificationsViewSet,
    basename='notifications'
)

schema_view = get_schema_view(
    openapi.Info(
        title='VolleyBolley API',
        default_version='v1',
        description='API documentation for VolleyBolley project',
        license=openapi.License(name='BSD License'),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', include(api_v1.urls)),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('countries/', CountryListView.as_view(), name='countries'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/google/login/', GoogleLogin.as_view(), name='google-login'),
    path(
        'auth/phone-number/login/',
        PhoneNumberLogin.as_view(),
        name='phone-number-login',
    ),
    path(
        'auth/facebook/login',
        FacebookLogin.as_view(),
        name='facebook-login'
    ),
    path(
        'auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'
    ),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token-verify'),
    # Swagger UI (interactive API docs)
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json'
        ),
    path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='schema-swagger-ui'
        ),
    # ReDoc UI (alternative API docs UI)
    path(
        'redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='schema-redoc'
        ),
]
