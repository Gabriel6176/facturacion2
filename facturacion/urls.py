from django.urls import path
from . import views  # Importa views desde el mismo módulo

urlpatterns = [
    path('', views.file_upload_view, name='file_upload'),
    path('download/<str:filename>/', views.file_download_view, name='file_download'),
]
