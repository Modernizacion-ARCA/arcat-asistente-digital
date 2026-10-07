from django.conf import settings
from rest_framework import serializers


class RAGQuestionSerializer(serializers.Serializer):
    pregunta = serializers.CharField(
        allow_blank=False,
        max_length=settings.RAG_MAX_QUESTION_LENGTH,
        trim_whitespace=True,
    )
    organismo_id = serializers.IntegerField(required=False, min_value=1)
    categoria_id = serializers.IntegerField(required=False, min_value=1)


class RAGEvidenceSerializer(serializers.Serializer):
    fragmento_id = serializers.IntegerField(source='chunk_id')
    documento = serializers.CharField(source='document_title')
    fuente = serializers.CharField(source='source_name')
    url = serializers.URLField()


class RAGAnswerSerializer(serializers.Serializer):
    respuesta = serializers.CharField(source='answer')
    evidencias = RAGEvidenceSerializer(source='evidence', many=True)
    modelo = serializers.CharField(source='model', allow_null=True)
