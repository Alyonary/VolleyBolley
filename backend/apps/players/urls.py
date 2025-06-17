from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.players import views

app_name = 'players'
router = DefaultRouter()
router.register('', views.PlayerViewSet)

urlpatterns = [
    path('players/', include(router.urls)),
]
