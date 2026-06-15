# Proyecto: Análisis del Mercado Laboral IT en Panamá

> **Documento de especificación para Claude Code.** Léelo completo antes de empezar. Implementa por fases en el orden indicado. Al final de cada fase, verifica los criterios de aceptación antes de pasar a la siguiente.

---

## 1. Contexto del proyecto

Este es un **proyecto universitario** (Gestión de la Información, UTP-FISC). Corresponde al **Segundo Parcial** de un proyecto integrador. El objetivo es construir un sistema de gestión de información sobre el **mercado laboral IT en Panamá**: ingerir ofertas de empleo de varias fuentes, procesarlas, aplicar una técnica de Machine Learning y mostrar todo en un dashboard interactivo.

**Entorno de ejecución:** Windows 10 (PC del desarrollador). Usar `venv` de Python. No asumir Docker ni Linux.

**IMPORTANTE — Restricción del profesor:** En esta fase **NO se debe implementar ningún LLM ni chatbot**. La extracción de habilidades/tecnologías debe hacerse con técnicas clásicas (matching de diccionario de keywords, regex). Nada de OpenAI, Anthropic, ni modelos generativos. Esto es un requisito estricto.

---

## 2. Requisitos de evaluación (lo que se califica)

| Componente | Peso | Qué debe cumplirse |
|---|---|---|
| **Pipeline de datos** | 30% | Ingesta de **mínimo 2 fuentes diferentes** + preprocesamiento + transformación, todo funcional y documentado |
| **Análisis ML** | 25% | Al menos **1 técnica** de ML: clasificación, clustering o regresión |
| **Visualización / Dashboard** | 25% | Dashboard interactivo en **Streamlit** |
| **Documentación** | 20% | README completo en repositorio GitHub |

**Requisitos técnicos obligatorios:** Python · pipeline funcional y documentado · 2+ fuentes de datos diferentes · dashboard en Streamlit · repositorio GitHub con README.

---

## 3. Arquitectura general

Tres fuentes de datos de **distinto tipo**, normalizadas a un **esquema común**, unificadas en un solo dataset que alimenta el ML y el dashboard.

```
  Fuente 1 (SCRAPING)      Fuente 2 (API)        Fuente 3 (DATASET)
  Computrabajo Panamá      Remotive (jobs IT)    CSV de Kaggle
         │                       │                      │
         ▼                       ▼                      ▼
  ┌──────────────────────────────────────────────────────────┐
  │  1. INGESTA   → guardar datos crudos en data/raw/         │
  ├──────────────────────────────────────────────────────────┤
  │  2. LIMPIEZA  → nulos, duplicados, normalizar texto       │
  ├──────────────────────────────────────────────────────────┤
  │  3. TRANSFORMACIÓN → mapear a esquema común +             │
  │     extraer tecnologías por matching de keywords          │
  ├──────────────────────────────────────────────────────────┤
  │  4. DATASET UNIFICADO → data/processed/ofertas.csv        │
  └──────────────────────────────────────────────────────────┘
         │                                              │
         ▼                                              ▼
   ML (clustering/                              Dashboard Streamlit
    regresión)                                  (filtros + gráficas)
```

### Esquema común (toda oferta, venga de donde venga, se normaliza a esto)

| Campo | Tipo | Descripción |
|---|---|---|
| `titulo` | str | Título del puesto |
| `empresa` | str | Nombre de la empresa (puede ser nulo) |
| `ubicacion` | str | Ciudad / país / "Remoto" |
| `tecnologias` | list[str] | Lista de tecnologías detectadas |
| `salario_min` | float | Salario mínimo (nulo si no hay) |
| `salario_max` | float | Salario máximo (nulo si no hay) |
| `fecha` | date | Fecha de publicación |
| `fuente` | str | `computrabajo` / `remotive` / `kaggle` |
| `descripcion` | str | Texto de la oferta |

---

## 4. Estructura de carpetas a generar

```
mercado-it-panama/
├── data/
│   ├── raw/                      # datos crudos por fuente (gitignored salvo .gitkeep)
│   └── processed/                # dataset unificado final
├── src/
│   ├── __init__.py
│   ├── config.py                 # rutas, constantes, diccionario de tecnologías
│   ├── ingesta/
│   │   ├── __init__.py
│   │   ├── scraper_computrabajo.py
│   │   ├── api_remotive.py
│   │   └── loader_dataset.py
│   ├── procesamiento/
│   │   ├── __init__.py
│   │   ├── limpieza.py
│   │   ├── extraccion_tecnologias.py
│   │   └── transformacion.py
│   └── ml/
│       ├── __init__.py
│       └── analisis.py
├── dashboard/
│   └── app.py                    # Streamlit
├── notebooks/
│   └── exploracion.ipynb         # opcional, exploración de datos
├── run_pipeline.py               # orquesta todo el pipeline de punta a punta
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 5. Fases de implementación

### FASE 0 — Setup del proyecto
- Crear la estructura de carpetas completa.
- `requirements.txt` con: `requests`, `beautifulsoup4`, `lxml`, `pandas`, `numpy`, `scikit-learn`, `streamlit`, `plotly`, `python-dateutil`. (Si Computrabajo requiere render de JavaScript, añadir `playwright` y documentarlo).
- `.gitignore` que ignore `venv/`, `__pycache__/`, `*.pyc`, y `data/raw/*` (con `.gitkeep`).
- `src/config.py` con:
  - Rutas a `data/raw` y `data/processed`.
  - **Diccionario maestro de tecnologías** para el matching. Incluir al menos: lenguajes (`python`, `java`, `javascript`, `typescript`, `php`, `c#`, `go`, `ruby`, `kotlin`, `swift`), frameworks (`react`, `angular`, `vue`, `laravel`, `django`, `spring`, `node.js`, `.net`, `flask`), bases de datos (`mysql`, `mariadb`, `postgresql`, `mongodb`, `redis`, `sql server`, `oracle`), cloud/devops (`aws`, `azure`, `gcp`, `docker`, `kubernetes`, `git`, `jenkins`, `terraform`), y otros (`linux`, `rest`, `graphql`, `html`, `css`). Estructurarlo de forma que el matching sea case-insensitive y maneje variantes (ej. "node" / "nodejs" / "node.js").

**Criterio de aceptación:** la estructura existe, `pip install -r requirements.txt` corre sin error en un venv limpio de Windows.

---

### FASE 1 — Fuente 2: API de Remotive (empezar por aquí, es la más estable)

> Se empieza por la API porque devuelve datos reales, limpios y sin bloqueos, lo que permite probar el resto del pipeline rápido.

- `src/ingesta/api_remotive.py`:
  - Consumir la API pública de Remotive de empleos (endpoint de jobs, categoría software-dev). **No requiere API key.** Verificar el endpoint vigente al implementar (el formato histórico es un GET que devuelve JSON con una lista bajo la clave `jobs`).
  - Permitir filtrar por categoría de software/IT y opcionalmente por término de búsqueda.
  - Guardar la respuesta cruda en `data/raw/remotive_raw.json`.
  - Exponer una función `ingerir_remotive() -> list[dict]` que devuelva la lista de ofertas crudas.
- Manejar errores de red con try/except y mensajes claros. Si la API falla, el pipeline debe seguir con las otras fuentes (degradación elegante).

**Nota de relevancia para el tema:** Remotive son empleos remotos tech. Son relevantes para "mercado IT en Panamá" porque un desarrollador panameño puede aplicar a remotos. Documentar esto en el README.

**Criterio de aceptación:** ejecutar el módulo descarga ofertas reales y guarda el JSON crudo.

---

### FASE 2 — Fuente 3: Dataset de Kaggle (la base de volumen)

- `src/ingesta/loader_dataset.py`:
  - Cargar un CSV de empleos/salarios IT desde `data/raw/`. El usuario descargará manualmente un dataset de Kaggle (ej. datasets de "data science / tech job salaries" o "LinkedIn tech jobs") y lo colocará ahí.
  - El loader debe ser **robusto a columnas variables**: detectar columnas relevantes (título, salario, ubicación, skills/descripción) de forma flexible, con un mapeo configurable al inicio del archivo. Documentar qué columnas espera.
  - Exponer `cargar_dataset(ruta) -> pd.DataFrame`.
- En el README, dar instrucciones claras de qué dataset descargar y dónde ponerlo. Incluir un **dataset de ejemplo pequeño** (`data/raw/ejemplo_kaggle.csv`, 15-20 filas inventadas pero realistas) para que el pipeline corra aunque el usuario aún no haya bajado el real.

**Criterio de aceptación:** el loader lee el CSV de ejemplo y devuelve un DataFrame con las columnas mapeadas.

---

### FASE 3 — Fuente 1: Scraper de Computrabajo Panamá (la más delicada)

> Se deja de última porque el scraping es lo más frágil y puede requerir ajustes según el HTML real del sitio al momento de ejecutar.

- `src/ingesta/scraper_computrabajo.py`:
  - Scrapear ofertas de empleo del área de tecnología/informática de Computrabajo Panamá.
  - **Antes de scrapear, revisar y respetar el `robots.txt` del sitio.** Añadir headers de user-agent realista y un `time.sleep` entre requests (1-2 segundos) para no saturar el servidor. Ser un buen ciudadano de la web.
  - Empezar con `requests` + `BeautifulSoup`. **Si el contenido se carga por JavaScript** (las ofertas no aparecen en el HTML inicial), entonces migrar a `playwright` y documentarlo en el README.
  - Extraer por cada oferta: título, empresa, ubicación, fecha si está disponible, y el texto/snippet de la descripción. Manejar paginación (varias páginas de resultados) con un límite configurable de páginas.
  - Guardar crudo en `data/raw/computrabajo_raw.json`.
  - Exponer `scrapear_computrabajo(max_paginas=3) -> list[dict]`.
  - **Robustez:** si el sitio bloquea, cambia de estructura o falla, capturar la excepción, loguear una advertencia clara, y devolver lista vacía (el pipeline continúa con las otras dos fuentes). El proyecto NO debe romperse si esta fuente falla.

**Criterio de aceptación:** el scraper intenta la extracción y, o bien devuelve ofertas reales, o falla de forma controlada sin romper el pipeline.

---

### FASE 4 — Procesamiento (limpieza + extracción + transformación)

- `src/procesamiento/limpieza.py`:
  - Funciones para: eliminar registros nulos críticos (sin título), quitar duplicados, normalizar texto (trim, minúsculas donde aplique, quitar HTML residual), y **parsear salarios** desde strings variados a `salario_min` / `salario_max` numéricos (manejar rangos "B/. 1,500 - 2,000", valores únicos, monedas, y nulos).
- `src/procesamiento/extraccion_tecnologias.py`:
  - Función `extraer_tecnologias(texto: str) -> list[str]` que recorre el diccionario maestro de `config.py` y devuelve las tecnologías encontradas en el texto (case-insensitive, manejando variantes y límites de palabra con regex para evitar falsos positivos, ej. que "go" no matchee dentro de "google").
  - **Esta es la función que reemplaza al LLM.** Debe estar bien comentada explicando que es matching de diccionario.
- `src/procesamiento/transformacion.py`:
  - Tomar las salidas crudas de las 3 fuentes y mapear cada una al **esquema común** (sección 3).
  - Aplicar limpieza y extracción de tecnologías.
  - Concatenar todo en un solo DataFrame.
  - Guardar en `data/processed/ofertas.csv` (y opcionalmente `.parquet`).
  - Exponer `construir_dataset_unificado() -> pd.DataFrame`.

**Criterio de aceptación:** se genera `data/processed/ofertas.csv` con el esquema común, combinando las fuentes disponibles, con la columna `tecnologias` poblada.

---

### FASE 5 — Análisis ML

> Cumplir el requisito de "al menos 1 técnica de ML". Implementar **dos** análisis para robustez (clustering + regresión), pero como mínimo uno debe quedar sólido.

- `src/ml/analisis.py`:
  - **Clustering (principal):** agrupar ofertas por perfil tecnológico. Vectorizar las tecnologías (one-hot / multi-hot encoding de la lista `tecnologias`), aplicar **K-Means** (con selección de k razonable, ej. método del codo) para descubrir "familias" de puestos (ej. cluster frontend, cluster backend, cluster data, cluster devops). Devolver las etiquetas de cluster y un resumen de las tecnologías dominantes por cluster.
  - **Regresión (secundaria, si hay suficientes datos de salario):** predecir `salario` en función de las tecnologías presentes y la ubicación. Usar un modelo simple (regresión lineal o RandomForestRegressor). Reportar métrica (ej. MAE/R²). Si no hay suficientes datos salariales, documentarlo y dejar el clustering como técnica principal.
  - Exponer funciones que devuelvan resultados consumibles por el dashboard (no solo prints).
  - Guardar resultados procesados si ayuda al dashboard (ej. dataset con columna `cluster`).

**Criterio de aceptación:** al menos una técnica de ML corre sobre el dataset unificado y produce resultados interpretables.

---

### FASE 6 — Dashboard en Streamlit

- `dashboard/app.py`:
  - Cargar `data/processed/ofertas.csv` (con los clusters del ML).
  - **Filtros interactivos en el sidebar:** por tecnología (multiselect), por fuente, por rango de salario (slider), por ubicación, y por rango de fecha si hay datos.
  - **Visualizaciones (usar Plotly):**
    1. Top tecnologías más demandadas (bar chart) — responde directo al tema del proyecto.
    2. Distribución de salarios (histograma o boxplot), idealmente por tecnología.
    3. Ofertas por fuente (para evidenciar el multi-fuente del pipeline).
    4. Resultado del clustering (ej. scatter con reducción de dimensionalidad PCA a 2D, coloreado por cluster, o un resumen de tecnologías por cluster).
    5. Tendencia temporal de publicaciones si hay fechas (line chart).
  - **Métricas resumen arriba** (st.metric): total de ofertas, nº de fuentes, nº de tecnologías únicas, salario promedio.
  - Tabla filtrable con las ofertas (st.dataframe).
  - Que se ejecute con `streamlit run dashboard/app.py`.

**Criterio de aceptación:** el dashboard levanta, los filtros funcionan y refrescan las gráficas, y todas las visualizaciones renderizan con los datos reales del pipeline.

---

### FASE 7 — Orquestación y documentación

- `run_pipeline.py`: script que ejecuta el pipeline completo de punta a punta en orden (ingesta de las 3 fuentes → procesamiento → genera dataset unificado → corre ML y guarda resultados). Con mensajes de progreso claros por consola. Debe poder correrse con `python run_pipeline.py`.
- `README.md` completo (ver sección 6).

**Criterio de aceptación:** un usuario nuevo puede clonar el repo, seguir el README, correr el pipeline y levantar el dashboard sin pasos faltantes.

---

## 6. Contenido del README.md

El README vale parte del 20% de documentación. Debe incluir:

1. **Título y descripción** del proyecto y la problemática que resuelve.
2. **Tema:** Análisis del Mercado Laboral IT en Panamá (Grupo 4).
3. **Arquitectura del pipeline** (incluir el diagrama de la sección 3).
4. **Fuentes de datos:** las 3, explicando el tipo de cada una (scraping / API / dataset) y por qué son relevantes al tema. Justificar que Remotive (remotos) aplica a devs panameños.
5. **Técnica(s) de ML** aplicada(s) y qué se descubre con ellas.
6. **Requisitos previos** (Python 3.x, etc.).
7. **Instalación paso a paso** (crear venv en Windows, instalar requirements).
8. **Cómo descargar el dataset de Kaggle** y dónde colocarlo.
9. **Cómo ejecutar:** primero `python run_pipeline.py`, luego `streamlit run dashboard/app.py`.
10. **Estructura del proyecto** (árbol de carpetas).
11. **Nota sobre el scraping:** advertencia de que la disponibilidad/estructura de Computrabajo puede cambiar y que el pipeline degrada con elegancia si una fuente falla.
12. **Limitaciones y trabajo futuro** (mencionar que el chatbot/LLM y la predicción de habilidades emergentes son fase posterior — NO implementados aquí por alcance).

---

## 7. Principios de implementación

- **Código en español** (nombres de variables/funciones en español, comentarios en español) para consistencia con el contexto académico.
- **Comentar bien** las partes clave, especialmente la extracción de tecnologías (la que sustituye al LLM) y el ML.
- **Degradación elegante:** si una fuente de datos falla, el pipeline sigue con las demás. Nunca debe romperse todo por una fuente caída.
- **Nada de LLMs/chatbots** en esta fase. Es un requisito estricto del profesor.
- **Reproducible en Windows** con venv. No asumir herramientas de Linux/Mac.
- Verificar los **criterios de aceptación** de cada fase antes de avanzar.

---

## 8. Orden de ejecución recomendado para Claude Code

1. Fase 0 (setup) completa.
2. Fase 1 (API Remotive) — obtener datos reales rápido.
3. Fase 2 (dataset Kaggle + dataset de ejemplo).
4. Fase 4 (procesamiento) — ya con 2 fuentes se puede construir el dataset unificado y validar el esquema.
5. Fase 5 (ML) — sobre el dataset unificado.
6. Fase 6 (dashboard) — visualizar lo que ya existe.
7. Fase 3 (scraper Computrabajo) — añadir la tercera fuente al final, integrándola al pipeline ya funcional.
8. Fase 7 (orquestador + README) — cerrar todo.

> Construir un pipeline que funcione con 2 fuentes primero y añadir el scraping al final reduce el riesgo: si Computrabajo da problemas, ya tienes un proyecto entregable y completo con API + dataset.
