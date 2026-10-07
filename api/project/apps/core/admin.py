from django.contrib import admin
from django.template.loader import render_to_string
from django.utils import timezone

from . import filters
from .models import LLMDailyQuota, LLMRequestLog


@admin.register(LLMDailyQuota)
class LLMDailyQuotaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'solicitudes', 'fecha_actualizacion')
    readonly_fields = ('fecha', 'solicitudes', 'fecha_actualizacion')
    ordering = ('-fecha',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LLMRequestLog)
class LLMRequestLogAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_creacion',
        'modelo',
        'estado',
        'posicion_fallback',
        'tokens_entrada',
        'tokens_salida',
        'duracion_ms',
    )
    list_filter = ('estado', 'modelo', 'fecha_creacion')
    search_fields = ('modelo', 'codigo_error')
    readonly_fields = (
        'proveedor',
        'modelo',
        'estado',
        'posicion_fallback',
        'tokens_entrada',
        'tokens_salida',
        'duracion_ms',
        'codigo_error',
        'fecha_creacion',
    )
    ordering = ('-fecha_creacion',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PublicadoMixinAdmin(admin.ModelAdmin):
    actions = ['publicar', 'no_publicar']

    def publicar(self, request, queryset):
        updated_records = queryset.update(publicado=timezone.now())
        message = 'registros actualizados %s' % updated_records
        self.message_user(request, message)

    publicar.short_description = 'Publicar los registros seleccionados'

    def no_publicar(self, request, queryset):
        updated_records = queryset.update(publicado=None)
        message = 'registros actualizados %s' % updated_records
        self.message_user(request, message)

    no_publicar.short_description = 'Despublicar los registros seleccionados'

    def get_list_display(self, request):
        return list(super().get_list_display(request)) + ['publicado']

    def get_list_filter(self, request):
        list_filter = [filters.PublicadoFilter] + list(super().get_list_filter(request))
        return list_filter


class ControlsAdminMixin(object):
    list_controls_template = None
    list_display_links = None
    search_fields_placeholder = ''

    def get_controls(self, object_instance):
        if not self.list_controls_template:
            self.list_controls_template = 'core/generic_controls.html'

        return render_to_string(
            self.list_controls_template,
            {'object_instance': object_instance, 'request': getattr(self, 'request')}
        )

    get_controls.short_description = ''

    def get_list_display(self, request):
        list_display = [
            'get_controls'
        ] + list(super().get_list_display(request))

        return list_display

    def get_queryset(self, request):
        setattr(self, 'request', request)
        return super().get_queryset(request)

    def get_changelist_instance(self, request):
        changelist = super().get_changelist_instance(request)
        changelist.search_fields_placeholder = self.search_fields_placeholder
        return changelist
