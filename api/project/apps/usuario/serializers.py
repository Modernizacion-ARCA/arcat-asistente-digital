from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from rest_framework_json_api import serializers
from rest_framework.serializers import Serializer as DRFSerializer
from django.contrib.auth.models import Group

from persona.serializers import PersonaSerializer

Usuario = get_user_model()


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name',)


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'persona',
            'groups'
        )

    included_serializers = {
        'groups': GroupSerializer

    }


class RegistroUsuarioSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=Usuario.objects.all())]
    )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Usuario
        fields = ('username', 'password', 'password_2', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def extraer_datos_persona(self):
        datos_persona = {}
        if hasattr(self, 'initial_data') and 'persona' in self.initial_data:
            datos_persona = self.initial_data.pop('persona')

        return datos_persona

    def validate(self, attrs):
        if attrs['password'] != attrs['password_2']:
            raise serializers.ValidationError({"password": "Las contraseñas ingresadas no coinciden."})

        return attrs

    def create(self, validated_data):
        usuario = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            **{
                'first_name': validated_data['first_name'],
                'last_name': validated_data['last_name'],
                'is_active': True
            }
        )

        return usuario


class CambiarClaveSecretaSerializer(DRFSerializer):
    clave = serializers.CharField(max_length=128, write_only=True, required=True)
    clave_nueva = serializers.CharField(max_length=128, write_only=True, required=True)
    clave_nueva_2 = serializers.CharField(max_length=128, write_only=True, required=True)

    def validate_clave(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña anterior no es válida. ¡Intentalo nuevamente!")
        return value

    def validate(self, data):
        if data['clave_nueva'] != data['clave_nueva_2']:
            raise serializers.ValidationError({'clave_nueva_2': "Los nuevos campos de contraseñas no coinciden"})
        password_validation.validate_password(data['clave_nueva'], self.context['request'].user)
        return data

    def save(self, **kwargs):
        clave = self.validated_data['clave_nueva']
        usuario = self.context['request'].user
        usuario.set_password(clave)
        usuario.save()
        return usuario
