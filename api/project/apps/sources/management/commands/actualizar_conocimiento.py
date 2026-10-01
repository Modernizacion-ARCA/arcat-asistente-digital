import json

from django.core.management.base import BaseCommand, CommandError

from sources.indexing import DocumentIndexer, IndexingError
from sources.ingestion import IngestionError, IngestionService
from sources.models import Fuente


class Command(BaseCommand):
    help = 'Ingiere fuentes oficiales y reindexa únicamente documentos modificados.'

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

        ingestion = IngestionService()
        indexer = DocumentIndexer()
        summary = {
            'sources': sources.count(),
            'ingested': 0,
            'unchanged': 0,
            'indexed': 0,
            'errors': [],
        }
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

        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
        if summary['errors']:
            raise CommandError(
                f'Fallaron {len(summary["errors"])} fuente(s); revise stderr.'
            )
