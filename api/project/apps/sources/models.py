from django.core.validators import RegexValidator
from django.db import models


class Fuente(models.Model):
    class Tipo(models.TextChoices):
        SITIO_WEB = 'SITIO_WEB', 'Sitio web'
        PORTAL_TRAMITES = 'PORTAL_TRAMITES', 'Portal de trámites'
        BOLETIN_OFICIAL = 'BOLETIN_OFICIAL', 'Boletín oficial'
        REPOSITORIO = 'REPOSITORIO', 'Repositorio documental'
        OTRO = 'OTRO', 'Otro'

    class OrigenInformacion(models.TextChoices):
        OFICIAL = 'OFICIAL', 'Oficial'
        DEMO = 'DEMO', 'Demo'

    class EstadoVerificacion(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        VERIFICADA = 'VERIFICADA', 'Verificada'
        RECHAZADA = 'RECHAZADA', 'Rechazada'

    class EstadoDisponibilidad(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        NO_DISPONIBLE = 'NO_DISPONIBLE', 'No disponible'
        DESCONOCIDO = 'DESCONOCIDO', 'Desconocido'

    nombre = models.CharField(max_length=250)
    url = models.URLField(max_length=1000, unique=True)
    organismo = models.ForeignKey(
        'organizations.Organismo',
        on_delete=models.PROTECT,
        related_name='fuentes',
    )
    categoria = models.ForeignKey(
        'procedures.Categoria',
        on_delete=models.PROTECT,
        related_name='fuentes',
        blank=True,
        null=True,
    )
    plataforma = models.ForeignKey(
        'procedures.Plataforma',
        on_delete=models.PROTECT,
        related_name='fuentes',
        blank=True,
        null=True,
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    origen_informacion = models.CharField(
        max_length=10,
        choices=OrigenInformacion.choices,
    )
    prioridad = models.PositiveSmallIntegerField(default=100)
    estado_verificacion = models.CharField(
        max_length=20,
        choices=EstadoVerificacion.choices,
        default=EstadoVerificacion.PENDIENTE,
    )
    fecha_ultima_consulta = models.DateTimeField(blank=True, null=True)
    fecha_actualizacion_origen = models.DateTimeField(blank=True, null=True)
    estado_disponibilidad = models.CharField(
        max_length=20,
        choices=EstadoDisponibilidad.choices,
        default=EstadoDisponibilidad.DESCONOCIDO,
    )
    activo = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('prioridad', 'nombre')
        verbose_name = 'Fuente'
        verbose_name_plural = 'Fuentes'

    def __str__(self):
        return self.nombre


class Documento(models.Model):
    class Tipo(models.TextChoices):
        PDF = 'PDF', 'PDF'
        HTML = 'HTML', 'HTML'
        INSTRUCTIVO = 'INSTRUCTIVO', 'Instructivo'
        FORMULARIO = 'FORMULARIO', 'Formulario'
        NORMATIVA = 'NORMATIVA', 'Normativa'
        GUIA = 'GUIA', 'Guía'
        MANUAL = 'MANUAL', 'Manual'
        OTRO = 'OTRO', 'Otro'

    titulo = models.CharField(max_length=300)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    fuente = models.ForeignKey(
        Fuente,
        on_delete=models.PROTECT,
        related_name='documentos',
    )
    url = models.URLField(max_length=1000)
    fecha_documento = models.DateField(blank=True, null=True)
    contenido = models.TextField(blank=True)
    texto_extraido = models.TextField(blank=True)
    checksum = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        validators=[RegexValidator(
            regex=r'^[0-9a-f]{64}$',
            message='El checksum debe ser un hash SHA-256 hexadecimal.',
        )],
    )
    metadata = models.JSONField(default=dict, blank=True)
    activo = models.BooleanField(default=True)
    tramites = models.ManyToManyField(
        'procedures.Tramite',
        related_name='documentos',
        blank=True,
    )
    servicios = models.ManyToManyField(
        'procedures.Servicio',
        related_name='documentos',
        blank=True,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('titulo',)
        constraints = [
            models.UniqueConstraint(
                fields=('fuente', 'url'),
                name='unique_documento_por_fuente_url',
            ),
        ]
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

    def __str__(self):
        return self.titulo
