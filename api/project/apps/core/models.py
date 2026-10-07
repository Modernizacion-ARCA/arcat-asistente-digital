from django.db import models
from django.utils import timezone

from core.querysets import PublicadoQuerySet


class Publicado(models.Model):
    class Meta:
        abstract = True

    publicado = models.DateTimeField(blank=True, null=True, editable=False, default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True, editable=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True, editable=False)

    objects = PublicadoQuerySet.as_manager()

    def publicar(self, estado=True):
        self.publicado = timezone.now() if estado else None
        self.save()


class LLMDailyQuota(models.Model):
    fecha = models.DateField(unique=True)
    solicitudes = models.PositiveIntegerField(default=0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-fecha',)
        verbose_name = 'Cupo diario LLM'
        verbose_name_plural = 'Cupos diarios LLM'

    def __str__(self):
        return f'{self.fecha}: {self.solicitudes} solicitudes'


class LLMRequestLog(models.Model):
    class Estado(models.TextChoices):
        EXITOSA = 'EXITOSA', 'Exitosa'
        ERROR = 'ERROR', 'Error'
        BLOQUEADA = 'BLOQUEADA', 'Bloqueada'

    proveedor = models.CharField(max_length=50)
    modelo = models.CharField(max_length=255)
    estado = models.CharField(max_length=12, choices=Estado.choices)
    posicion_fallback = models.PositiveSmallIntegerField(default=0)
    tokens_entrada = models.PositiveIntegerField(blank=True, null=True)
    tokens_salida = models.PositiveIntegerField(blank=True, null=True)
    duracion_ms = models.PositiveIntegerField(default=0)
    codigo_error = models.CharField(max_length=100, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('-fecha_creacion',)
        verbose_name = 'Solicitud LLM'
        verbose_name_plural = 'Solicitudes LLM'

    def __str__(self):
        return f'{self.modelo}: {self.get_estado_display()}'
