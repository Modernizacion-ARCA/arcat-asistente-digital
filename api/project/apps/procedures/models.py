from django.core.exceptions import ValidationError
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ('nombre',)
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Plataforma(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    url = models.URLField(max_length=500, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ('nombre',)
        verbose_name = 'Plataforma'
        verbose_name_plural = 'Plataformas'

    def __str__(self):
        return self.nombre


class GestionBase(models.Model):
    class Modalidad(models.TextChoices):
        ONLINE = 'ONLINE', 'En línea'
        PRESENCIAL = 'PRESENCIAL', 'Presencial'
        MIXTA = 'MIXTA', 'Mixta'
        NO_INFORMADA = 'NO_INFORMADA', 'No informada'

    nombre = models.CharField(max_length=250)
    slug = models.SlugField(max_length=270, unique=True)
    descripcion = models.TextField()
    organismo = models.ForeignKey(
        'organizations.Organismo',
        on_delete=models.PROTECT,
        related_name='%(class)ss',
    )
    area = models.ForeignKey(
        'organizations.Area',
        on_delete=models.PROTECT,
        related_name='%(class)ss',
        blank=True,
        null=True,
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='%(class)ss',
        blank=True,
        null=True,
    )
    plataforma = models.ForeignKey(
        Plataforma,
        on_delete=models.PROTECT,
        related_name='%(class)ss',
        blank=True,
        null=True,
    )
    requisitos = models.TextField(blank=True)
    documentacion = models.TextField(blank=True)
    pasos = models.TextField(blank=True)
    costo = models.TextField(blank=True)
    plazo = models.TextField(blank=True)
    modalidad = models.CharField(
        max_length=20,
        choices=Modalidad.choices,
        default=Modalidad.NO_INFORMADA,
    )
    autenticacion_requerida = models.BooleanField(default=False)
    metodo_autenticacion = models.CharField(max_length=200, blank=True)
    url_inicio = models.URLField(max_length=500, blank=True)
    url_instructivo = models.URLField(max_length=500, blank=True)
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_publicacion = models.DateField(blank=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ('nombre',)

    def clean(self):
        super().clean()
        if self.area_id and self.organismo_id:
            area_organismo_id = self.area.organismo_id
            if area_organismo_id != self.organismo_id:
                raise ValidationError(
                    {'area': 'El área debe pertenecer al organismo seleccionado.'}
                )
        if self.metodo_autenticacion and not self.autenticacion_requerida:
            raise ValidationError({
                'autenticacion_requerida': (
                    'Debe indicarse que requiere autenticación cuando se informa un método.'
                )
            })

    def __str__(self):
        return self.nombre


class Tramite(GestionBase):
    tipo = models.CharField(max_length=120, blank=True)

    class Meta(GestionBase.Meta):
        verbose_name = 'Trámite'
        verbose_name_plural = 'Trámites'


class Servicio(GestionBase):
    class Tipo(models.TextChoices):
        CONSULTA_DEUDA = 'CONSULTA_DEUDA', 'Consulta de deuda'
        PAGO = 'PAGO', 'Pago de impuestos'
        VENCIMIENTOS = 'VENCIMIENTOS', 'Consulta de vencimientos'
        BOLETA = 'BOLETA', 'Generación de boleta'
        LIBRE_DEUDA = 'LIBRE_DEUDA', 'Libre deuda'
        OTRO = 'OTRO', 'Otro'

    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.OTRO)
    impuesto = models.CharField(max_length=150, blank=True)
    conceptos_disponibles = models.TextField(blank=True)
    consulta_deuda = models.TextField(blank=True)
    generacion_boleta = models.TextField(blank=True)
    medios_pago = models.TextField(blank=True)
    instrucciones = models.TextField(blank=True)

    class Meta(GestionBase.Meta):
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
