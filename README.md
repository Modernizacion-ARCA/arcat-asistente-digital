# Asistente digital de ARCAT

MVP en evolución para consultar, en lenguaje natural, información institucional de la Agencia de Recaudación Catamarca (ARCAT). El repositorio parte de un backend Django existente y se desarrolla por fases para preservar la trazabilidad, evitar datos inventados y mantener una arquitectura simple.

> **Estado actual:** Django, PostgreSQL + pgvector, dominio, administración e ingesta con detección de cambios están implementados. También están preparadas las abstracciones de OpenRouter y embeddings locales, la configuración RAG y la persistencia de fragmentos vectoriales. Todavía no hay información oficial precargada, retrieval híbrido, endpoint de chat ni frontend ejecutable.

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
  ├── embeddings locales ──► BAAI/bge-m3
  ├── recuperación RAG
  └── LLMProvider ──► OpenRouter
  │
  ▼
PostgreSQL + pgvector
```

Next.js nunca se comunicará directamente con OpenRouter, proveedores de embeddings ni credenciales privadas. Django será la única frontera para reglas de negocio, recuperación, límites de uso, selección de modelos y sanitización de errores.

### Modelo de datos

El backend incluye entidades normalizadas para `Organismo`, `Area`, `Categoria`, `Plataforma`, `Tramite`, `Servicio`, `Fuente`, `Documento` y `DocumentChunk`. Los trámites y servicios referencian las clasificaciones compartidas sin copiar sus datos; los documentos pueden vincularse con ambos y siempre pertenecen a una fuente. Cada `DocumentChunk` conserva texto, posición, metadata, modelo y embedding, con trazabilidad completa `Fuente → Documento → DocumentChunk`. Los vectores no se guardan en entidades de negocio.

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

### LLM: OpenRouter

`OpenRouterProvider` implementa la interfaz backend `LLMProvider` para generación de respuestas. Requiere `OPENROUTER_API_KEY` sólo al intentar generar una respuesta: migraciones, administración e ingesta pueden ejecutarse sin la clave. La clave se crea en la cuenta de OpenRouter y se copia únicamente al `.env` local; nunca debe incluirse en Git, logs, frontend ni variables públicas de Next.js.

`OPENROUTER_PRIMARY_MODEL` selecciona el modelo y `OPENROUTER_FALLBACK_MODELS` admite una lista separada por comas para la etapa posterior de fallback. El valor seguro `ALLOW_PAID_MODELS=false` rechaza antes de cualquier solicitud todo identificador que no sea `openrouter/free` ni termine en `:free`, incluso los fallbacks configurados. No existe cambio automático a modelos pagos. Como segunda barrera, la clave de desarrollo debe configurarse con USD 0 de crédito en OpenRouter.

### Embeddings: modelo local

`LocalEmbeddingProvider` implementa `EmbeddingProvider` dentro del proceso Django. No usa OpenRouter ni requiere una API key. `EMBEDDING_MODEL` selecciona el modelo local; el valor inicial `BAAI/bge-m3` produce vectores de 1024 dimensiones, almacenados por `DocumentChunk.embedding` en PostgreSQL mediante pgvector. `EMBEDDING_DIMENSION=1024` documenta y valida ese contrato: cambiar a una dimensión distinta requiere también una migración de base de datos.

La primera ejecución descarga el modelo y puede demorar. Compose conserva la caché de Hugging Face en el volumen `embedding_models`; no se crea un microservicio adicional.

### Indexación de fuentes

La ingesta descarga HTML o PDF desde una fuente registrada, conserva URL original, fechas, contenido y metadata, extrae y limpia texto y calcula un checksum. Un checksum sin cambios evita reprocesamientos. La siguiente etapa conectará el chunking y `LocalEmbeddingProvider` con la ingesta y construirá el retrieval híbrido; no se incorporarán datos de ARCAT que no provengan de fuentes oficiales verificadas.

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
| `OPENROUTER_API_KEY` | Credencial backend para generación; puede quedar vacía mientras no se invoque el LLM. |
| `OPENROUTER_BASE_URL` | Endpoint compatible con OpenAI utilizado por el adaptador. |
| `OPENROUTER_PRIMARY_MODEL`, `OPENROUTER_FALLBACK_MODELS` | Modelo primario y lista opcional separada por comas. |
| `ALLOW_PAID_MODELS` | Barrera local contra modelos pagos; `false` por defecto. |
| `MAX_DAILY_LLM_REQUESTS`, `MAX_INPUT_TOKENS`, `MAX_OUTPUT_TOKENS` | Límites centralizados para los controles de consumo de la API/RAG. |
| `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL` | Proveedor `local` y modelo cargado por Django. |
| `EMBEDDING_DIMENSION` | Dimensión persistida por pgvector; `1024` para `BAAI/bge-m3`. |
| `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP` | Tamaño y solapamiento iniciales, expresados en palabras. |
| `RAG_TOP_K` | Máximo inicial de evidencias devueltas por retrieval. |

Todos los valores se leen y validan en Django Settings. Para cambiar modelos o parámetros RAG basta editar `.env` y reiniciar el backend. No se aceptan secretos en variables públicas de Next.js.

## Ejecución con Docker

```bash
docker compose up --build
```

Compose inicia `postgres` con la imagen oficial de pgvector y, una vez saludable, inicia `backend`, ejecuta migraciones y sirve Django en <http://localhost:8000>. La migración inicial de `core` ejecuta `CREATE EXTENSION vector` de forma versionada. Los volúmenes `postgres_data` y `embedding_models` mantienen la base y la caché del modelo local entre reinicios.

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

1. Indexación de fragmentos y recuperación híbrida (vectorial + textual + filtros).
2. Orquestación RAG, fallback gratuito y controles persistentes de consumo.
3. API pública.
4. Next.js y chat.
5. Estadísticas y endurecimiento final de Docker/documentación.

Las inconsistencias heredadas en endpoints de persona/usuario se consideran deuda preexistente y se corregirán sólo cuando interfieran con una fase, para evitar un refactor general fuera de alcance.
