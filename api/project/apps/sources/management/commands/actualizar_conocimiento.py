import json
from uuid import uuid4

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from sources.indexing import DocumentIndexer, IndexingError
from sources.ingestion import IngestionError, IngestionService
from sources.models import Fuente, KnowledgeUpdateRun


class Command(BaseCommand):
    help = 'Ingiere fuentes oficiales y reindexa únicamente documentos modificados.'
    lock_key = 'sources:actualizar_conocimiento:lock'
    lock_timeout = 60 * 60

    def add_arguments(self, parser):
        parser.add_argument(
            '--fuente',
            action='append',
            type=int,
            dest='fuentes',
            help='ID de una fuente a actualizar; se puede repetir.',
        )
        parser.add_argument(
            '--force-index',
            action='store_true',
            help='Reindexa aunque el checksum del documento no haya cambiado.',
        )

    def handle(self, *args, **options):
        lock_token = uuid4().hex
        try:
            acquired = cache.add(
                self.lock_key,
                lock_token,
                timeout=self.lock_timeout,
            )
        except Exception as exc:
            raise CommandError(
                'No se pudo comprobar el bloqueo de actualización compartido.'
            ) from exc
        if not acquired:
            raise CommandError(
                'Ya existe otra actualización de conocimiento en ejecución.'
            )

        try:
            return self._update(options)
        finally:
            self._release_lock(lock_token)

    def _update(self, options):
        sources = Fuente.objects.filter(
            activo=True,
            origen_informacion=Fuente.OrigenInformacion.OFICIAL,
            estado_verificacion=Fuente.EstadoVerificacion.VERIFICADA,
        ).order_by('prioridad', 'pk')
        if options['fuentes']:
            sources = sources.filter(pk__in=options['fuentes'])
        if not sources.exists():
            raise CommandError(
                'No hay fuentes oficiales, activas y verificadas para actualizar.'
            )

        run = KnowledgeUpdateRun.objects.create(fuentes_total=sources.count())
        summary = {
            'run_id': run.pk,
            'sources': run.fuentes_total,
            'ingested': 0,
            'unchanged': 0,
            'indexed': 0,
            'errors': [],
        }
        try:
            ingestion = IngestionService()
            indexer = DocumentIndexer()
            for source in sources.iterator():
                try:
                    ingestion_result = ingestion.ingest(source)
                    summary['ingested'] += int(ingestion_result.changed)
                    summary['unchanged'] += int(not ingestion_result.changed)
                    index_result = indexer.index(
                        ingestion_result.documento,
                        force=options['force_index'],
                    )
                    summary['indexed'] += int(index_result.changed)
                except (IngestionError, IndexingError, ValueError) as exc:
                    summary['errors'].append({
                        'source_id': source.pk,
                        'error': type(exc).__name__,
                    })
                    self.stderr.write(self.style.ERROR(
                        f'Fuente {source.pk} ({source.nombre}): {exc}'
                    ))
        except Exception as exc:
            summary['errors'].append({'error': type(exc).__name__})
            self._finish_run(run, summary)
            raise

        self._finish_run(run, summary)

        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
        if summary['errors']:
            raise CommandError(
                f'Fallaron {len(summary["errors"])} fuente(s); revise stderr.'
            )

    def _finish_run(self, run, summary):
        run.estado = (
            KnowledgeUpdateRun.Estado.ERROR
            if summary['errors']
            else KnowledgeUpdateRun.Estado.EXITOSA
        )
        run.documentos_actualizados = summary['ingested']
        run.documentos_sin_cambios = summary['unchanged']
        run.documentos_indexados = summary['indexed']
        run.errores = len(summary['errors'])
        run.detalle_errores = summary['errors']
        run.fecha_fin = timezone.now()
        run.save(update_fields=(
            'estado',
            'documentos_actualizados',
            'documentos_sin_cambios',
            'documentos_indexados',
            'errores',
            'detalle_errores',
            'fecha_fin',
        ))

    def _release_lock(self, lock_token):
        try:
            if cache.get(self.lock_key) == lock_token:
                cache.delete(self.lock_key)
        except Exception:
            self.stderr.write(self.style.WARNING(
                'No se pudo liberar el bloqueo; expirará automáticamente.'
            ))
