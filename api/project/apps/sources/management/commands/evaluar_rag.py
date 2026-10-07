import json

from django.core.management.base import BaseCommand, CommandError

from sources.evaluation import EvaluationDatasetError, RAGEvaluator, load_dataset


class Command(BaseCommand):
    help = 'Evalúa recuperación RAG sin invocar al LLM ni generar cargos.'

    def add_arguments(self, parser):
        parser.add_argument('--dataset', required=True, help='Ruta al dataset JSON.')
        parser.add_argument(
            '--fail-below-hit-rate',
            type=float,
            help='Finaliza con error si hit_rate es menor al valor indicado (0 a 1).',
        )

    def handle(self, *args, **options):
        threshold = options['fail_below_hit_rate']
        if threshold is not None and not 0 <= threshold <= 1:
            raise CommandError('--fail-below-hit-rate debe estar entre 0 y 1.')
        try:
            name, version, cases = load_dataset(options['dataset'])
        except EvaluationDatasetError as exc:
            raise CommandError(str(exc)) from exc

        report = RAGEvaluator().evaluate(name, version, cases)
        self.stdout.write(json.dumps(
            report.to_dict(),
            ensure_ascii=False,
            indent=2,
        ))
        if threshold is not None and report.hit_rate < threshold:
            raise CommandError(
                f'hit_rate={report.hit_rate:.4f} es menor que {threshold:.4f}.'
            )
