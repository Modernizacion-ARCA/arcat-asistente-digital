from django.contrib import admin

from .models import Documento, Fuente


@admin.register(Fuente)
class FuenteAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'organismo',
        'tipo',
        'origen_informacion',
        'estado_verificacion',
        'estado_disponibilidad',
        'prioridad',
        'activo',
    )
    list_filter = (
        'activo',
        'origen_informacion',
        'estado_verificacion',
        'estado_disponibilidad',
        'tipo',
        'organismo',
        'categoria',
    )
    search_fields = ('nombre', 'url', 'organismo__nombre')
    autocomplete_fields = ('organismo', 'categoria', 'plataforma')
    list_select_related = ('organismo', 'categoria', 'plataforma')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    ordering = ('prioridad', 'nombre')
    list_per_page = 30


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'fuente',
        'tipo',
        'fecha_documento',
        'activo',
        'fecha_actualizacion',
    )
    list_filter = (
        'activo',
        'tipo',
        'fuente__origen_informacion',
        'fuente__estado_verificacion',
        'fecha_documento',
    )
    search_fields = (
        'titulo',
        'url',
        'checksum',
        'fuente__nombre',
        'texto_extraido',
    )
    autocomplete_fields = ('fuente', 'tramites', 'servicios')
    list_select_related = ('fuente',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    ordering = ('titulo',)
    list_per_page = 30
    fieldsets = (
        (None, {'fields': ('titulo', 'tipo', 'fuente', 'url', 'activo')}),
        ('Relaciones', {'fields': ('tramites', 'servicios')}),
        ('Contenido', {
            'fields': ('contenido', 'texto_extraido', 'checksum', 'metadata'),
            'classes': ('collapse',),
        }),
        ('Fechas', {
            'fields': ('fecha_documento', 'fecha_creacion', 'fecha_actualizacion'),
        }),
    )
