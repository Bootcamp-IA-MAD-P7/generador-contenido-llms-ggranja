# Demo local reproducible

Esta guía prepara el MVP para una demostración **local y offline**. No configura
Groq, Ollama, publicación social ni datos de comercios reales.

## Preparar una vez

Desde la raíz del repositorio, con el entorno virtual activo:

```bash
python scripts/prepare_demo.py
```

El comando escribe solo archivos ignorados por Git:

- `.env`: API en `127.0.0.1:18000`, proveedor `mock` y hash de acceso local.
- `apps/web/.env.local`: URL de la API para Next.js.
- `.local/credenciales-gabriela.txt`: recordatorio de las credenciales locales.

Las credenciales de demo son siempre:

```text
usuario: gabriela
contraseña: gabriela
```

El helper se niega a ejecutarse si `APP_ENV` no es `development` o está vacío.
No debe usarse para despliegues ni exponerse fuera de localhost. Cada ejecución
renueva el secreto de sesión, por lo que hay que volver a iniciar sesión.

## Arrancar la demo

Terminal 1, desde la raíz:

```bash
python -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 18000
```

Terminal 2:

```bash
cd apps/web
npm run dev
```

Abrir `http://localhost:3000/login` e iniciar sesión con `gabriela / gabriela`.
El recorrido de demo es: login → Content Studio → preparar un brief → revisar el
borrador. El estado debe ser `pending_human_review`; no se publica contenido.

## Verificación rápida

```bash
curl http://127.0.0.1:18000/readiness
```

La respuesta esperada es:

```json
{"status":"ready","service":"api"}
```

Antes de una presentación, ejecutar:

```bash
python -m pytest -q --import-mode=importlib tests
cd apps/web && npm test && npm run typecheck
```

## Proveedores reales

La demo inicial usa `LLM_PROVIDER=mock` para ser reproducible. Para probar Groq
u Ollama después, modificar solo la configuración local siguiendo
`docs/demo-groq-ollama.md`, reiniciar la API y repetir el mismo brief. No incluir
claves ni tokens en capturas, commits o documentación.
