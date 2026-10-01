# Asistente digital de ARCAT

MVP en evolución para consultar, en lenguaje natural, información institucional de la Agencia de Recaudación Catamarca (ARCAT). El repositorio parte de un backend Django existente y se desarrolla por fases para preservar la trazabilidad, evitar datos inventados y mantener una arquitectura simple.

> **Estado actual:** Django, PostgreSQL + pgvector, dominio, administración, ingesta, indexación con embeddings locales, retrieval híbrido, orquestación RAG, API pública, evaluación reproducible y frontend Next.js están implementados. OpenRouter dispone de fallback gratuito y controles persistentes de consumo. Todavía no hay información oficial precargada ni dataset oficial validado.

## Arquitectura objetivo

```text
Usuario
  │
  ▼
Next.js (interfaz pública)
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

La ingesta descarga HTML o PDF desde una fuente registrada, conserva URL original, fechas, contenido y metadata, extrae y limpia texto y calcula un checksum. Un checksum sin cambios evita reprocesamientos. La indexación divide ese texto, genera embeddings locales y reemplaza los fragmentos dentro de una transacción. Una firma del texto, modelo y parámetros evita regenerarlos si nada relevante cambió. No se incorporan datos de ARCAT que no provengan de fuentes oficiales verificadas.

`HybridRetriever` consulta en paralelo la distancia vectorial y la búsqueda de texto completo de PostgreSQL, aplica filtros institucionales y combina ambos rankings. Así, siglas y términos exactos como ARCAT, CUIT, IIBB o TAD no dependen únicamente de similitud semántica. El origen oficial es el filtro predeterminado y `RAG_TOP_K` limita el resultado final.

### Orquestación RAG y consumo

`RAGService` recupera evidencia, construye un contexto acotado y solicita una respuesta
en español que debe citar los fragmentos como `[1]`, `[2]`, etc. La respuesta devuelve
además título, fuente y URL de cada evidencia. Cuando no existen fragmentos utilizables,
no invoca al LLM y responde: “No encuentro esa información en las fuentes oficiales
disponibles.”

`LLMService` aplica `MAX_INPUT_TOKENS` antes de cualquier llamada mediante una
estimación conservadora basada en bytes UTF-8, envía `MAX_OUTPUT_TOKENS` al proveedor y
reserva en base de datos cada solicitud contra `MAX_DAILY_LLM_REQUESTS`. Cada intento
registra modelo, posición de fallback, duración, tokens y código de error, pero nunca
guarda prompts, respuestas, claves ni datos de la persona usuaria.

Los fallbacks se intentan en el orden de `OPENROUTER_FALLBACK_MODELS` únicamente ante
timeouts, problemas de red, rate limiting, indisponibilidad o errores 5xx recuperables.
Errores de autenticación, configuración, solicitud o formato de respuesta no activan
otro modelo. Con `ALLOW_PAID_MODELS=false`, el constructor de
OpenRouter rechaza toda la cadena si contiene un modelo que no sea explícitamente
gratuito; por lo tanto, un fallo nunca provoca un salto silencioso a un modelo pago.

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
| `DJANGO_CACHE_URL` | Redis compartido para throttling; obligatorio en producción. |
| `OPENROUTER_API_KEY` | Credencial backend para generación; puede quedar vacía mientras no se invoque el LLM. |
| `OPENROUTER_BASE_URL` | Endpoint compatible con OpenAI utilizado por el adaptador. |
| `OPENROUTER_PRIMARY_MODEL`, `OPENROUTER_FALLBACK_MODELS` | Modelo primario y lista opcional separada por comas. |
| `ALLOW_PAID_MODELS` | Barrera local contra modelos pagos; `false` por defecto. |
| `MAX_DAILY_LLM_REQUESTS`, `MAX_INPUT_TOKENS`, `MAX_OUTPUT_TOKENS` | Límites centralizados para los controles de consumo de la API/RAG. |
| `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL` | Proveedor `local` y modelo cargado por Django. |
| `EMBEDDING_DIMENSION` | Dimensión persistida por pgvector; `1024` para `BAAI/bge-m3`. |
| `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP` | Tamaño y solapamiento iniciales, expresados en palabras. |
| `RAG_TOP_K` | Máximo inicial de evidencias devueltas por retrieval. |
| `RAG_MAX_QUESTION_LENGTH` | Longitud máxima aceptada por la API pública. |
| `RAG_API_RATE_LIMIT` | Límite por identidad anónima; por defecto `10/hour`. |
| `NEXT_PUBLIC_API_BASE_URL` | URL pública de Django utilizada por el navegador; nunca contiene secretos. |

Todos los valores se leen y validan en Django Settings. Para cambiar modelos o parámetros RAG basta editar `.env` y reiniciar el backend. No se aceptan secretos en variables públicas de Next.js.

## Ejecución con Docker

```bash
docker compose up --build
```

Compose inicia PostgreSQL/pgvector, Redis, Django en <http://localhost:8000> y Next.js en
<http://localhost:3000>. Django ejecuta las migraciones al iniciar. Los volúmenes
`postgres_data` y `embedding_models` mantienen la base y la caché del modelo local.

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

Después de la ingesta, se pueden indexar todos los documentos activos pertenecientes
a fuentes verificadas:

```bash
python manage.py indexar_documentos
```

También se puede limitar la operación a documentos concretos. La primera ejecución
descargará el modelo local configurado:

```bash
python manage.py indexar_documentos --documento 1 --documento 3
```

Si falla la generación de embeddings, el índice anterior se conserva. La sustitución
de fragmentos sólo comienza después de recibir y validar un vector para cada chunk.

### Actualización operativa del conocimiento

Para una ejecución programada se dispone de un único comando que encadena ingesta e
indexación:

```bash
python manage.py actualizar_conocimiento
```

Por seguridad, esta operación considera exclusivamente fuentes con procedencia
`OFICIAL` que estén activas y verificadas. Los datos `DEMO` y las fuentes pendientes
quedan excluidos aun cuando existan en la base. El checksum evita persistir nuevamente
un documento idéntico y la firma del índice evita recalcular embeddings cuando no
cambiaron el texto, la metadata, el modelo ni la configuración de chunking.

La ejecución puede limitarse a una o más fuentes y también permite reconstruir el
índice de forma explícita:

```bash
python manage.py actualizar_conocimiento --fuente 1 --fuente 3
python manage.py actualizar_conocimiento --force-index
```

El comando intenta todas las fuentes seleccionadas, imprime un resumen JSON apto para
logs y finaliza con código distinto de cero si alguna falla. Un bloqueo en el cache
compartido impide que dos réplicas actualicen la base de conocimiento simultáneamente;
si Redis no está disponible, la ejecución falla de forma segura. El bloqueo vence en
una hora para permitir la recuperación ante una terminación abrupta.

Debe programarse desde el orquestador de despliegue (cron, systemd timer o tarea de la
plataforma) y configurarse con alertas sobre fallos. No requiere un servicio de
embeddings separado.

## Catálogo candidato de trámites ARCAT

Se incorporó `data/catalogs/arcat-tramites-candidatos-v1.json` con los diez registros
aportados para iniciar el relevamiento de ARCAT, Rentas y TAD. El archivo está marcado
deliberadamente como `PENDING_SOURCE_VERIFICATION`: **no se carga en los modelos, no se
indexa y no puede aparecer en la API pública**. Tener dominios oficiales como referencia
no sustituye la comprobación de cada nombre, descripción, requisito, vigencia y URL.

La estructura y la allowlist de hosts se validan con:

```bash
python manage.py validar_catalogo_arcat \
  --archivo data/catalogs/arcat-tramites-candidatos-v1.json
```

El siguiente comando falla mientras el borrador no esté aprobado, por lo que puede
usarse como barrera antes de cualquier futura importación:

```bash
python manage.py validar_catalogo_arcat \
  --archivo data/catalogs/arcat-tramites-candidatos-v1.json \
  --require-verified
```

Para promover una versión se debe contrastar registro por registro contra
`arcat.gob.ar`, `dgrentas.arcat.gob.ar` y `tad.catamarca.gob.ar`, completar los campos
vacíos sólo cuando la fuente los publique, guardar la URL específica y fecha de consulta,
y realizar revisión humana. Luego se crea una nueva versión del archivo; no se reescribe
la versión usada como evidencia histórica. El acceso de red de este entorno fue rechazado
por el proxy, por lo que en esta entrega se preservó el contenido como borrador y no se
afirma que haya sido verificado online.

Para probar el pipeline sin confundir el borrador con información institucional, puede
cargarse en un espacio aislado `DEMO`. El flag explícito es obligatorio:

```bash
python manage.py cargar_catalogo_demo \
  --archivo data/catalogs/arcat-tramites-candidatos-v1.json \
  --confirm-demo
```

La carga es idempotente y crea un organismo `ARCAT DEMO`, trámites inactivos, una fuente
de origen `DEMO` y documentos bajo `demo.invalid`. Conserva las URLs candidatas sólo en
metadata y nunca convierte el catálogo en oficial. Luego se pueden generar embeddings y
ejecutar el benchmark ficticio de punta a punta:

```bash
python manage.py indexar_documentos --origen DEMO
python manage.py evaluar_rag --dataset evaluation/datasets/demo-v1.json
```

Este circuito sirve para desarrollo técnico. La promoción oficial será un proceso
separado y sólo se implementará cuando exista una versión verificada con URLs específicas
y aprobación humana.

## API pública de consulta

El endpoint público acepta únicamente JSON y no requiere autenticación:

```http
POST /api/v1/asistente/consultar/
Content-Type: application/json

{
  "pregunta": "¿Qué documentación necesito?",
  "organismo_id": 1,
  "categoria_id": 2
}
```

`organismo_id` y `categoria_id` son filtros opcionales. La procedencia no puede ser
elegida por el cliente: la API consulta fuentes oficiales de manera predeterminada.
La respuesta incluye el texto, el modelo utilizado y evidencias trazables:

```json
{
  "respuesta": "Respuesta basada en evidencia [1]",
  "evidencias": [
    {
      "fragmento_id": 15,
      "documento": "Título del documento",
      "fuente": "Fuente oficial",
      "url": "https://dominio-oficial.example/documento"
    }
  ],
  "modelo": "openrouter/free"
}
```

La pregunta se limita mediante `RAG_MAX_QUESTION_LENGTH`. El throttle usa la sesión o
IP de la solicitud sólo para derivar un HMAC irreversible; la identidad original no se
guarda en logs ni base de datos. `RAG_API_RATE_LIMIT` controla la frecuencia. Los
detalles internos de OpenRouter nunca se devuelven: los límites producen HTTP 429 y la
indisponibilidad del proveedor HTTP 503 con mensajes sanitizados.

Compose incluye Redis sin publicar su puerto y configura `DJANGO_CACHE_URL` en el
backend. Esto permite que varias réplicas compartan el historial del throttle. Si Redis
falla, el endpoint responde HTTP 503 en vez de omitir el límite. Desarrollo y tests
pueden dejar la variable vacía para usar memoria local, pero settings de producción
rechaza explícitamente arrancar sin un Redis configurado. Los datos del throttle son
efímeros y no requieren persistencia en disco.

## Frontend Next.js

La interfaz pública ofrece un formulario accesible, sugerencias de consulta, estados de
carga/error y una lista de evidencias con enlaces. También advierte que no deben enviarse
CUIT, claves ni datos personales y que la respuesta no reemplaza una resolución
administrativa.

El navegador llama únicamente a `NEXT_PUBLIC_API_BASE_URL`; esa variable contiene una
URL pública, no una credencial. OpenRouter, modelos, fallbacks, límites y embeddings
siguen siendo responsabilidad exclusiva de Django. Para desarrollo sin Compose:

```bash
cd front
cp .env.example .env.local
npm install
npm run dev
```

## Evaluación de recuperación

La evaluación es offline y **no invoca al LLM ni consume OpenRouter**. Cada dataset JSON
versionado declara una pregunta, una o más URLs documentales esperadas, términos que
deberían aparecer en los fragmentos y la procedencia (`OFICIAL` o `DEMO`). El comando
ejecuta el mismo `HybridRetriever` utilizado por la API:

```bash
python manage.py evaluar_rag \
  --dataset evaluation/datasets/demo-v1.json
```

El reporte JSON incluye resultados por caso y tres métricas agregadas:

- `hit_rate`: proporción de preguntas que recuperan al menos un documento esperado;
- `mean_reciprocal_rank`: premia que la primera evidencia esperada aparezca arriba;
- `mean_term_coverage`: cobertura de términos esperados dentro de los chunks recuperados.

Para usarlo como control de CI puede indicarse un umbral explícito:

```bash
python manage.py evaluar_rag \
  --dataset evaluation/datasets/demo-v1.json \
  --fail-below-hit-rate 0.80
```

El archivo incluido es exclusivamente DEMO y sólo verifica el mecanismo. No establece
un benchmark institucional ni justifica todavía cambiar `RAG_TOP_K`, el chunking o un
umbral de evidencia. Esos valores deben ajustarse recién con preguntas y documentos
oficiales revisados, conservando cada versión del dataset para comparar regresiones.

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

### Qué falta

1. **Verificación del catálogo candidato:** contrastar los diez trámites con las páginas
   oficiales, capturar URLs específicas, vigencia y campos faltantes, y aprobar una nueva
   versión antes de importarla o indexarla.
2. **Dataset oficial y criterios de aceptación:** redactar con referentes de ARCAT casos
   reales revisados, fijar baselines y recién entonces ajustar `top-k`, chunking y el
   umbral mínimo de evidencia.
3. **Validación de experiencia:** pruebas con personas usuarias, revisión de lenguaje
   claro, accesibilidad automatizada y ajustes responsive sobre dispositivos reales.
4. **Operación:** conectar `actualizar_conocimiento` al scheduler del entorno, sumar
   alertas, métricas, retención de registros, backups y endurecimiento de producción.
5. **Datos:** alta y revisión humana de fuentes oficiales de ARCAT. Hasta completar esa
   revisión, no corresponde presentar respuestas como información institucional real.

### Cómo seguimos

La próxima entrega debería verificar fuentes oficiales y construir con referentes
el **dataset institucional de evaluación**, sin inventar respuestas desde desarrollo.
Con ese baseline se podrán fijar umbrales de evidencia y validar el chat ya disponible
sin presentarlo todavía como una fuente institucional completa. Después corresponde
probar accesibilidad/usabilidad y, finalmente, automatización operativa y métricas.

Las inconsistencias heredadas en endpoints de persona/usuario se consideran deuda preexistente y se corregirán sólo cuando interfieran con una fase, para evitar un refactor general fuera de alcance.
