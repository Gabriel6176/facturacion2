from django.urls import path
from . import views  # Importa views desde el mismo módulo

urlpatterns = [
    path('', views.file_upload_view, name='home'), # mientras desarrollo
    #path('', views.dashboard_redirect, name='home'),  # Redirige al login o dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Página del dashboard
    path('upload/', views.file_upload_view, name='file_upload'),  # Página para subir archivos
    path('download/<str:filename>/', views.file_download_view, name='file_download'),  # Descargar archivo
    path('presupuesto/nuevo/', views.presupuesto_nuevo, name='presupuesto_nuevo'),
    path('nueva_prestacion/<int:presupuesto_id>/', views.nueva_prestacion, name='nueva_prestacion'),
    path('buscar_descripcion/', views.buscar_descripcion, name='buscar_descripcion'),
    path('detalle_presupuestador/', views.detalle_presupuestador, name='detalle_presupuestador'),
    path('presupuesto/<int:presupuesto_id>/agregar_item/', views.agregar_item, name='agregar_item'),
    path('presupuesto/<int:presupuesto_id>/eliminar_item/', views.eliminar_item, name='eliminar_item'),
    path('obtener-prestaciones/', views.obtener_prestaciones, name='obtener_prestaciones'),
    path('presupuesto/<int:presupuesto_id>/detalle/', views.detalle_presupuesto, name='detalle_presupuesto'),
    path('presupuesto/<int:numero>/editar/', views.editar_presupuesto, name='editar_presupuesto'),
    path('presupuesto/nuevo/', views.presupuesto_nuevo, name='presupuesto_nuevo'),
]
