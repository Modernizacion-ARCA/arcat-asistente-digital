import json
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from sources.models import DocumentChunk, Fuente, KnowledgeUpdateRun


class Command(BaseCommand):
    help = 'Informa el estado operativo de la base de conocimiento en JSON.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-hours',
            type=int,
            default=24,
            help='Antigüedad máxima aceptable para la última ejecución exitosa.',
        )

    def handle(self, *args, **options):
        max_hours = options['max_hours']
        if max_hours <= 0:
            raise CommandError('--max-hours debe ser un entero mayor que cero.')

        now = timezone.now()
        threshold = now - timedelta(hours=max_hours)
        runs = KnowledgeUpdateRun.objects.all()
        latest = runs.first()
        last_success = runs.filter(
            estado=KnowledgeUpdateRun.Estado.EXITOSA,
            fecha_fin__isnull=False,
        ).first()
        official_sources = Fuente.objects.filter(
            activo=True,
            origen_informacion=Fuente.OrigenInformacion.OFICIAL,
            estado_verificacion=Fuente.EstadoVerificacion.VERIFICADA,
        )
        chunks = DocumentChunk.objects.filter(
            documento__activo=True,
            documento__fuente__in=official_sources,
        )

        reasons = []
        if last_success is None:
            reasons.append('no_successful_run')
        elif last_success.fecha_fin < threshold:
            reasons.append('last_success_is_stale')
        if latest and latest.estado == KnowledgeUpdateRun.Estado.ERROR:
            reasons.append('latest_run_failed')
        if (
            latest
            and latest.estado == KnowledgeUpdateRun.Estado.EN_CURSO
            and latest.fecha_inicio < threshold
        ):
            reasons.append('latest_run_is_stalled')

        report = {
            'healthy': not reasons,
            'checked_at': now.isoformat(),
            'max_hours': max_hours,
            'reasons': reasons,
            'latest_run': self._serialize_run(latest),
            'last_success_at': (
                last_success.fecha_fin.isoformat() if last_success else None
            ),
            'official_verified_sources': official_sources.count(),
            'indexed_documents': chunks.values('documento_id').distinct().count(),
            'chunks': chunks.count(),
        }
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
        if reasons:
            raise CommandError(
                'La base de conocimiento requiere atención: '
                f'{", ".join(reasons)}.'
            )

    @staticmethod
    def _serialize_run(run):
        if run is None:
            return None
        return {
            'id': run.pk,
            'status': run.estado,
            'started_at': run.fecha_inicio.isoformat(),
            'finished_at': run.fecha_fin.isoformat() if run.fecha_fin else None,
            'sources': run.fuentes_total,
            'updated': run.documentos_actualizados,
            'unchanged': run.documentos_sin_cambios,
            'indexed': run.documentos_indexados,
            'errors': run.errores,
        }
