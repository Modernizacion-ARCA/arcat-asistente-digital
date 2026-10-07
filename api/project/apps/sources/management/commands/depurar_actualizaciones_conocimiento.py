import json
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from sources.models import KnowledgeUpdateRun


class Command(BaseCommand):
    help = 'Depura el historial antiguo de actualizaciones de conocimiento.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Conserva registros iniciados durante esta cantidad de días.',
        )
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Confirma la eliminación; sin esta opción sólo informa candidatos.',
        )

    def handle(self, *args, **options):
        days = options['days']
        if days <= 0:
            raise CommandError('--days debe ser un entero mayor que cero.')

        cutoff = timezone.now() - timedelta(days=days)
        completed = KnowledgeUpdateRun.objects.exclude(
            estado=KnowledgeUpdateRun.Estado.EN_CURSO,
        )
        protected_ids = set()
        latest_completed = completed.first()
        latest_success = completed.filter(
            estado=KnowledgeUpdateRun.Estado.EXITOSA,
        ).first()
        if latest_completed:
            protected_ids.add(latest_completed.pk)
        if latest_success:
            protected_ids.add(latest_success.pk)

        candidates = completed.filter(fecha_inicio__lt=cutoff).exclude(
            pk__in=protected_ids,
        )
        candidate_count = candidates.count()
        deleted_runs = 0
        if options['execute'] and candidate_count:
            with transaction.atomic():
                deleted_runs, _ = candidates.delete()

        report = {
            'executed': options['execute'],
            'retention_days': days,
            'cutoff': cutoff.isoformat(),
            'candidates': candidate_count,
            'deleted_runs': deleted_runs,
            'protected_run_ids': sorted(protected_ids),
        }
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
