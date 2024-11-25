from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView  # Importa vistas genéricas para login/logout
from facturacion import views  # Importa las vistas de la app "facturacion"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('facturacion/', include('facturacion.urls')),  # Incluye las URLs de la app "facturacion"
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),  # Página de inicio de sesión
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),  # Redirección al cerrar sesión
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Página del dashboard
    path('', views.dashboard_redirect, name='home'),  # Redirige a login si no está autenticado
]

# Solo en modo de desarrollo: servir archivos de media (uploads) directamente
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

