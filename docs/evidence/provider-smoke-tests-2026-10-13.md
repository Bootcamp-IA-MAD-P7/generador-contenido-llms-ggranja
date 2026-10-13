# Provider smoke tests — 2026-10-13

## Resultado

**Groq: no ejecutado. Ollama: no ejecutado.** Esta es una verificación de
disponibilidad del entorno de preparación, no un resultado de generación.

Checks realizados sin revelar valores:

- `GROQ_API_KEY` configurada en este runner: **no**.
- Ejecutable `ollama` en `PATH`: **no**.
- Por ello no se envió una petición a Groq ni a Ollama y no hay respuesta/latencia
  que reportar.

El PR #103 indica que la integración Ollama fue probada con mocks y sin smoke test
real porque su runner no tenía servicio/modelo local. En esta sesión tampoco había
checkout local del repo, por lo que no se pudieron lanzar la UI ni `POST /drafts`.

## Próxima captura requerida

Completar `docs/demo-groq-ollama.md` en una máquina con ambos proveedores
disponibles. Guardar proveedor/modelo informado, timestamp con zona, duración,
payload común, respuesta redactada, referencias RAG/claims no soportados y error
si lo hubo. Nunca registrar la clave. Mantener la respuesta como dato de evaluación,
no como prueba de una calidad universal.

## Evidencia que sí existe

- `docs/evidence/mvp-evaluation-issue-25.md`: 28 tests locales con proveedor mock;
  verifica integración RAG/API/PDF, no calidad de LLM hospedado.
- `docs/evidence/rag-issue-32-representative-runs.md`: casos sintéticos trazables,
  deterministas y mock.
- PR #103: provider adapter de Ollama y pruebas unitarias/API simuladas; sin llamada
  a modelo real.