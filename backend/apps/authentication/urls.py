from django.urls import path

from apps.authentication.views import (
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    FacebookLogin,
    GoogleLogin,
    GoogleLoginV2,
    LogoutView,
    PhoneNumberLogin,
)

app_name = 'auth'


urlpatterns = [
    path('logout/', LogoutView.as_view(), name='logout'),
    path('google/login/', GoogleLogin.as_view(), name='google-login'),
    path('google/login/v2/', GoogleLoginV2.as_view(), name='google-login-v2'),
    path(
        'phone-number/login/',
        PhoneNumberLogin.as_view(),
        name='phone-number-login',
    ),
    path('facebook/login', FacebookLogin.as_view(), name='facebook-login'),
    path(
        'token/refresh/',
        CustomTokenRefreshView.as_view(),
        name='token-refresh',
    ),
    path(
        'token/verify/', CustomTokenVerifyView.as_view(), name='token-verify'
    ),
]
