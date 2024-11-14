from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('facturacion/', include('facturacion.urls')),  # Incluye las URLs de la app "facturacion"
]

# Solo en modo de desarrollo: servir archivos de media (uploads) directamente
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
