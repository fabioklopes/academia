"""
URL configuration for jiujitsu_academy project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('academia.urls')),
]

# Configuração para servir arquivos de mídia em Desenvolvimento e Produção
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

# Configuração de handlers de erro
handler404 = 'academia.views.error_404'
handler500 = 'academia.views.error_500'
handler403 = 'academia.views.error_403'
handler400 = 'academia.views.error_400'
