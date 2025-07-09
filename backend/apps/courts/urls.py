from django.urls import path

from .views import CourtsView

urlpatterns = [
    path('courts/', CourtsView.as_view()),
]
