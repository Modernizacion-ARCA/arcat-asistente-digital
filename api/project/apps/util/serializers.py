from rest_framework import serializers

from util.models import Telefono


class TelefonoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telefono
        fields = ('tipo', 'numero')
