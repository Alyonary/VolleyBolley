from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', include('apps.admin_panel.urls', namespace='admin_panel')),
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls', namespace='api')),
    path(
        'privacy/',
        TemplateView.as_view(template_name='privacy.html'),
        name='privacy',
    ),
    path(
        'terms/',
        TemplateView.as_view(template_name='terms.html'),
        name='terms',
    ),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('', include('django_prometheus.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
