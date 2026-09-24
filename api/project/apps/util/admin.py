from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from util.models import  Telefono, Ubicacion, Mail, RedSocial


class TelefonoInline(GenericTabularInline):
    model = Telefono
    extra = 0

class MailInline(GenericTabularInline):
    model = Mail
    extra = 0

@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'parent',
        'tipo',
    )
    search_fields = ('nombre',)
    list_select_related = ('parent', 'parent__parent')
    list_filter = ('tipo',)



class RedSocialInline(GenericTabularInline):
    model = RedSocial
    extra = 0
