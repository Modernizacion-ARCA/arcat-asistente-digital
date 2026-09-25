from django.contrib import admin

from .models import Categoria, Plataforma, Servicio, Tramite


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'slug', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}
    ordering = ('nombre',)


@admin.register(Plataforma)
class PlataformaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'url', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'descripcion', 'url')
    ordering = ('nombre',)


class GestionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'organismo',
        'area',
        'categoria',
        'modalidad',
        'activo',
        'fecha_actualizacion',
    )
    list_filter = (
        'activo',
        'modalidad',
        'organismo',
        'categoria',
        'plataforma',
    )
    search_fields = (
        'nombre',
        'slug',
        'descripcion',
        'organismo__nombre',
        'area__nombre',
        'categoria__nombre',
    )
    autocomplete_fields = ('organismo', 'area', 'categoria', 'plataforma')
    list_select_related = ('organismo', 'area', 'categoria', 'plataforma')
    prepopulated_fields = {'slug': ('nombre',)}
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    ordering = ('nombre',)
    list_per_page = 30
    fieldsets = (
        (None, {'fields': ('nombre', 'slug', 'descripcion', 'activo')}),
        ('Clasificación', {
            'fields': ('organismo', 'area', 'categoria', 'plataforma', 'modalidad'),
        }),
        ('Información para la gestión', {
            'fields': (
                'requisitos',
                'documentacion',
                'pasos',
                'costo',
                'plazo',
            ),
            'classes': ('collapse',),
        }),
        ('Acceso', {
            'fields': (
                'autenticacion_requerida',
                'metodo_autenticacion',
                'url_inicio',
                'url_instructivo',
            ),
        }),
        ('Publicación', {
            'fields': (
                'fecha_publicacion',
                'observaciones',
                'fecha_creacion',
                'fecha_actualizacion',
            ),
            'classes': ('collapse',),
        }),
    )


@admin.register(Tramite)
class TramiteAdmin(GestionAdmin):
    fieldsets = GestionAdmin.fieldsets + (
        ('Datos del trámite', {'fields': ('tipo',)}),
    )


@admin.register(Servicio)
class ServicioAdmin(GestionAdmin):
    list_filter = GestionAdmin.list_filter + ('tipo',)
    fieldsets = GestionAdmin.fieldsets + (
        ('Datos del servicio', {
            'fields': (
                'tipo',
                'impuesto',
                'conceptos_disponibles',
                'consulta_deuda',
                'generacion_boleta',
                'medios_pago',
                'instrucciones',
            ),
        }),
    )
