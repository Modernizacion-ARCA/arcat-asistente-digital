import hashlib
import json
from dataclasses import dataclass

from django.db import transaction
from django.utils.text import slugify

from organizations.models import Area, Organismo
from procedures.models import Categoria, Plataforma, Tramite

from .models import Documento, Fuente


@dataclass(frozen=True)
class DemoLoadResult:
    records: int
    created_procedures: int
    updated_procedures: int


def _render_record(record):
    lines = [
        f'Trámite: {record["nombre"]}',
        f'Organismo declarado: {record["organismo"]}',
        f'Área declarada: {record["area"]}',
        f'Categoría: {record["categoria"]}',
        f'Canal: {record["canal"]}',
        f'Descripción: {record["descripcion"]}',
    ]
    for label, field in (
        ('Requisitos', 'requisitos'),
        ('Documentación', 'documentacion'),
        ('Pasos', 'pasos'),
    ):
        if record[field]:
            lines.append(f'{label}: ' + '; '.join(record[field]))
    if record['costo']:
        lines.append(f'Costo: {record["costo"]}')
    if record['plazo']:
        lines.append(f'Plazo: {record["plazo"]}')
    return '\n'.join(lines)


class DemoCatalogLoader:
    """Load candidate records into an isolated DEMO namespace, never as official data."""

    source_url = 'https://demo.invalid/catalog/arcat-tramites-revisados-v2/'

    @transaction.atomic
    def load(self, catalog):
        organismo, _ = Organismo.objects.update_or_create(
            nombre='ARCAT DEMO',
            defaults={
                'descripcion': 'Organismo ficticio para pruebas del catálogo candidato.',
                'activo': False,
            },
        )
        plataforma, _ = Plataforma.objects.update_or_create(
            nombre='TAD DEMO',
            defaults={'descripcion': 'Canal ficticio para pruebas.', 'activo': False},
        )
        fuente, _ = Fuente.objects.update_or_create(
            url=self.source_url,
            defaults={
                'nombre': 'Catálogo candidato ARCAT (DEMO)',
                'organismo': organismo,
                'tipo': Fuente.Tipo.OTRO,
                'origen_informacion': Fuente.OrigenInformacion.DEMO,
                'estado_verificacion': Fuente.EstadoVerificacion.VERIFICADA,
                'estado_disponibilidad': Fuente.EstadoDisponibilidad.DISPONIBLE,
                'activo': True,
                'metadata': {
                    'catalog_name': catalog.name,
                    'catalog_version': catalog.version,
                    'source_verification_status': catalog.verification_status,
                },
            },
        )
        created_count = 0
        updated_count = 0
        for record in catalog.records:
            category_slug = f'demo-{slugify(record["categoria"])}'
            category, _ = Categoria.objects.update_or_create(
                slug=category_slug,
                defaults={
                    'nombre': f'{record["categoria"]} (DEMO)',
                    'descripcion': 'Clasificación ficticia aislada.',
                    'activo': False,
                },
            )
            area = None
            if ' / ' not in record['area']:
                area, _ = Area.objects.get_or_create(
                    organismo=organismo,
                    nombre=f'{record["area"]} (DEMO)',
                    defaults={'activo': False},
                )
            tramite, created = Tramite.objects.update_or_create(
                slug=f'demo-{record["id"]}',
                defaults={
                    'nombre': record['nombre'],
                    'descripcion': record['descripcion'],
                    'organismo': organismo,
                    'area': area,
                    'categoria': category,
                    'plataforma': plataforma,
                    'requisitos': '\n'.join(record['requisitos']),
                    'documentacion': '\n'.join(record['documentacion']),
                    'pasos': '\n'.join(record['pasos']),
                    'costo': record['costo'] or '',
                    'plazo': record['plazo'] or '',
                    'modalidad': Tramite.Modalidad.ONLINE,
                    'url_inicio': record['url_tad'],
                    'observaciones': (
                        'Registro DEMO pendiente de aprobación institucional.'
                    ),
                    'activo': False,
                },
            )
            created_count += int(created)
            updated_count += int(not created)
            text = _render_record(record)
            document, _ = Documento.objects.update_or_create(
                fuente=fuente,
                url=f'https://demo.invalid/catalog/{record["id"]}/',
                defaults={
                    'titulo': f'{record["nombre"]} [DEMO]',
                    'tipo': Documento.Tipo.OTRO,
                    'contenido': json.dumps(record, ensure_ascii=False, sort_keys=True),
                    'texto_extraido': text,
                    'checksum': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                    'metadata': {
                        'catalog_record': record,
                        'candidate_source_url': record['url_tad'],
                        'not_officially_verified': True,
                    },
                    'activo': True,
                },
            )
            document.tramites.set((tramite,))
        return DemoLoadResult(
            records=len(catalog.records),
            created_procedures=created_count,
            updated_procedures=updated_count,
        )
