import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import Fuente
from .retrieval import HybridRetriever, RetrievalFilters


class EvaluationDatasetError(ValueError):
    """Raised when a versioned RAG evaluation dataset is invalid."""


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    question: str
    expected_document_urls: tuple[str, ...]
    expected_terms: tuple[str, ...]
    origen_informacion: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    hit: bool
    reciprocal_rank: float
    term_coverage: float
    retrieved_document_urls: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationReport:
    dataset: str
    version: int
    cases: int
    hit_rate: float
    mean_reciprocal_rank: float
    mean_term_coverage: float
    results: tuple[CaseResult, ...]

    def to_dict(self):
        return asdict(self)


def _required_string(value, field, case_id):
    if not isinstance(value, str) or not value.strip():
        raise EvaluationDatasetError(
            f'El caso {case_id!r} requiere un valor válido en {field}.'
        )
    return value.strip()


def load_dataset(path):
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationDatasetError(f'No se pudo leer el dataset: {exc}') from exc

    if not isinstance(payload, dict):
        raise EvaluationDatasetError('La raíz del dataset debe ser un objeto JSON.')
    if payload.get('version') != 1 or not isinstance(payload.get('cases'), list):
        raise EvaluationDatasetError('El dataset debe usar version=1 y contener cases.')
    dataset_name = _required_string(payload.get('name'), 'name', 'dataset')
    cases = []
    seen_ids = set()
    valid_origins = {choice for choice, _ in Fuente.OrigenInformacion.choices}
    for raw_case in payload['cases']:
        if not isinstance(raw_case, dict):
            raise EvaluationDatasetError('Cada caso debe ser un objeto JSON.')
        case_id = _required_string(raw_case.get('id'), 'id', 'sin-id')
        if case_id in seen_ids:
            raise EvaluationDatasetError(f'El id de caso {case_id!r} está duplicado.')
        seen_ids.add(case_id)
        question = _required_string(raw_case.get('question'), 'question', case_id)
        urls = raw_case.get('expected_document_urls')
        if not isinstance(urls, list) or not urls:
            raise EvaluationDatasetError(
                f'El caso {case_id!r} requiere expected_document_urls.'
            )
        expected_urls = tuple(
            _required_string(url, 'expected_document_urls', case_id) for url in urls
        )
        terms = raw_case.get('expected_terms', [])
        if not isinstance(terms, list):
            raise EvaluationDatasetError(
                f'expected_terms debe ser una lista en el caso {case_id!r}.'
            )
        origin = raw_case.get('origen_informacion', Fuente.OrigenInformacion.OFICIAL)
        if origin not in valid_origins:
            raise EvaluationDatasetError(
                f'origen_informacion inválido en el caso {case_id!r}.'
            )
        cases.append(EvaluationCase(
            case_id=case_id,
            question=question,
            expected_document_urls=expected_urls,
            expected_terms=tuple(str(term).strip() for term in terms if str(term).strip()),
            origen_informacion=origin,
        ))
    if not cases:
        raise EvaluationDatasetError('El dataset debe contener al menos un caso.')
    return dataset_name, payload['version'], tuple(cases)


class RAGEvaluator:
    def __init__(self, retriever=None):
        self.retriever = retriever or HybridRetriever()

    def evaluate_case(self, case):
        results = self.retriever.retrieve(
            case.question,
            filters=RetrievalFilters(origen_informacion=case.origen_informacion),
        )
        urls = tuple(result.chunk.documento.url for result in results)
        expected = set(case.expected_document_urls)
        relevant_rank = next(
            (rank for rank, url in enumerate(urls, start=1) if url in expected),
            None,
        )
        retrieved_text = ' '.join(
            result.chunk.contenido.casefold() for result in results
        )
        matched_terms = sum(
            1 for term in case.expected_terms if term.casefold() in retrieved_text
        )
        term_coverage = (
            matched_terms / len(case.expected_terms) if case.expected_terms else 1.0
        )
        return CaseResult(
            case_id=case.case_id,
            hit=relevant_rank is not None,
            reciprocal_rank=1 / relevant_rank if relevant_rank else 0.0,
            term_coverage=term_coverage,
            retrieved_document_urls=urls,
        )

    def evaluate(self, dataset_name, version, cases):
        results = tuple(self.evaluate_case(case) for case in cases)
        total = len(results)
        return EvaluationReport(
            dataset=dataset_name,
            version=version,
            cases=total,
            hit_rate=sum(result.hit for result in results) / total,
            mean_reciprocal_rank=(
                sum(result.reciprocal_rank for result in results) / total
            ),
            mean_term_coverage=(
                sum(result.term_coverage for result in results) / total
            ),
            results=results,
        )
