SISTEMA BASE
==================


### Descripción

Este proyecto pretende servir de base para otros proyectos, ya incluyendo algunas características comunes para todos los proyectos que tengan una api y un administrador con django jet con Django 5

## Requermientos

1. Python 3.11
2. pip 23.2.1

## Instalación

1. Creación de un entorno virtual: `mkvirtualenv -p python3.11 base` o `mkvirtualenv base` si solo esta instalado python 3.11 
2. Instalar pip version 23 `pip install pip==23.2.1`
2. Instalacion de dependencias: `pip install -r requirements/development.txt`
3. Creacion de una base de datos. (Preferentemente PostgreSQL)
4. Configuracion del proyecto desde el archivo `.env`: `cp env.example .env`
5. Correr migraciones. `python manage.py migrate`
6. Si se quiere importar provincias/departamentos/localidades: `python manage.py importar_ubicaciones`


# Bibliotecas utilizadas en el proyecto

## Frameworks y Herramientas Principales:
- **Django**: Framework web de Python para desarrollo rápido.
- **Django REST Framework**: Herramienta potente para la creación de APIs web.

## Gestión de Configuración y Entorno:
- **django-environ**: Carga la configuración de Django desde variables de entorno.

## Integraciones y Extensiones:
- **psycopg2** y **psycopg2-binary**: Adaptadores de base de datos PostgreSQL para Python.
- **django-extensions**: Colección de extensiones útiles para el desarrollo de Django.
- **django-autocomplete-light**: Implementa campos de autocompletado.
- **django-cors-headers**: Añade encabezados CORS a las respuestas Django.
- **django-4-jet**: Tema moderno para el panel de administración de Django.

## Utilidades y Compatibilidad:
- **six**: Proporciona compatibilidad entre Python 2 y Python 3.

## Filtrado y Manipulación de Datos:
- **django-filter**: Filtra consultas de Django basadas en parámetros de URL.
- **django-js-asset**: Empaqueta activos JavaScript para Django.
- **django-mptt**: Gestiona árboles de modelos en Django.
- **django-better-admin-arrayfield**: Mejora la visualización de campos de matriz en el panel de administración de Django.
- **django-querysetsequence**: Combina y ordena objetos QuerySet de Django.

## Autenticación y Seguridad:
- **django-oauth-toolkit**: Implementa el flujo OAuth2 en aplicaciones Django.
- **django-rest-framework-social-oauth2**: Autenticación social OAuth2 en Django REST Framework.
