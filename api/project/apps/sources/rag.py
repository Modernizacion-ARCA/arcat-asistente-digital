from dataclasses import dataclass

from django.conf import settings

from core.ai.service import LLMService, conservative_token_estimate

from .retrieval import HybridRetriever, RetrievalFilters


NO_EVIDENCE_ANSWER = 'No encuentro esa información en las fuentes oficiales disponibles.'


@dataclass(frozen=True)
class Evidence:
    chunk_id: int
    document_title: str
    source_name: str
    url: str


@dataclass(frozen=True)
class RAGAnswer:
    answer: str
    evidence: tuple[Evidence, ...]
    model: str | None


class RAGService:
    system_prompt = (
        'Respondé en español usando exclusivamente el contexto proporcionado. '
        'No inventes datos. Citá las evidencias con [1], [2], etc. Si el contexto '
        f'no alcanza, respondé exactamente: "{NO_EVIDENCE_ANSWER}"'
    )

    def __init__(self, retriever=None, llm_service=None):
        self.retriever = retriever or HybridRetriever()
        self.llm_service = llm_service or LLMService()

    @staticmethod
    def _format_result(result, position):
        chunk = result.chunk
        return (
            f'[{position}] Documento: {chunk.documento.titulo}\n'
            f'Fuente: {chunk.documento.fuente.nombre}\n'
            f'URL: {chunk.documento.url}\n'
            f'Contenido:\n{chunk.contenido}'
        )

    def _build_messages(self, question, results):
        selected = []
        context_parts = []
        for result in results:
            position = len(selected) + 1
            candidate = self._format_result(result, position)
            proposed_context = '\n\n'.join((*context_parts, candidate))
            messages = [
                {'role': 'system', 'content': self.system_prompt},
                {
                    'role': 'user',
                    'content': f'Contexto:\n{proposed_context}\n\nPregunta: {question}',
                },
            ]
            if conservative_token_estimate(messages) > settings.MAX_INPUT_TOKENS:
                continue
            selected.append(result)
            context_parts.append(candidate)
        if not selected:
            return [], []
        context = '\n\n'.join(context_parts)
        return selected, [
            {'role': 'system', 'content': self.system_prompt},
            {
                'role': 'user',
                'content': (
                    f'Contexto:\n{context}\n\nPregunta: {question}'
                ),
            },
        ]

    def answer(self, question, filters=None):
        question = question.strip()
        if not question:
            return RAGAnswer(answer=NO_EVIDENCE_ANSWER, evidence=(), model=None)
        results = self.retriever.retrieve(
            question,
            filters=filters or RetrievalFilters(),
        )
        selected, messages = self._build_messages(question, results)
        if not selected:
            return RAGAnswer(answer=NO_EVIDENCE_ANSWER, evidence=(), model=None)

        response = self.llm_service.generate(messages)
        evidence = tuple(
            Evidence(
                chunk_id=result.chunk.pk,
                document_title=result.chunk.documento.titulo,
                source_name=result.chunk.documento.fuente.nombre,
                url=result.chunk.documento.url,
            )
            for result in selected
        )
        return RAGAnswer(
            answer=response.text,
            evidence=evidence,
            model=response.model,
        )
