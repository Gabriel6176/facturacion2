from django.contrib import admin

from django.contrib import admin
from .models import MesAno

@admin.register(MesAno)
class MesAnoAdmin(admin.ModelAdmin):
    list_display = ('año', 'mes')
    list_filter = ('año', 'mes')
    ordering = ('año', 'mes')

