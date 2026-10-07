import hashlib
import ipaddress
import socket
from dataclasses import dataclass
from datetime import timezone as datetime_timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.db import transaction
from django.utils import timezone
from pypdf import PdfReader

from .models import Documento, Fuente


class IngestionError(Exception):
    """Error controlado al descargar o procesar una fuente."""


@dataclass(frozen=True)
class FetchResult:
    body: bytes
    final_url: str
    content_type: str
    charset: str = ''
    etag: str = ''
    last_modified: str = ''


@dataclass(frozen=True)
class IngestionResult:
    documento: Documento
    changed: bool


def validate_public_url(url):
    parsed = urlparse(url)
    if (
        parsed.scheme not in {'http', 'https'}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise IngestionError('La fuente debe usar una URL pública HTTP o HTTPS.')

    try:
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        addresses = socket.getaddrinfo(parsed.hostname, port)
    except (socket.gaierror, ValueError) as exc:
        raise IngestionError('No se pudo resolver el host de la fuente.') from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise IngestionError('La fuente no puede apuntar a una red privada o reservada.')


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class UrlFetcher:
    max_bytes = 20 * 1024 * 1024
    timeout = 20

    def fetch(self, url):
        validate_public_url(url)
        request = Request(url, headers={'User-Agent': 'ARCAT-Asistente/1.0'})
        try:
            with build_opener(SafeRedirectHandler).open(
                request, timeout=self.timeout
            ) as response:
                body = response.read(self.max_bytes + 1)
                if len(body) > self.max_bytes:
                    raise IngestionError('La fuente supera el límite de 20 MB.')
                return FetchResult(
                    body=body,
                    final_url=response.geturl(),
                    content_type=response.headers.get_content_type(),
                    charset=response.headers.get_content_charset() or '',
                    etag=response.headers.get('ETag', ''),
                    last_modified=response.headers.get('Last-Modified', ''),
                )
        except (HTTPError, URLError, TimeoutError) as exc:
            raise IngestionError(f'No se pudo descargar la fuente: {exc}') from exc


class HTMLTextExtractor(HTMLParser):
    ignored_tags = {'script', 'style', 'noscript'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored_tags:
            self.ignored_depth += 1

    def handle_endtag(self, tag):
        if tag in self.ignored_tags and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data):
        if not self.ignored_depth:
            value = ' '.join(data.split())
            if value:
                self.parts.append(value)

    def text(self):
        return '\n'.join(self.parts)


def extract_content(result):
    content_type = result.content_type.lower()
    if content_type in {'text/html', 'application/xhtml+xml'}:
        source = result.body.decode(result.charset or 'utf-8', errors='replace')
        parser = HTMLTextExtractor()
        parser.feed(source)
        return Documento.Tipo.HTML, source, parser.text()
    if content_type == 'application/pdf':
        try:
            pages = PdfReader(BytesIO(result.body)).pages
            text = '\n\n'.join(page.extract_text() or '' for page in pages).strip()
        except Exception as exc:
            raise IngestionError('No se pudo extraer el texto del PDF.') from exc
        return Documento.Tipo.PDF, '', text
    if content_type.startswith('text/plain'):
        text = result.body.decode(result.charset or 'utf-8', errors='replace')
        return Documento.Tipo.OTRO, text, text
    raise IngestionError(f'Tipo de contenido no admitido: {result.content_type}.')


def parse_last_modified(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if timezone.is_naive(parsed):
        parsed = parsed.replace(tzinfo=datetime_timezone.utc)
    return parsed


class IngestionService:
    def __init__(self, fetcher=None):
        self.fetcher = fetcher or UrlFetcher()

    def ingest(self, fuente):
        consulted_at = timezone.now()
        try:
            fetched = self.fetcher.fetch(fuente.url)
            document_type, content, extracted_text = extract_content(fetched)
        except IngestionError:
            fuente.fecha_ultima_consulta = consulted_at
            fuente.estado_disponibilidad = Fuente.EstadoDisponibilidad.NO_DISPONIBLE
            fuente.save(update_fields=(
                'fecha_ultima_consulta',
                'estado_disponibilidad',
                'fecha_actualizacion',
            ))
            raise

        checksum = hashlib.sha256(fetched.body).hexdigest()
        with transaction.atomic():
            documento, created = Documento.objects.get_or_create(
                fuente=fuente,
                url=fuente.url,
                defaults={'titulo': fuente.nombre, 'tipo': document_type},
            )
            changed = created or documento.checksum != checksum
            if changed:
                documento.titulo = fuente.nombre
                documento.tipo = document_type
                documento.contenido = content
                documento.texto_extraido = extracted_text
                documento.checksum = checksum
                documento.metadata = {
                    **documento.metadata,
                    'ingesta': {
                        'content_type': fetched.content_type,
                        'charset': fetched.charset,
                        'etag': fetched.etag,
                        'last_modified': fetched.last_modified,
                        'url_final': fetched.final_url,
                    },
                }
                documento.full_clean()
                documento.save()

            fuente.fecha_ultima_consulta = consulted_at
            source_updated_at = parse_last_modified(fetched.last_modified)
            if source_updated_at:
                fuente.fecha_actualizacion_origen = source_updated_at
            elif changed:
                fuente.fecha_actualizacion_origen = consulted_at
            fuente.estado_disponibilidad = Fuente.EstadoDisponibilidad.DISPONIBLE
            fuente.save(update_fields=(
                'fecha_ultima_consulta',
                'fecha_actualizacion_origen',
                'estado_disponibilidad',
                'fecha_actualizacion',
            ))
        return IngestionResult(documento=documento, changed=changed)
