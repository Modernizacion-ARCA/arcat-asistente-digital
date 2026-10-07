from rest_framework import serializers

from util.models import Telefono


class TelefonoSerializer(serializers.ModelSerializer):
    tipo = serializers.CharField(source='type', required=False)
    numero = serializers.CharField(source='contact_point')

    class Meta:
        model = Telefono
        fields = ('tipo', 'numero')

    def validate_tipo(self, value):
        aliases = {
            'telefono': Telefono.TELEFONO_FIJO,
            'celular': Telefono.CELULAR,
            'whatsapp': Telefono.WHATSAPP,
        }
        normalized = aliases.get(value.lower(), value.lower())
        valid_types = {choice[0] for choice in Telefono.TIPOS}
        if normalized not in valid_types:
            raise serializers.ValidationError('El tipo de teléfono no es válido.')
        return normalized
