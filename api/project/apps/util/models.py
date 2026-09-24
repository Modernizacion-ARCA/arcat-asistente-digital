from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class RedSocial(models.Model):
    class Meta:
        verbose_name = 'Red social'
        verbose_name_plural = 'Redes sociales'

    FACEBOOK = 'fbk'
    INSTAGRAM = 'insta'
    LINKEDIN = 'lnkd'
    TWITTER = 'twt'
    WHATSAPP = 'wsp'
    YOUTUBE = 'ytb'
    SNAPCHAT = 'snap'
    TIKTOK = 'tiktok'
    PINTEREST = 'pin'

    REDES = (
        (FACEBOOK, 'Facebook'),
        (INSTAGRAM, 'Instagram'),
        (LINKEDIN, 'Linkedin'),
        (TWITTER, 'Twitter/X'),
        (WHATSAPP, 'WhatsApp'),
        (YOUTUBE, 'YouTube'),
        (SNAPCHAT, 'Snapchat'),
        (TIKTOK, 'TikTok'),
        (PINTEREST, 'Pinterest')
    )
    red_social = models.CharField(max_length=6, choices=REDES, verbose_name='Red Social')
    url = models.URLField(max_length=200)
    content_type = models.ForeignKey(
        ContentType,
        # limit_choices_to={'model__in': ('hotel', 'agency', 'transport')     # Add more after.},
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')


class Telefono(models.Model):
    class Meta:
        verbose_name = 'Teléfono'
        verbose_name_plural = 'Teléfonos'

    CELULAR = 'celu'
    TELEFONO_FIJO = 'fijo'
    WHATSAPP = 'wsp'

    TIPOS = (
        (CELULAR, 'Celular'),
        (TELEFONO_FIJO, 'Teléfono de Linea'),
        (WHATSAPP, 'Whatsapp')
    )

    type = models.CharField(max_length=4, choices=TIPOS, verbose_name='Tipo de teléfono',
                            default=TELEFONO_FIJO)
    contact_point = models.CharField(max_length=40, verbose_name='Número')
    content_type = models.ForeignKey(
        ContentType,
        # limit_choices_to={'model__in': ('hotel', 'agency', 'transport')     # Add more after.},
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return "(%s) %s" % (self.get_type_display(), self.contact_point)


class Mail(models.Model):
    class Meta:
        verbose_name = 'Correo electrónico'
        verbose_name_plural = 'Correos electrónicos'

    CONSULTA = 'consulta'
    RECLAMO = 'reclamo'
    SUGERENCIA = 'sugerencia'

    TIPOS = (
        (CONSULTA, 'Consulta'),
        (RECLAMO, 'Reclamo'),
        (SUGERENCIA, 'Sugerencia')

    )

    type = models.CharField(max_length=10, choices=TIPOS, verbose_name='Tipo de teléfono',
                            default=CONSULTA)
    contact_point = models.EmailField(max_length=40, verbose_name='Correo Electrónico')
    content_type = models.ForeignKey(
        ContentType,
        # limit_choices_to={'model__in': ('hotel', 'agency', 'transport')     # Add more after.},
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return "(%s) %s" % (self.get_type_display(), self.contact_point)


class Ubicacion(MPTTModel, models.Model):
    class Meta:
        verbose_name = 'Ubicación '
        verbose_name_plural = 'Ubicaciones'
        constraints = [
            models.UniqueConstraint(
                fields=['nombre', 'parent'],
                name='unique_ubicacion'
            )
        ]

    PAIS = 'PA'
    PROVINCIA = 'PR'
    DEPARTAMENTO = 'DE'
    MUNICIPIO = 'MU'
    LOCALIDAD = 'LO'
    BARRIO = 'BA'

    TIPOS_UBICACIONES = (
        (PAIS, 'Pais'),
        (PROVINCIA, 'Provincia'),
        (DEPARTAMENTO, 'Departamento'),
        (MUNICIPIO, 'Municipio'),
        (LOCALIDAD, 'Localidad'),
        (BARRIO, 'Barrio')
    )

    tipo = models.CharField(max_length=2, choices=TIPOS_UBICACIONES, default=LOCALIDAD)
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Ejemplo: SAN ISIDRO'
    )
    parent = TreeForeignKey(
        'self',
        blank=True, null=True,
        on_delete=models.CASCADE,
        db_index=True,
        verbose_name='Ubicación Padre',
        help_text='Ejemplo: VALLE VIEJO'
    )

    def __str__(self):
        nombre = f'{self.nombre}'
        if self.parent_id:
            nombre = f'{self.nombre} -> {self.parent.nombre}'

        return nombre

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.upper()
        super(Ubicacion, self).save(*args, **kwargs)

    @classmethod
    def obtener_crear_ubicacion_temporal(cls):
        ubicacion, _ = cls.objects.get_or_create(nombre='ubicacion-temporal', tipo=cls.PROVINCIA)
        return ubicacion

    @classmethod
    def obtener_departamentos_catamarca(cls):
        queryset = cls.objects.all()
        try:
            provincia_catamarca = cls.objects.get(nombre='CATAMARCA', tipo=cls.PROVINCIA)
        except cls.DoesNotExist:
            queryset = cls.objects.none()

        if queryset.exists():
            queryset = queryset.filter(parent=provincia_catamarca, tipo=cls.DEPARTAMENTO)
        return queryset

    @classmethod
    def obtener_localidades_catamarca(cls):
        queryset = cls.objects.all()
        try:
            provincia_catamarca = cls.objects.get(tipo=Ubicacion.PROVINCIA, nombre='CATAMARCA')
        except cls.DoesNotExist:
            queryset = cls.objects.none()
        if queryset.exists():
            queryset = queryset.filter(parent__parent=provincia_catamarca, tipo=Ubicacion.LOCALIDAD)
        return queryset

    @staticmethod
    def autocomplete_search_fields():
        return 'nombre',
