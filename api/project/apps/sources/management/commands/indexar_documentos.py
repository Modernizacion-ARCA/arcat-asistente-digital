from django.core.management.base import BaseCommand, CommandError

from sources.indexing import DocumentIndexer, IndexingError
from sources.models import Documento, Fuente


class Command(BaseCommand):
    help = 'Divide documentos verificados y genera embeddings locales para pgvector.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--documento',
            action='append',
            type=int,
            dest='documentos',
            help='ID de un documento a indexar; se puede repetir.',
        )

    def handle(self, *args, **options):
        documents = Documento.objects.filter(
            activo=True,
            fuente__activo=True,
            fuente__estado_verificacion=Fuente.EstadoVerificacion.VERIFICADA,
        ).select_related('fuente').order_by('pk')
        if options['documentos']:
            documents = documents.filter(pk__in=options['documentos'])
        if not documents.exists():
            raise CommandError('No hay documentos activos y verificados para indexar.')

        indexer = DocumentIndexer()
        errors = []
        for document in documents:
            try:
                result = indexer.index(document)
            except (IndexingError, ValueError) as exc:
                errors.append(f'{document.pk}: {exc}')
                self.stderr.write(self.style.ERROR(f'{document}: {exc}'))
                continue
            status = 'actualizado' if result.changed else 'sin cambios'
            self.stdout.write(self.style.SUCCESS(
                f'{document}: {status} ({result.chunks} fragmentos)'
            ))

        if errors:
            raise CommandError(
                f'Fallaron {len(errors)} documento(s): {"; ".join(errors)}'
            )
