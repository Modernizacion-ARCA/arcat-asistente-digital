from types import SimpleNamespace

from core.ai.llm import LLMResponse
from sources.rag import NO_EVIDENCE_ANSWER, RAGService


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def retrieve(self, question, filters=None):
        self.calls.append((question, filters))
        return self.results


class FakeLLMService:
    def __init__(self):
        self.messages = None

    def generate(self, messages):
        self.messages = messages
        return LLMResponse(text='Respuesta sustentada [1]', model='modelo:free')


def test_sin_evidencia_no_invoca_llm():
    llm_service = FakeLLMService()
    service = RAGService(
        retriever=FakeRetriever([]),
        llm_service=llm_service,
    )

    response = service.answer('Pregunta sin respuesta')

    assert response.answer == NO_EVIDENCE_ANSWER
    assert response.evidence == ()
    assert response.model is None
    assert llm_service.messages is None


def test_respuesta_incluye_evidencias_trazables():
    source = SimpleNamespace(nombre='Fuente oficial')
    document = SimpleNamespace(
        titulo='Documento oficial',
        url='https://example.gov/documento',
        fuente=source,
    )
    chunk = SimpleNamespace(
        pk=7,
        contenido='La evidencia oficial responde la consulta.',
        documento=document,
    )
    result = SimpleNamespace(chunk=chunk)
    llm_service = FakeLLMService()
    service = RAGService(
        retriever=FakeRetriever([result]),
        llm_service=llm_service,
    )

    response = service.answer('¿Cuál es la respuesta?')

    assert response.answer == 'Respuesta sustentada [1]'
    assert response.model == 'modelo:free'
    assert response.evidence[0].chunk_id == 7
    assert response.evidence[0].url == document.url
    assert '[1] Documento oficial' in llm_service.messages[1]['content']
    assert 'evidencia oficial' in llm_service.messages[1]['content']
