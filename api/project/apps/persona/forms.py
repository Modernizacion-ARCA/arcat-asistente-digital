from django.forms import ModelForm

from persona.models import Persona
from util.models import Ubicacion


class PersonaAdminForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PersonaAdminForm, self).__init__(*args, **kwargs)
        # access object through self.instance...
        self.fields['nacionalidad'].autocomplete = False
        self.fields['nacionalidad'].queryset = Ubicacion.objects.filter(tipo=Ubicacion.PAIS)
        catamarca = Ubicacion.objects.filter(tipo=Ubicacion.PROVINCIA, nombre='CATAMARCA').first()
        if catamarca:
            self.fields['localidad'].autocomplete = False
            self.fields['localidad'].queryset = Ubicacion.objects.filter(tipo=Ubicacion.LOCALIDAD,
                                                                         parent__parent=catamarca)
