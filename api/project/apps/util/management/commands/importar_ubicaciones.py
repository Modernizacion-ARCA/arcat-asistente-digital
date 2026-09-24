import json

from django.conf import settings
from django.core.management.base import BaseCommand

from util.models import Ubicacion

UBICACION_DUMPS = 'ubicaciones.json'

cache_provincias = {}
cache_departamentos = {}


def obtener_o_crear_provincia(nombre, id_provincia):
    if id_provincia not in cache_provincias:
        provincia, creada = Ubicacion.objects.get_or_create(
            nombre=nombre,
            tipo=Ubicacion.PROVINCIA
        )

        cache_provincias[id_provincia] = provincia
        if creada:
            print(f'Se creó la provincia {provincia}')

    return cache_provincias[id_provincia]


def obtener_o_crear_departamento(nombre, provincia, id_departamento, id_provincia):
    if id_departamento not in cache_departamentos:
        departamento, creada = Ubicacion.objects.get_or_create(
            tipo=Ubicacion.DEPARTAMENTO,
            nombre=nombre,
            parent=obtener_o_crear_provincia(provincia, id_provincia)
        )

        cache_departamentos[id_departamento] = departamento
        if creada:
            print(f'Se creó el departamento {departamento}')

    return cache_departamentos[id_departamento]


def importador_ubicacion():
    ruta_archivo_json = settings.ROOT_DIR.path('dumps', UBICACION_DUMPS)
    with open(ruta_archivo_json, encoding='utf-8-sig') as archivo_json:
        datos_ubicaciones = json.load(archivo_json)

    lista_creados = []
    for dato_ubicacion in datos_ubicaciones['localidades']:
        localidad, creada = Ubicacion.objects.get_or_create(
            tipo=Ubicacion.LOCALIDAD,
            nombre=dato_ubicacion['nombre'],
            parent=obtener_o_crear_departamento(dato_ubicacion['departamento']['nombre'],
                                                dato_ubicacion['provincia']['nombre'],
                                                dato_ubicacion['departamento']['id'],
                                                dato_ubicacion['provincia']['id']
                                                )
        )

        if creada:
            print(f'se creo Localidad: {localidad}')


class Command(BaseCommand):
    help = "Importar Ubicanciones desde JSON"

    def handle(self, *args, **options):
        print('Iniciamos la importación de Ubicaciones ...')
        importador_ubicacion()
