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
