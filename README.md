# Asistente digital de ARCAT

MVP en evolución para consultar, en lenguaje natural, información institucional de la Agencia de Recaudación Catamarca (ARCAT). El repositorio parte de un backend Django existente y se desarrolla por fases para preservar la trazabilidad, evitar datos inventados y mantener una arquitectura simple.

> **Estado actual:** Fases 1 a 4 completadas: Django + PostgreSQL + pgvector, modelo normalizado del dominio, administración Django e ingesta con detección de cambios. El código heredado de usuarios, personas y utilidades se conserva. Todavía no hay información oficial ni datos DEMO precargados, RAG, OpenRouter o frontend ejecutable.

## Arquitectura objetivo

```text
Usuario
  │
  ▼
Next.js (interfaz pública; fase posterior)
  │ REST
  ▼
Django + Django REST Framework
  ├── dominio e ingesta
  ├── recuperación RAG
  └── proveedor LLM abstracto ──► OpenRouter
  │
  ▼
PostgreSQL + pgvector
```

Next.js nunca se comunicará directamente con OpenRouter, proveedores de embeddings ni credenciales privadas. Django será la única frontera para reglas de negocio, recuperación, límites de uso, selección de modelos y sanitización de errores.

### Modelo de datos

El backend incluye entidades normalizadas para `Organismo`, `Area`, `Categoria`, `Plataforma`, `Tramite`, `Servicio`, `Fuente` y `Documento`. Los trámites y servicios referencian las clasificaciones compartidas sin copiar sus datos; los documentos pueden vincularse con ambos y siempre pertenecen a una fuente. Más adelante, `Fragmento` será una entidad separada que conservará el texto, su embedding y referencias al documento y a la fuente originales. Así se evita guardar vectores en entidades de negocio y cada evidencia permanece trazable.

Las fuentes representan atributos verificables —origen oficial o DEMO, prioridad, estado de verificación, disponibilidad y fechas— en lugar de una valoración subjetiva de confiabilidad. `Fuente.origen_informacion` separa obligatoriamente los datos `DEMO` de los oficiales. `Documento` conserva contenido recuperado, texto extraído, metadata variable y un checksum SHA-256 validado, sin almacenar embeddings en la entidad documental.

Las relaciones protegidas impiden eliminar organismos o fuentes que todavía sustentan información. Una validación de dominio impide asociar un trámite o servicio con un área perteneciente a otro organismo y evita declarar un método de autenticación sin marcar que la autenticación es requerida.

### Flujo RAG previsto

1. Validar y normalizar la pregunta sin registrar credenciales ni datos sensibles.
2. Clasificar la intención como una señal adicional, nunca como bloqueo de recuperación.
3. Generar un embedding mediante una interfaz `EmbeddingProvider` configurable.
4. Ejecutar búsqueda híbrida: similitud vectorial en pgvector, texto completo y filtros de metadata.
5. Seleccionar solamente los fragmentos relevantes (`top-k`) y construir un contexto acotado.
6. Enviar ese contexto al `LLMProvider`; nunca se enviará toda la base.
7. Responder en español con enlaces y evidencias utilizadas. Cuando no haya evidencia suficiente, se indicará: “No encuentro esa información en las fuentes oficiales disponibles.”

### OpenRouter, fallback y costos

La integración futura implementará una interfaz `LLMProvider`, con OpenRouter como primer adaptador. Modelo principal, fallbacks y límites se configurarán mediante variables de entorno del backend. Los modelos se intentarán en orden únicamente ante errores recuperables (timeout, límite o indisponibilidad), registrando modelo, duración, tokens, error y posición de fallback sin incluir secretos.

`ALLOW_PAID_MODELS=false` será el valor seguro por defecto. Antes de una llamada se validarán el contador diario, los límites por IP/sesión y los máximos de entrada/salida; si se alcanza un límite no habrá solicitud al proveedor. Ninguna clave de OpenRouter se expondrá al frontend.

### Indexación de fuentes

La ingesta futura descargará HTML o PDF desde una fuente registrada, conservará URL original, fechas, contenido y metadata, extraerá y limpiará texto, calculará un checksum, dividirá en fragmentos y generará embeddings. Un checksum sin cambios evitará reprocesamientos. La reindexación podrá limitarse a un documento, trámite o categoría. No se incorporarán datos de ARCAT que no provengan de fuentes oficiales verificadas.

## Requisitos

- Docker con Docker Compose (recomendado).
- Para ejecución local sin contenedores: Python 3.12 y PostgreSQL 16 con la extensión `vector` disponible.

## Configuración

1. Copiar las variables de ejemplo:

   ```bash
   cp .env.example .env
   ```

2. Reemplazar todos los valores `change-this-*`. El archivo `.env` está excluido de Git.

Las variables actuales son:

| Variable | Propósito |
| --- | --- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Base y credenciales locales de PostgreSQL. |
| `DJANGO_SETTINGS_MODULE` | Módulo de configuración; Compose usa desarrollo inicialmente. |
| `DJANGO_SECRET_KEY` | Secreto de Django; no debe versionarse. |
| `DJANGO_DEBUG` | Activa depuración solamente en desarrollo. |
| `DJANGO_ALLOWED_HOSTS` | Hosts aceptados por Django. |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Orígenes frontend autorizados explícitamente. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes confiables para solicitudes CSRF. |
| `DJANGO_*_COOKIE_SECURE`, `DJANGO_SECURE_SSL_REDIRECT` | Controles HTTPS, habilitados por defecto en producción. |

Las variables futuras de proveedores (`OPENROUTER_API_KEY`, modelos y límites) se agregarán cuando exista esa integración; no se aceptan secretos en variables públicas de Next.js.

## Ejecución con Docker

```bash
docker compose up --build
```

Compose inicia `postgres` con la imagen oficial de pgvector y, una vez saludable, inicia `backend`, ejecuta migraciones y sirve Django en <http://localhost:8000>. La migración inicial de `core` ejecuta `CREATE EXTENSION vector` de forma versionada. El volumen `postgres_data` mantiene los datos entre reinicios.

El servicio `frontend` se incorporará en su fase correspondiente; no se agrega un contenedor vacío antes de que exista una aplicación Next.js ejecutable.

## Ejecución local del backend

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements/development.txt
cp env.example .env
python manage.py migrate
python manage.py runserver
```

La URL de base por defecto apunta a `postgresql://arcat:arcat@localhost:5432/arcat`; se recomienda definir siempre `DATABASE_URL` con credenciales propias.

## Migraciones

```bash
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py makemigrations --check --dry-run
```

No se debe editar manualmente el esquema. PostgreSQL + pgvector es la persistencia principal; SQLite queda limitado a la suite heredada mientras los tests se migran gradualmente.

## Datos e ingesta

Las fuentes se crean y verifican primero desde Django Admin. La ingesta procesa sólo
las fuentes activas y verificadas, ordenadas por prioridad:

```bash
python manage.py ingestar_fuentes
```

Para limitar la ejecución a fuentes concretas, el argumento se puede repetir:

```bash
python manage.py ingestar_fuentes --fuente 1 --fuente 3
```

El comando admite HTML, texto plano y PDF, conserva la URL original, metadata HTTP y
texto extraído, y calcula un checksum SHA-256. Si el checksum no cambia, no vuelve a
guardar el documento. Cada consulta actualiza la disponibilidad de la fuente; un fallo
en una fuente no impide intentar las demás. Las descargas rechazan destinos privados o
reservados y tienen límites de tiempo y tamaño.

La procedencia `DEMO` u oficial sigue siendo la definida explícitamente en cada
`Fuente`; la ingesta no promueve ni verifica fuentes automáticamente.

## Tests y verificaciones

Desde `api/`, con dependencias de testing instaladas:

```bash
pip install -r requirements/testing.txt
pytest
python manage.py check
python manage.py makemigrations --check --dry-run
```

Para validar la infraestructura completa, ejecutar además `docker compose config` y las migraciones contra el contenedor PostgreSQL.

## Próximas fases

1. Embeddings, fragmentos y recuperación híbrida.
2. RAG, OpenRouter, fallback y controles de costo.
3. API pública.
4. Next.js y chat.
5. Estadísticas y endurecimiento final de Docker/documentación.

Las inconsistencias heredadas en endpoints de persona/usuario se consideran deuda preexistente y se corregirán sólo cuando interfieran con una fase, para evitar un refactor general fuera de alcance.
