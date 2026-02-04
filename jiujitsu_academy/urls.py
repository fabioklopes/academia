"""
URL configuration for jiujitsu_academy project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('academia.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Configuração de handlers de erro
handler404 = 'academia.views.error_404'
handler413 = 'academia.views.error_413'
handler500 = 'academia.views.error_500'
handler403 = 'academia.views.error_403'
handler400 = 'academia.views.error_400'
