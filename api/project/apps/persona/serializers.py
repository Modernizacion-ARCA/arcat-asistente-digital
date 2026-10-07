from django.db import transaction
from rest_framework_json_api import serializers

from persona.models import Persona
from util.models import Mail, Telefono
from util.serializers import TelefonoSerializer


class PersonaSerializer(serializers.ModelSerializer):
    correo_electronico = serializers.EmailField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    telefonos = TelefonoSerializer(many=True, write_only=True, required=False)

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
        )

    @transaction.atomic
    def create(self, validated_data):
        correo_electronico = validated_data.pop('correo_electronico', '')
        telefonos = validated_data.pop('telefonos', [])
        persona = Persona.objects.create(**validated_data)
        if correo_electronico:
            Mail.objects.create(
                content_object=persona,
                contact_point=correo_electronico,
            )
        for telefono in telefonos:
            Telefono.objects.create(content_object=persona, **telefono)
        return persona


class DocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = (
            'documento_identidad',
        )
