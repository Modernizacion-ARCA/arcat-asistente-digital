from django.core.management.base import BaseCommand, CommandError

from sources.ingestion import IngestionError, IngestionService
from sources.models import Fuente


class Command(BaseCommand):
    help = 'Descarga fuentes activas y actualiza sus documentos cuando cambia el contenido.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fuente',
            action='append',
            type=int,
            dest='fuentes',
            help='ID de una fuente a procesar; se puede repetir.',
        )

    def handle(self, *args, **options):
        fuentes = Fuente.objects.filter(
            activo=True,
            estado_verificacion=Fuente.EstadoVerificacion.VERIFICADA,
        ).order_by('prioridad', 'pk')
        if options['fuentes']:
            fuentes = fuentes.filter(pk__in=options['fuentes'])

        if not fuentes.exists():
            raise CommandError('No hay fuentes activas y verificadas para procesar.')

        service = IngestionService()
        errors = []
        for fuente in fuentes:
            try:
                result = service.ingest(fuente)
            except IngestionError as exc:
                errors.append(f'{fuente.pk}: {exc}')
                self.stderr.write(self.style.ERROR(f'{fuente}: {exc}'))
                continue
            status = 'actualizada' if result.changed else 'sin cambios'
            self.stdout.write(self.style.SUCCESS(f'{fuente}: {status}'))

        if errors:
            raise CommandError(
                f'Fallaron {len(errors)} fuente(s): {"; ".join(errors)}'
            )
