from django.contrib import admin

from django.contrib import admin
from .models import MesAno, Presupuesto, Prestacion, DetallePrestacion

@admin.register(MesAno)
class MesAnoAdmin(admin.ModelAdmin):
    list_display = ('año', 'mes')
    list_filter = ('año', 'mes')
    ordering = ('año', 'mes')

# Configuración avanzada para la administración de Presupuesto
@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    # Columnas visibles en la lista de elementos
    list_display = ('numero', 'cliente', 'documento', 'fecha')
    
    # Campos que se pueden buscar
    search_fields = ('cliente', 'documento')
    
    # Filtros laterales
    list_filter = ('fecha',)
    
    # Orden por defecto
    ordering = ('-fecha',)  # Orden descendente por fecha (los más recientes primero)
    
    # Campos que se agrupan para editar
    fieldsets = (
        ("Información General", {
            'fields': ('cliente', 'documento')
        }),
        ("Datos del Presupuesto", {
            'fields': ('fecha',)
        }),
    )

    # Solo lectura para ciertos campos
    readonly_fields = ('fecha',)

# Configuración avanzada para la administración de Prestacion
@admin.register(Prestacion)
class PrestacionAdmin(admin.ModelAdmin):
    # Columnas visibles en la lista de elementos
    list_display = ('codigo', 'descripcion', 'honorarios', 'ayudante', 'gastos', 'anestesia', 'total', 'servicio', 'practica')
    
    # Campos que se pueden buscar
    search_fields = ('codigo', 'descripcion', 'servicio', 'practica')
    
    # Filtros laterales
    list_filter = ('servicio',)
    
    # Orden por defecto
    ordering = ('servicio',)
    
    # Campos que se agrupan para editar
    fieldsets = (
        ("Información General", {
            'fields': ('codigo', 'descripcion', 'servicio', 'practica')
        }),
        ("Detalles Económicos", {
            'fields': ('honorarios', 'ayudante', 'gastos', 'anestesia', 'total')
        }),
    )

@admin.register(DetallePrestacion)
class DetallePrestacionAdmin(admin.ModelAdmin):
    # Columnas visibles en la lista
    list_display = ('presupuesto', 'prestacion')
    
    # Campos que se pueden buscar
    search_fields = ('presupuesto__cliente', 'prestacion__descripcion')
    
    # Filtros laterales
    list_filter = ('presupuesto', 'prestacion')
    
    # Orden por defecto
    ordering = ('presupuesto', 'prestacion')

