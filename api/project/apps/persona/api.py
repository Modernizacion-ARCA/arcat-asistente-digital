from rest_framework import viewsets, filters
from rest_framework.mixins import RetrieveModelMixin, CreateModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from persona.models import Persona
from persona.serializers import PersonaSerializer, DocumentoSerializer
from util.models import Telefono
from util.serializers import TelefonoSerializer


class PersonaViewSet(ListModelMixin, CreateModelMixin, RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        if self.action in ('create',):
            setattr(self, 'telefono_data', serializer.extraer_telefono())
        return serializer

    def perform_update(self, serializer):
        telefono_data = getattr(self, 'telefono_data')
        TelefonoSerializer(data={'numero': telefono_data}).is_valid(raise_exception=True)

        persona = serializer.save()

        if not persona.telefonos.filter(numero=telefono_data).exists():
            persona.telefonos.add(Telefono(numero=telefono_data), bulk=False)

    @action(
        methods=('POST',),
        detail=False,
        url_path='obtener_persona',
        parser_classes=(JSONParser,)
    )
    def obtener_persona_id(self, request):
        documento_serializer = DocumentoSerializer(data=request.data)
        documento_serializer.is_valid(raise_exception=True)
        documento_identidad = documento_serializer.validated_data['documento_identidad']

        try:
            persona = Persona.objects.get(
                documento_identidad=documento_identidad
            )

            persona_id = persona.id
        except Persona.DoesNotExist:
            persona_id = None

        return Response({'persona_id': persona_id})

