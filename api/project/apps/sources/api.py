from rest_framework import permissions, status
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.ai.llm import LLMProviderError
from core.ai.service import LLMUsageLimitError

from .rag import RAGService
from .retrieval import RetrievalFilters
from .serializers import RAGAnswerSerializer, RAGQuestionSerializer
from .throttling import HashedRAGThrottle


class RAGQuestionAPIView(APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    parser_classes = (JSONParser,)
    throttle_classes = (HashedRAGThrottle,)

    def post(self, request):
        serializer = RAGQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        filters = RetrievalFilters(
            organismo_id=data.get('organismo_id'),
            categoria_id=data.get('categoria_id'),
        )
        try:
            answer = RAGService().answer(data['pregunta'], filters=filters)
        except LLMUsageLimitError as exc:
            return Response(
                {'detail': str(exc), 'code': 'usage_limit_exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except LLMProviderError:
            return Response(
                {
                    'detail': 'El asistente no está disponible temporalmente.',
                    'code': 'assistant_unavailable',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        output = RAGAnswerSerializer(answer)
        return Response(output.data, status=status.HTTP_200_OK)
