from rest_framework_json_api import serializers

from persona.models import Persona
from util.serializers import TelefonoSerializer


class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = (
            'nombre',
            'apellido',
            'documento_identidad',
            'fecha_nacimiento',
            'domicilio',
            'correo_electronico',
            'telefonos',
            'referente'

        )
        extra_kwargs = {
            'usuario': {'read_only': True}
        }

    telefonos = TelefonoSerializer(many=True, required=False)

    included_serializers = {
        'telefonos': TelefonoSerializer,
    }

    def extraer_telefono(self):
        telefono = ''
        if hasattr(self, 'initial_data') and 'telefono' in self.initial_data:
            telefono = self.initial_data.pop('telefono')
        return telefono


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = (
            'documento_identidad',
        )
