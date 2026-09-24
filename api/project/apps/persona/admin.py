from django.contrib import admin

from persona.forms import PersonaAdminForm
from persona.models import Persona


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = ('obtener_nombre_completo', 'documento_identidad', 'fecha_nacimiento',)
    search_fields = ('nombre', 'apellido', 'documento_identidad', 'cuit')
    list_per_page = 30
    form = PersonaAdminForm

    def save_model(self, request, obj, form, change):
        obj.referente = request.user
        super().save_model(request, obj, form, change)
