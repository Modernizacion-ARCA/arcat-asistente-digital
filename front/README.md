# Frontend del Asistente Digital ARCAT

Aplicación Next.js accesible que consume exclusivamente la API pública de Django.
No contiene ni recibe claves de OpenRouter, nombres de fallback o configuración de
embeddings.

## Desarrollo local

```bash
cp .env.example .env.local
npm install
npm run dev
```

La interfaz queda disponible en <http://localhost:3000>. La única variable pública es
`NEXT_PUBLIC_API_BASE_URL`, que identifica el backend HTTP y no debe contener secretos.

## Verificaciones

```bash
npm run check
npm run build
```
