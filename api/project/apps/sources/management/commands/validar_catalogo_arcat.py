import json

from django.core.management.base import BaseCommand, CommandError

from sources.catalog import CatalogValidationError, load_catalog


class Command(BaseCommand):
    help = 'Valida un catálogo candidato sin cargarlo como información oficial.'

    def add_arguments(self, parser):
        parser.add_argument('--archivo', required=True, help='Ruta al catálogo JSON.')
        parser.add_argument(
            '--require-verified',
            action='store_true',
            help='Falla si el catálogo aún requiere verificación contra las fuentes.',
        )

    def handle(self, *args, **options):
        try:
            catalog = load_catalog(options['archivo'])
        except CatalogValidationError as exc:
            raise CommandError(str(exc)) from exc
        summary = {
            'name': catalog.name,
            'schema_version': catalog.version,
            'verification_status': catalog.verification_status,
            'reviewed_at': catalog.reviewed_at,
            'institutionally_approved': bool(catalog.institutional_approval),
            'source_urls': catalog.source_urls,
            'records': len(catalog.records),
        }
        self.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2))
        if (
            options['require_verified']
            and catalog.verification_status != 'VERIFIED'
        ):
            raise CommandError(
                'El catálogo todavía requiere verificación manual contra sus fuentes.'
            )
