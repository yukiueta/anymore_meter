"""anymore_meter URL Configuration"""

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/meters/', include('app.meters.urls')),
    path('api/readings/', include('app.readings.urls')),
    path('api/keys/', include('app.keys.urls')),
    path('api/alerts/', include('app.alerts.urls')),
    path('api/users/', include('app.user.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()