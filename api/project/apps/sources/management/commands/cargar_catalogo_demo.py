import json

from django.core.management.base import BaseCommand, CommandError

from sources.catalog import CatalogValidationError, load_catalog
from sources.catalog_demo import DemoCatalogLoader


class Command(BaseCommand):
    help = 'Carga un catálogo candidato en un espacio DEMO aislado.'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', required=True, help='Ruta al catálogo JSON.')
        parser.add_argument(
            '--confirm-demo',
            action='store_true',
            help='Confirma que los datos se usarán sólo como DEMO no oficial.',
        )

    def handle(self, *args, **options):
        if not options['confirm_demo']:
            raise CommandError(
                'Debe usar --confirm-demo para reconocer que los datos no son oficiales.'
            )
        try:
            catalog = load_catalog(options['archivo'])
        except CatalogValidationError as exc:
            raise CommandError(str(exc)) from exc
        result = DemoCatalogLoader().load(catalog)
        self.stdout.write(json.dumps({
            'records': result.records,
            'created_procedures': result.created_procedures,
            'updated_procedures': result.updated_procedures,
            'origin': 'DEMO',
            'officially_verified': False,
        }, ensure_ascii=False, indent=2))
