from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from apps.core.views import FAQView
from apps.courts.views import CourtViewSet
from apps.event.views import GameViewSet, TourneyViewSet
from apps.locations.views import CountryListView
from apps.players.views import PlayerViewSet

app_name = 'api'

api_v1 = DefaultRouter()
api_v1.register(r'courts', CourtViewSet, basename='courts')
api_v1.register(r'players', PlayerViewSet, basename='players')
api_v1.register(r'games', GameViewSet, basename='games')
<<<<<<< HEAD
api_v1.register(r'tournaments', TourneyViewSet, basename='tournaments')
api_v1.register(
    r'notifications',
    NotificationsViewSet,
    basename='notifications'
)
=======
>>>>>>> origin/main

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
    path('auth/', include('apps.authentication.urls', namespace='auth')),
    path(
        'notifications/',
        include('apps.notifications.urls', namespace='notifications')
    ),
<<<<<<< HEAD
    path(
        'auth/facebook/login',
        FacebookLogin.as_view(),
        name='facebook-login'
    ),
=======
>>>>>>> origin/main
    # Swagger UI (interactive API docs)
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
<<<<<<< HEAD
        name='schema-json'
=======
        name='schema-json',
>>>>>>> origin/main
    ),
    path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
<<<<<<< HEAD
        name='schema-swagger-ui'
=======
        name='schema-swagger-ui',
>>>>>>> origin/main
    ),
    # ReDoc UI (alternative API docs UI)
    path(
        'redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
<<<<<<< HEAD
        name='schema-redoc'
    ),
=======
        name='schema-redoc',
    ),
    path('faq/', FAQView.as_view(), name='faq'),
>>>>>>> origin/main
]
