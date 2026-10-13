# Autoevaluación provisional con evidencia — 2026-10-13

Fuente de requisitos y ponderaciones: `docs/rubric-traceability.md` (24
indicadores, 100 puntos). Esta hoja separa **evidenciado**, **parcial** y
**pendiente**. La puntuación provisional cuenta únicamente indicadores con
evidencia verificable; parcial/pending reciben 0 hasta cerrar la prueba. No es una
nota oficial ni reemplaza la revisión del evaluador.

## Resultado conservador

| Competencia | Evidenciado | Parcial | Pendiente | Puntos con evidencia |
|---|---:|---:|---:|---:|
| C1 Comunicación (12) | 4/4 | 0 | 0 | 12/12 |
| C2 Control de versiones (16) | 7/8 | 1 | 0 | 14/16 |
| C3 Equipo/proyecto (18) | 3/9 | 1 | 5 | 6/18 |
| C4 NLP/IA (54) | 2/3 | 1 | 0 | 36/54 |
| **Total provisional** | **16/24** | **3/24** | **5/24** | **68/100** |

El 68 es un piso documentado con el criterio binario de la rúbrica, no una
predicción de calificación. El trabajo de la demo suma preparación, pero la falta
de ensayo/ejecución puede hacer que el evaluador no acepte C1.2. C4.1 no se puntúa
porque la generación real aún no se ha demostrado en esta sesión.

## Indicadores y evidencia

| Nº | Indicador (peso) | Estado | Evidencia / límite |
|---:|---|---|---|
| 1 | Estructura ordenada (3) | Evidenciado | `presentacion-tecnica-10-min.pptx`, 8 diapositivas con bloques y tiempos. Falta ensayo. |
| 2 | Contenido visual / demo (3) | Evidenciado | Deck + guion/fallback en `docs/demo-groq-ollama.md`; la demo real sigue pendiente. Confirmar aceptación del evaluador. |
| 3 | Estructura pragmática y concreta (3) | Evidenciado | Deck presenta problema, solución, arquitectura, evidencia, límites y próximos pasos. |
| 4 | Storytelling (3) | Evidenciado | Narrativa brief → contexto → borrador → control humano en el deck. |
| 5 | GitHub/GitLab/Bitbucket (2) | Evidenciado | Repositorio GitHub y Project #1. |
| 6 | Conectar repo local/remoto (2) | Parcial | Repositorio remoto existe y configuración está documentada; clon limpio y ejecución no verificados en esta sesión. |
| 7 | Commits descriptivos (2) | Evidenciado | Historial y convenciones/validación referenciados en Issue #38. Revisar commits seleccionados para exposición. |
| 8 | Metodología Gitflow (2) | Evidenciado | Desarrollo en `dev`, ramas de feature y PR; workflow descrito en `CONTRIBUTING.md`. |
| 9 | Uso apropiado de ramas (2) | Evidenciado | PRs de features integrados a `dev`; no trabajar directo sobre `main`. |
| 10 | Nomenclatura de commits (2) | Evidenciado | Política y validador Git Conventions; `CONTRIBUTING.md`. |
| 11 | Issues (2) | Evidenciado | Backlog y trazabilidad; Issues #29/#35/#36 enlazan criterios de entrega. |
| 12 | Nomenclatura de ramas (2) | Evidenciado | Convención documentada en `CONTRIBUTING.md` y validación de repositorio. |
| 13 | Kanban / burndown (2) | Evidenciado | GitHub Project #1 con tablero Kanban. No se encontró burndown; la rúbrica usa “/”. |
| 14 | Roles definidos (2) | Pendiente | No se halló un registro de roles/responsabilidades verificable para el trabajo individual. |
| 15 | Actas (2) | Pendiente | No se hallaron actas. No fabricar reuniones retrospectivas. |
| 16 | Dailies (2) | Parcial | Hay `docs/daily/` con entradas 4–6 oct; cobertura incompleta hasta la entrega. |
| 17 | Retrospectivas (2) | Pendiente | Sin retrospectiva verificable en el material inspeccionado. |
| 18 | Herramienta de gestión (2) | Evidenciado | GitHub Project #1 y backlog de Issues. |
| 19 | Estimación de tareas (2) | Pendiente | No se halló estimación suficiente por tarea. |
| 20 | Prioriza al equipo (2) | Pendiente | No hay evidencia suficiente para valorar priorización de equipo; proyecto individual limita aplicabilidad, pero no se presume equivalencia. |
| 21 | README/documentación (2) | Evidenciado | README, roadmap, evaluación, evidencia RAG y esta autoevaluación. |
| 22 | Uso de modelos LLM (18) | Parcial | Groq adapter y Ollama adapter implementados; PR #103 usa mocks. Sin generación real en la evidencia. Smoke tests bloqueados por entorno. |
| 23 | Framework de aplicaciones LLM (18) | Evidenciado | Boundary LangChain/provider-neutral documentado y verificado con pruebas del API/core; ver `docs/evaluation-plan.md` y roadmap. |
| 24 | Arquitectura RAG (18) | Evidenciado | `docs/evidence/mvp-evaluation-issue-25.md` y `rag-issue-32-representative-runs.md`: recuperación, referencias, unsupported claim, aislamiento; todo con fixtures/mocks. |

## Bloqueos y acciones para cierre

1. Ejecutar las dos llamadas reales con el brief común definido en
   `docs/demo-groq-ollama.md`; adjuntar salidas, modelos, tiempos y límites.
2. Ensayar la presentación a 10 minutos y guardar evidencia/captura de demo o
   activar el fallback, declarando que es mock.
3. Hacer clon e instalación limpios del README; guardar comandos y resultado.
4. Reunir registros reales de trabajo/roles/estimaciones/retrospectiva solo si
   existen. No crear actas o dailies retroactivas.
5. Confirmar con el profesor el nivel de evidencia RAG pendiente en
   `docs/assumptions.md`.

## Referencias

- `docs/rubric-traceability.md` (rúbrica oficial transcrita).
- `docs/evaluation-plan.md` (protocolo y política de datos).
- `docs/evidence/provider-smoke-tests-2026-10-13.md` (intentos reales no ejecutados y motivo).
- GitHub Project #1; Issues #27, #29, #35, #36, #38; PR #103.