# Generador de contenido LLMs · G. Granja

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Web-Next.js-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![LangChain](https://img.shields.io/badge/IA-LangChain-1C3C3C)](https://www.langchain.com/)
[![Estado](https://img.shields.io/badge/estado-demo_local-orange)](https://github.com/Bootcamp-IA-MAD-P7/generador-contenido-llms-ggranja)

Aplicación para preparar borradores de contenido para redes sociales a partir de un brief y la información de un negocio. Esta copia se entrega en la organización [Bootcamp-IA-MAD-P7](https://github.com/Bootcamp-IA-MAD-P7).

## Arranque local

Requisitos: Python 3.11 o superior, Node.js 22 y npm.

Desde la raíz del repositorio, prepara el entorno y arranca la API:

~~~bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python scripts/prepare_demo.py
python -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 18000
~~~

En otra terminal, arranca la web:

~~~bash
cd apps/web
npm ci
npm run dev
~~~

Abre [http://localhost:3000/login](http://localhost:3000/login) e inicia sesión con **gabriela / gabriela**. Son credenciales solo para la demo local. La API queda en http://127.0.0.1:18000; puedes comprobarla en /readiness. La demo usa el proveedor determinista mock y solo escucha en localhost.

## Pruebas

~~~bash
python -m pytest -q --import-mode=importlib tests
~~~

~~~bash
cd apps/web
npm test
npm run typecheck
~~~

## Alcance y límites

La entrega permite recorrer el flujo local de brief y borrador con API FastAPI, interfaz Next.js y proveedor simulado. El repositorio incluye evidencia de LangChain y RAG; la demo offline no demuestra llamadas a proveedores reales.

No están disponibles en esta demo las integraciones reales de Groq/Ollama, generación de imágenes, voz ni OAuth/publicación en Instagram. Quedan fuera de la primera entrega las Stories, LinkedIn, autopublicación en Facebook, campañas desatendidas y gestión multiempresa. Tampoco se entregan carruseles como conjuntos completos de imágenes ni vídeos Reel renderizados.

## Evidencia frente a la rúbrica

| Competencia | Peso | Estado resumido |
|---|---:|---|
| C1 · Comunicación | 12% | Evidencias documentadas. |
| C2 · Gestión del proyecto y control de versiones | 16% | Mayormente evidenciado; queda pendiente la verificación completa de una instalación limpia. |
| C3 · Gestión de equipos | 18% | Parcial; faltan evidencias de roles, actas, retrospectivas y estimaciones/priorización. |
| C4 · NLP / IA | 54% | LangChain y RAG evidenciados; la integración de modelos LLM sigue parcial mientras falten pruebas reales de proveedor. |

La autoevaluación conservadora del proyecto es **68/100 provisional**, no una nota oficial. Consulta el [seguimiento detallado de la rúbrica](docs/rubric-traceability.md), la [autoevaluación](docs/self-assessment-2026-10-13.md), el [alcance](docs/scope.md) y la [guía de demo local](docs/local-demo.md).
