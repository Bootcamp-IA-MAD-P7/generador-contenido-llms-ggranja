# Demo reproducible: Groq y Ollama

Estado al 2026-10-13: **guion y fallback preparados; llamadas reales pendientes**.
Esta nota no registra resultados inventados. En el entorno de preparación no hay
`GROQ_API_KEY`, ejecutable Ollama ni servidor local disponible. El PR #103 confirma
que el smoke test real de Ollama tampoco se ejecutó durante su integración.

## Objetivo y brief fijo

Repetir exactamente este caso en la interfaz/API del proyecto, primero con Groq y
luego con Ollama. El endpoint es `POST /drafts` y requiere la sesión local normal.
Usar el mismo JSON en ambas corridas; no cambiar código entre ejecuciones.

> Negocio sintético: panadería de barrio. Tema: caja de desayuno entre semana.
> Audiencia: vecinos de la zona. Canal: Instagram. Hecho aprobado: incluye pan y
> fruta. Tono: claro y cercano. No inventes precio, horario, ingredientes extra,
> disponibilidad ni beneficios nutricionales. Si falta información, indícalo para
> revisión. Devuelve un borrador corto, una llamada a la acción prudente y las
> afirmaciones que no puedas respaldar.

Payload equivalente para guardar/reutilizar en las dos ejecuciones:

```json
{
  "brief": {
    "topic_or_offer": "Caja de desayuno entre semana",
    "objective": "Dar a conocer la oferta a vecinos de la zona",
    "audience_context": "Vecinos del barrio",
    "business_context_refs": ["synthetic-bakery-demo"],
    "platforms": ["instagram"],
    "format": "single_image",
    "brand_and_constraints": "Tono claro y cercano. No inventar precio, horario, ingredientes extra, disponibilidad ni beneficios nutricionales.",
    "notes": "Si falta información, señalarla para revisión; proponer borrador corto y CTA prudente.",
    "facts": [
      {
        "statement": "La caja de desayuno incluye pan y fruta.",
        "status": "CONFIRMED",
        "source": "Brief sintético de demostración",
        "reason": "Hecho autorizado para el caso de prueba",
        "scope": "offer",
        "validation_needed": false
      }
    ]
  },
  "rag_enabled": false,
  "top_k": 3
}
```

## Preparación

1. Clonar/actualizar la rama `dev` y seguir la instalación limpia del README del
   repositorio. No usar secretos en capturas, archivos versionados ni el frontend.
2. Copiar `.env.example` a `.env` local (ignorado por Git) y conservar los límites
   comunes: `LLM_TEMPERATURE=0.2`, `LLM_TIMEOUT_SECONDS=30`,
   `LLM_MAX_OUTPUT_TOKENS=350`.
3. Para Groq: `LLM_PROVIDER=groq`, `GROQ_MODEL=openai/gpt-oss-20b` (o un modelo
   habilitado y anotado), y `GROQ_API_KEY` configurada solo en el entorno local.
4. Para Ollama: instalar e iniciar Ollama, descargar explícitamente un modelo,
   y configurar `LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL=http://127.0.0.1:11434`
   y `OLLAMA_MODEL` con el nombre exacto que `ollama list` muestre.
5. Reiniciar únicamente la API entre proveedores y comprobar `/readiness`. La
   selección de proveedor es configuración de backend; la clave nunca va al browser.
6. Iniciar sesión en la UI local ya configurada y pegar el mismo brief, o enviar
   el payload anterior a `POST /drafts` usando la sesión autenticada obtenida por
   el flujo local `/auth/login`. No pegar la clave Groq en la petición del cliente.

## Ejecución y registro

1. Enviar el payload fijo con Groq. Guardar el resultado completo sin credenciales,
   modelo, fecha/hora y latencia observada; comprobar provider/model informado.
2. Cambiar a Ollama y repetir el mismo payload, canal, temperatura, timeout y
   límite de salida. Guardar los mismos campos.
3. Para cada salida, marcar: incluye solo el hecho respaldado; inventa precio u
   horario; respeta canal/tono; señala incertidumbres; requiere edición. Adjuntar
   referencias RAG si el recorrido integra recuperación en ese setup.
4. No comparar calidad como conclusión con una sola salida por proveedor. La
   comparación entre modelos es opcional para la rúbrica; aquí se verifica primero
   que cada proveedor genere una respuesta real y quede identificada.

| Campo | Groq | Ollama |
|---|---|---|
| Fecha/hora, zona | NO EJECUTADO | NO EJECUTADO |
| Modelo/provider informado | — | — |
| Latencia | — | — |
| ID de ejecución / captura redactada | — | — |
| Resultado de factualidad | — | — |
| Error / limitación | Falta `GROQ_API_KEY` en este runner | No hay CLI/servidor/modelo instalado aquí |

## Fallback para la presentación

Si falla Internet, API o el servicio Ollama, no improvisar ni atribuir el mock a un
modelo real. Mostrar la ejecución offline documentada en
`docs/evidence/rag-issue-32-representative-runs.md`:

- salida mock: `Weekday breakfast box includes bread and fruit.`
- evidencia: `business-guide-v1-p0001-c0001`, PDF sintético, página 1;
- el claim `The box costs five euros.` no aparece en la fuente y se marca
  `UNSUPPORTED` para revisión;
- aislamiento: el contexto de `synthetic-bakery-a` no se entrega a
  `synthetic-bakery-b`.

Decir en voz alta: “Este fallback prueba el recorrido de integración y trazabilidad
con un mock determinista; no es una generación de Groq ni Ollama”.

## Limitaciones

El setup solo puede demostrar las salidas y proveedores presentes en cada corrida.
Una generación por proveedor no es evaluación estadística ni prueba de calidad
general. RAG usa fixtures sintéticos y tests offline; la revisión léxica no es una
certificación de veracidad. No se deben usar datos privados de comercios.

## Evidencia relacionada

- [README / rama dev](https://github.com/gabrielagranja/generador-contenido-llms/tree/dev)
- [PR #103: Ollama local; sin smoke test real](https://github.com/gabrielagranja/generador-contenido-llms/pull/103)
- [Ejecuciones RAG mock reproducibles](evidence/rag-issue-32-representative-runs.md)
- [Evaluación offline y limitaciones](evidence/mvp-evaluation-issue-25.md)
- Issues #29 (presentación), #35 (demo/fallback), #36 (readiness).