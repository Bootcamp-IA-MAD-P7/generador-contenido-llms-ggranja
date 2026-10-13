# Rúbrica de autoevaluación y trazabilidad

Autoridad: fuente de verdad de los requisitos de evaluación, pesos, evidencias y estado de autoevaluación del proyecto.

Estado: transcripción completa de la rúbrica oficial el 2026-10-05. Autoevaluación provisional revisada el 2026-10-13. Cada estado incluye evidencia o limitación; el detalle por criterio y la puntuación conservadora están en `docs/self-assessment-2026-10-13.md`. Los smoke tests Groq/Ollama siguen pendientes.

## Fuente oficial

- Archivo: rubrica_autoevaluacion.xlsx.
- Hoja: Autoevaluación.
- Proyecto indicado por la fuente: LLMs - Modelos de lenguaje.
- Enlace de fuente incluido en la hoja: https://drive.google.com/file/d/1JrGeW02oyZu8UBySsjJqPLNjlFjz6kMQ/view

## Sistema de puntuación

La rúbrica suma 100 puntos y contiene 24 indicadores. Cada indicador reparte por igual el peso de su competencia, salvo cuando la fuente define un valor específico. La hoja calcula los puntos al marcar cada indicador como “Sí”.

| Competencia | Peso | Indicadores | Puntos por indicador |
|---|---:|---:|---:|
| C1. Comunicar efectivamente el desarrollo de un proyecto de forma clara y estructurada | 12 % | 4 | 3 |
| C2. Gestionar eficientemente proyectos de desarrollo con herramientas de control de versiones | 16 % | 8 | 2 |
| C3. Gestionar equipos de forma eficiente | 18 % | 9 | 2 |
| C4. Crear un modelo de inteligencia artificial con técnicas de Procesamiento del Lenguaje Natural | 54 % | 3 | 18 |
| **Total** | **100 %** | **24** | — |

## Requisitos oficiales y trazabilidad

### C1 — Comunicar efectivamente el desarrollo de un proyecto de forma clara y estructurada (12 %)

| Nº | Indicador evaluable | Peso | Evidencia prevista en el proyecto | Estado |
|---:|---|---:|---|---|
| 1 | Uso de estructura ordenada | 3 % | Issue #29, presentación; Issue #28, artículo; README y documentación de entrega. | Evidenciado — docs/delivery/presentacion-tecnica-10-min.pptx |
| 2 | Uso de contenido visual / demo | 3 % | Issue #29, presentación; Issue #35, escenarios de demo; Issue #36, revisión final. | Evidenciado — docs/delivery/presentacion-tecnica-10-min.pptx y docs/demo-groq-ollama.md; smoke real pendiente |
| 3 | Uso de estructura pragmática y concreta | 3 % | Issue #29, presentación; Issue #28, artículo; README. | Evidenciado — docs/delivery/presentacion-tecnica-10-min.pptx |
| 4 | Uso de storytelling | 3 % | Issue #28, narrativa de portfolio; Issue #29, presentación. | Evidenciado — narrativa brief → borrador → control humano en docs/delivery/presentacion-tecnica-10-min.pptx |

### C2 — Gestionar eficientemente proyectos de desarrollo con herramientas de control de versiones (16 %)

| Nº | Indicador evaluable | Peso | Evidencia prevista en el proyecto | Estado |
|---:|---|---:|---|---|
| 5 | Uso de GitHub, GitLab o Bitbucket | 2 % | Repositorio GitHub; Issue #36, revisión final. | Evidenciado — repositorio GitHub del proyecto |
| 6 | Conectar el repositorio local al remoto | 2 % | Instrucciones de configuración en Issue #26 y comprobación de ejecución limpia en Issue #36. | Parcial — existe remoto; clon e instalación limpia pendientes de verificación |
| 7 | Uso de commits descriptivos | 2 % | Issue #38, política de commits y validador de Git Conventions. | Evidenciado — Issue #38 y Git Conventions |
| 8 | Uso de metodología Gitflow | 2 % | Estrategia de ramas dev y feature documentada y verificada en Issue #38 e Issue #36. | Evidenciado — CONTRIBUTING.md; trabajo en dev y ramas feature |
| 9 | Uso apropiado de ramas | 2 % | Issue #38, ramas de trabajo y pull requests. | Evidenciado — PRs de feature integrados hacia dev |
| 10 | Uso de nomenclatura en commits | 2 % | Issue #38, archivo .github/git-conventions.yml y validación CI. | Evidenciado — CONTRIBUTING.md, .github/git-conventions.yml y CI |
| 11 | Uso de issues en GitHub | 2 % | Backlog de Issues #1–#39 y trazabilidad en Issue #16. | Evidenciado — backlog de Issues #1–#39 |
| 12 | Uso de nomenclatura en ramas | 2 % | Issue #38 y validación de convenciones. | Evidenciado — CONTRIBUTING.md y validador CI |

### C3 — Gestionar equipos de forma eficiente (18 %)

| Nº | Indicador evaluable | Peso | Evidencia prevista en el proyecto | Estado |
|---:|---|---:|---|---|
| 13 | Uso de Kanban / burndown chart | 2 % | GitHub Project #1 y Issue #27. | Evidenciado — GitHub Project #1 (Kanban); no se halló burndown |
| 14 | Uso de roles definidos | 2 % | Issue #27, registro de roles y responsabilidades en el proyecto individual. | Pendiente — no se encontró registro verificable de roles |
| 15 | Uso de actas de reuniones | 2 % | Issue #27, registro de decisiones y reuniones cuando existan. | Pendiente — no se encontraron actas de reunión |
| 16 | Uso de dailies | 2 % | docs/daily/ y Issue #27. | Parcial — docs/daily contiene entradas 4–6 oct; cobertura incompleta |
| 17 | Uso de retrospectivas | 2 % | Issue #27, revisión y retrospectiva periódica. | Pendiente — sin retrospectiva verificable |
| 18 | Uso de herramientas de gestión de proyectos (Trello, Jira, etc.) | 2 % | GitHub Project #1 y Issue #27. | Evidenciado — GitHub Project #1 |
| 19 | Uso de estimación de tareas | 2 % | Issue #27 y planificación del Project #1. | Pendiente — sin evidencia suficiente de estimaciones |
| 20 | Prioriza al equipo | 2 % | Issue #27, evidencia de priorización y decisión aplicada al contexto individual. | Pendiente — sin evidencia suficiente de priorización de equipo |
| 21 | Uso de documentación (README) o celdas Markdown en notebook | 2 % | README, Issue #26 y documentación del repositorio. | Evidenciado — README y documentación del proyecto |

### C4 — Crear un modelo de inteligencia artificial con técnicas de Procesamiento del Lenguaje Natural (54 %)

| Nº | Indicador evaluable | Peso | Evidencia prevista en el proyecto | Estado |
|---:|---|---:|---|---|
| 22 | Uso de modelos LLM | 18 % | Issue #20, selección de stack; Issue #23, generación de contenido; Issue #25, evaluación; Issue #36, verificación final. | Parcial — adapters Groq/Ollama y pruebas mock; generación real no ejecutada. Ver docs/evidence/provider-smoke-tests-2026-10-13.md |
| 23 | Uso de frameworks para aplicaciones LLM (LangChain, CrewAI) | 18 % | Issue #20, LangChain; Issue #21 e Issue #23, integración y evidencia ejecutable; Issue #25, evaluación. | Evidenciado — boundary LangChain y pruebas; docs/evaluation-plan.md y roadmap |
| 24 | Uso de arquitecturas RAG | 18 % | Issue #32, recuperación de contexto de negocio; Issue #25, evidencia y evaluación; Issue #36, verificación final. | Evidenciado — docs/evidence/mvp-evaluation-issue-25.md y rag-issue-32-representative-runs.md (offline/mock) |

## Interpretación de alcance

### Issue #24 contract traceability

Issue #24 has an implemented and globally verified OpenSpec contract for explicit
human review, feedback/changed-input regeneration and approved-final text
copy/export. The evidence supports the repository's editorial-control practice;
no rubric indicator is marked complete by Issue #24 alone. See
`docs/evidence/issue-24-global-verification.md` for commands, criteria and
limitations. Issue #24 remains open pending human closure.

- C4 exige los tres indicadores: uso de modelos LLM, uso de un framework de aplicaciones LLM y uso de una arquitectura RAG. Cada uno vale 18 %.
- La rúbrica no exige generación de imágenes, comparación entre dos modelos LLM ni Docker. Esas capacidades pueden responder a decisiones de producto, coste o demostración, pero no deben presentarse como requisitos de la rúbrica.
- El indicador C1.2 exige contenido visual o demo. Puede acreditarse mediante una demostración funcional y materiales visuales; no prescribe generación de imágenes por IA.
- La pregunta enviada al profesor por Discord el 2026-10-05 se conserva para aclarar el nivel de evidencia esperado de RAG en un proyecto individual. La respuesta puede mejorar la estrategia de evaluación, pero no convierte RAG en opcional.

## Reglas de mantenimiento

- Todo cambio de alcance, diseño, OpenSpec, issue o plan de evaluación que afecte a la evaluación debe enlazar a este documento.
- Los requisitos y pesos de la rúbrica se modifican aquí antes de reflejarse en otros documentos.
- La autoevaluación final debe sustituir “Pendiente de autoevaluación” por evidencia concreta o una limitación explícita.
- Las referencias históricas que decían que la rúbrica no estaba disponible quedan sustituidas por este documento.