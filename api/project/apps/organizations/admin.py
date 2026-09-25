from django.contrib import admin
from django.db.models import Count

from .models import Area, Organismo


@admin.register(Organismo)
class OrganismoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'cantidad_areas', 'fecha_actualizacion')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion', 'url')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    ordering = ('nombre',)
    list_per_page = 30

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_cantidad_areas=Count('areas'))

    @admin.display(description='Áreas', ordering='_cantidad_areas')
    def cantidad_areas(self, obj):
        return obj._cantidad_areas


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'organismo', 'activo', 'fecha_actualizacion')
    list_filter = ('activo', 'organismo')
    search_fields = ('nombre', 'descripcion', 'organismo__nombre')
    autocomplete_fields = ('organismo',)
    list_select_related = ('organismo',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    ordering = ('organismo__nombre', 'nombre')
    list_per_page = 30
