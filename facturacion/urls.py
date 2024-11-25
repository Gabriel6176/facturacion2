from django.urls import path
from . import views  # Importa views desde el mismo módulo

urlpatterns = [
    path('', views.file_upload_view, name='home'), # mientras desarrollo
    #path('', views.dashboard_redirect, name='home'),  # Redirige al login o dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Página del dashboard
    path('upload/', views.file_upload_view, name='file_upload'),  # Página para subir archivos
    path('download/<str:filename>/', views.file_download_view, name='file_download'),  # Descargar archivo
    
]
