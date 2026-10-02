import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


class CatalogValidationError(ValueError):
    """Raised when a candidate institutional catalog is not structurally safe."""


@dataclass(frozen=True)
class CatalogDataset:
    name: str
    version: int
    verification_status: str
    source_urls: tuple[str, ...]
    records: tuple[dict, ...]


REQUIRED_STRING_FIELDS = (
    'id',
    'nombre',
    'organismo',
    'area',
    'categoria',
    'canal',
    'descripcion',
    'url_tad',
    'fuente',
)
LIST_FIELDS = ('requisitos', 'documentacion', 'pasos')
ALLOWED_SOURCE_HOSTS = {
    'arcat.gob.ar',
    'www.arcat.gob.ar',
    'dgrentas.arcat.gob.ar',
    'tad.catamarca.gob.ar',
}


def _non_empty_string(value, field, record_id):
    if not isinstance(value, str) or not value.strip():
        raise CatalogValidationError(
            f'El registro {record_id!r} requiere un texto válido en {field}.'
        )
    return value.strip()


def _validate_url(value, field, record_id):
    url = _non_empty_string(value, field, record_id)
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
        raise CatalogValidationError(
            f'El registro {record_id!r} contiene una URL no permitida en {field}.'
        )
    return url


def load_catalog(path):
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogValidationError(f'No se pudo leer el catálogo: {exc}') from exc
    if not isinstance(payload, dict):
        raise CatalogValidationError('La raíz del catálogo debe ser un objeto JSON.')
    if payload.get('schema_version') != 1:
        raise CatalogValidationError('El catálogo debe usar schema_version=1.')
    name = _non_empty_string(payload.get('name'), 'name', 'dataset')
    status = payload.get('verification_status')
    if status not in {'PENDING_SOURCE_VERIFICATION', 'VERIFIED'}:
        raise CatalogValidationError('verification_status no es válido.')
    raw_sources = payload.get('source_urls')
    if not isinstance(raw_sources, list) or not raw_sources:
        raise CatalogValidationError('source_urls debe contener al menos una URL.')
    source_urls = tuple(
        _validate_url(url, 'source_urls', 'dataset') for url in raw_sources
    )
    raw_records = payload.get('records')
    if not isinstance(raw_records, list) or not raw_records:
        raise CatalogValidationError('records debe contener al menos un trámite.')

    records = []
    seen_ids = set()
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            raise CatalogValidationError('Cada trámite debe ser un objeto JSON.')
        record_id = _non_empty_string(raw_record.get('id'), 'id', 'sin-id')
        if record_id in seen_ids:
            raise CatalogValidationError(f'El id {record_id!r} está duplicado.')
        seen_ids.add(record_id)
        record = dict(raw_record)
        for field in REQUIRED_STRING_FIELDS:
            record[field] = _non_empty_string(record.get(field), field, record_id)
        record['url_tad'] = _validate_url(record['url_tad'], 'url_tad', record_id)
        for field in LIST_FIELDS:
            if not isinstance(record.get(field), list):
                raise CatalogValidationError(
                    f'El campo {field} debe ser una lista en {record_id!r}.'
                )
        if record.get('tad_id') is not None and not isinstance(record['tad_id'], str):
            raise CatalogValidationError(f'tad_id no es válido en {record_id!r}.')
        for field in ('costo', 'plazo'):
            if record.get(field) is not None and not isinstance(record[field], str):
                raise CatalogValidationError(
                    f'El campo {field} debe ser texto o null en {record_id!r}.'
                )
        records.append(record)
    return CatalogDataset(
        name=name,
        version=payload['schema_version'],
        verification_status=status,
        source_urls=source_urls,
        records=tuple(records),
    )
