from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from contribuyente.models import Comercio, Parcela
from util.models import Ubicacion


class LocalidadCatamarcaFilter(admin.SimpleListFilter):
    title = _('Localidad')
    parameter_name = 'localidad'

    def lookups(self, request, model_admin):
        departamento_id = self.request.GET.get('departamento', None)
        if not departamento_id:
            qs = Ubicacion.obtener_localidades_catamarca()
        else:
            qs = Ubicacion.objects.filter(parent__id=departamento_id)
        types = [(localidad.id, f"{localidad.nombre} ({localidad.parent.nombre})") for localidad in qs]
        return list(types)

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(localidad_id=self.value())


class DepartamentoCatamarcaFilter(admin.SimpleListFilter):
    title = _('Departamento')
    parameter_name = 'departamento'

    def lookups(self, request, model_admin):
        qs = Ubicacion.obtener_departamentos_catamarca()
        types = qs.values_list('id', 'nombre')
        return list(types)

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        return queryset.filter(localidad__parent__id=self.value())
