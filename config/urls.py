from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/', include('tracker.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


import os
from django.views.generic import TemplateView
from django.conf import settings

if not settings.DEBUG:
    from django.contrib.staticfiles.views import serve as static_serve
    urlpatterns += [
        path('', TemplateView.as_view(template_name='index.html')),
    ]
