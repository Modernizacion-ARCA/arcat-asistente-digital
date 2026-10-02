import json
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from sources.evaluation import (
    EvaluationCase,
    EvaluationDatasetError,
    EvaluationReport,
    RAGEvaluator,
    load_dataset,
)


def retrieval_result(pk, url, content):
    document = SimpleNamespace(url=url)
    chunk = SimpleNamespace(pk=pk, documento=document, contenido=content)
    return SimpleNamespace(chunk=chunk)


class FakeRetriever:
    def __init__(self, results_by_question):
        self.results_by_question = results_by_question
        self.filters = []

    def retrieve(self, question, filters=None):
        self.filters.append(filters)
        return self.results_by_question.get(question, [])


def test_evaluador_calcula_hit_rate_mrr_y_cobertura():
    cases = (
        EvaluationCase(
            case_id='caso-1',
            question='pregunta uno',
            expected_document_urls=('https://demo.invalid/esperado-1',),
            expected_terms=('CUIT', 'formulario'),
            origen_informacion='DEMO',
        ),
        EvaluationCase(
            case_id='caso-2',
            question='pregunta dos',
            expected_document_urls=('https://demo.invalid/esperado-2',),
            expected_terms=('IIBB',),
            origen_informacion='DEMO',
        ),
    )
    retriever = FakeRetriever({
        'pregunta uno': [
            retrieval_result(1, 'https://demo.invalid/otro', 'CUIT'),
            retrieval_result(
                2,
                'https://demo.invalid/esperado-1',
                'Formulario requerido',
            ),
        ],
        'pregunta dos': [
            retrieval_result(3, 'https://demo.invalid/otro', 'Sin coincidencias'),
        ],
    })

    report = RAGEvaluator(retriever=retriever).evaluate('dataset-demo', 1, cases)

    assert report.cases == 2
    assert report.hit_rate == 0.5
    assert report.mean_reciprocal_rank == 0.25
    assert report.mean_term_coverage == 0.5
    assert all(item.origen_informacion == 'DEMO' for item in retriever.filters)


def test_loader_valida_dataset_versionado(tmp_path):
    path = tmp_path / 'dataset.json'
    path.write_text(json.dumps({
        'name': 'Dataset DEMO',
        'version': 1,
        'cases': [{
            'id': 'demo-1',
            'question': 'Pregunta DEMO',
            'expected_document_urls': ['https://demo.invalid/documento'],
            'expected_terms': ['término'],
            'origen_informacion': 'DEMO',
        }],
    }), encoding='utf-8')

    name, version, cases = load_dataset(path)

    assert name == 'Dataset DEMO'
    assert version == 1
    assert cases[0].case_id == 'demo-1'


def test_loader_rechaza_ids_duplicados(tmp_path):
    case = {
        'id': 'duplicado',
        'question': 'Pregunta DEMO',
        'expected_document_urls': ['https://demo.invalid/documento'],
    }
    path = tmp_path / 'dataset.json'
    path.write_text(json.dumps({
        'name': 'Dataset inválido',
        'version': 1,
        'cases': [case, case],
    }), encoding='utf-8')

    with pytest.raises(EvaluationDatasetError, match='duplicado'):
        load_dataset(path)


def test_comando_emite_reporte_json_sin_invocar_llm(mocker):
    mocker.patch(
        'sources.management.commands.evaluar_rag.load_dataset',
        return_value=('Dataset DEMO', 1, (SimpleNamespace(),)),
    )
    evaluator = mocker.patch(
        'sources.management.commands.evaluar_rag.RAGEvaluator'
    ).return_value
    evaluator.evaluate.return_value = EvaluationReport(
        dataset='Dataset DEMO',
        version=1,
        cases=1,
        hit_rate=1.0,
        mean_reciprocal_rank=1.0,
        mean_term_coverage=1.0,
        results=(),
    )
    output = StringIO()

    call_command(
        'evaluar_rag',
        dataset='dataset-demo.json',
        stdout=output,
    )

    assert json.loads(output.getvalue())['hit_rate'] == 1.0


def test_comando_rechaza_umbral_fuera_de_rango():
    with pytest.raises(CommandError, match='entre 0 y 1'):
        call_command(
            'evaluar_rag',
            dataset='no-se-lee.json',
            fail_below_hit_rate=1.5,
        )
