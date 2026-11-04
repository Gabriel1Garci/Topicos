# Guía Didáctica Completa: Análisis del Mercado Laboral IT en Panamá

> **Proyecto Universitario** — Gestión de la Información · UTP-FISC · Segundo Parcial  
> **Grupo 4** — Repositorio: https://github.com/Gabriel1Garci/Topicos

---

## Índice

1. [¿Qué es este proyecto?](#1-qué-es-este-proyecto)
2. [Conceptos fundamentales](#2-conceptos-fundamentales)
3. [Arquitectura del sistema](#3-arquitectura-del-sistema)
4. [Pipeline de datos (ETL)](#4-pipeline-de-datos-etl)
5. [Machine Learning aplicado](#5-machine-learning-aplicado)
6. [Dashboard interactivo](#6-dashboard-interactivo)
7. [Estructura del código](#7-estructura-del-código)
8. [Cómo ejecutar el proyecto](#8-cómo-ejecutar-el-proyecto)
9. [Pruebas (tests)](#9-pruebas-tests)
10. [Posibles mejoras y trabajo futuro](#10-posibles-mejoras-y-trabajo-futuro)
11. [Glosario de términos](#11-glosario-de-términos)

---

## 1. ¿Qué es este proyecto?

### 1.1. El problema que resuelve

Imagina que eres un estudiante de tecnología en Panamá y quieres saber:

- **¿Qué tecnologías** (Python, React, AWS, etc.) están pidiendo más las empresas?
- **¿Cuánto pagan** en promedio por cada tecnología?
- **¿Qué perfiles** existen (frontend, backend, data, devops) y cómo se agrupan?
- **¿De dónde vienen** las ofertas (bolsas de trabajo panameñas, empleos remotos, datasets)?

Este proyecto **automatiza** la respuesta a esas preguntas: descarga datos de múltiples fuentes, los limpia, extrae información útil, aplica Machine Learning para descubrir patrones, y muestra todo en un dashboard interactivo.

### 1.2. Contexto académico

Es un proyecto integrador de la materia **Gestión de la Información** (UTP-FISC). La gestión de la información trata sobre cómo capturar, almacenar, procesar y presentar datos de manera que generen valor. En este caso, los datos son ofertas de empleo IT en Panamá.

### 1.3. Restricción importante

Por decisión del profesor, **NO se permite usar LLMs (Large Language Models)** como ChatGPT, Claude, etc. para extraer tecnologías de los textos. En su lugar, se usa una técnica clásica llamada **matching de diccionario con regex** (expresiones regulares). Esto es intencional: enseñar que muchos problemas de extracción de información se resuelven sin inteligencia artificial generativa.

---

## 2. Conceptos fundamentales

Antes de entrar al código, necesitas entender estos conceptos base:

### 2.1. ETL (Extract, Transform, Load)

Es el proceso de mover datos desde su origen hasta un destino donde puedan analizarse:

| Fase | ¿Qué significa? | En este proyecto |
|------|----------------|------------------|
| **Extract** | Obtener datos de sus fuentes originales | Scraping web, llamadas a API REST, lectura de CSV |
| **Transform** | Limpiar, normalizar y enriquecer los datos | Quitar HTML, parsear salarios, extraer tecnologías con regex, unificar esquemas |
| **Load** | Guardar los datos transformados | Escribir `data/processed/ofertas.csv` |

### 2.2. Web Scraping

Técnica para extraer datos de sitios web automáticamente. En lugar de copiar y pegar manualmente cada oferta de empleo, un programa (scraper) navega el sitio y extrae la información estructurada.

**Herramientas usadas:**
- **BeautifulSoup4**: Parsea HTML estático (para Computrabajo)
- **Playwright**: Controla un navegador real (para Konzerta, porque carga contenido con JavaScript)

**Buenas prácticas incluidas:**
- `time.sleep(1.5)` entre requests — no saturar el servidor
- User-Agent realista — identificarse como navegador normal
- Try/except en cada paso — si algo falla, el pipeline continúa

### 2.3. API REST

Una API (Application Programming Interface) es un intermediario que permite que dos programas se comuniquen. REST es un estilo de diseño de APIs donde se usan URLs para acceder a recursos.

**Remotive API** es pública y no requiere autenticación. Simplemente haces un GET a `https://remotive.com/api/remote-jobs` y recibes JSON con cientos de ofertas de empleo remoto.

### 2.4. Expresiones Regulares (Regex / Regexp)

Son patrones para buscar texto. Piensa en ellas como un "CTRL+F" súper potente.

Ejemplo simple:
```python
r"\bpython\b"   # Busca la palabra "python" con bordes de palabra
```
- `\b` = word boundary (frontera de palabra). Evita que "python" aparezca dentro de "pythonista" o "python123"
- `re.IGNORECASE` = ignora mayúsculas/minúsculas

En el proyecto, las regex se usan para detectar tecnologías en la descripción de las ofertas:
```python
# Si el texto contiene "python", "react", "aws", etc. → lo detecta
```

### 2.5. Machine Learning básico

#### K-Means Clustering
Algoritmo de **aprendizaje no supervisado** que agrupa datos similares. No le dices qué grupos buscar; él descubre patrones.

**Analogía**: Tienes una bolsa con frutas (manzanas, naranjas, uvas). K-Means las agrupa sin decirle los nombres:
- Grupo A: frutas rojas y redondas → manzanas
- Grupo B: frutas naranjas y redondas → naranjas
- Grupo C: frutas pequeñas y ovaladas → uvas

En el proyecto, agrupa ofertas por tecnologías:
- Cluster 0: ofertas con Python + Django → perfil backend
- Cluster 1: ofertas con React + JavaScript → perfil frontend
- Cluster 2: ofertas con AWS + Docker → perfil devops

#### Método del codo (Elbow Method)
Para K-Means necesitas decir cuántos grupos (K) formar. El método del codo prueba varios K y mide la "inercia" (qué tan compactos son los grupos). El K óptimo es donde la mejora deja de ser significativa — se ve como un "codo" en la gráfica.

#### Random Forest Regressor
Algoritmo de **aprendizaje supervisado** que predice un número. En este caso, predice el salario basado en las tecnologías y ubicación.

**Analogía**: Imagina miles de árboles de decisión (de ahí "forest"). Cada árbol dice "si tiene Python y está en Panamá, gana $3000". El bosque promedia todos los árboles para dar una predicción más precisa.

#### PCA (Principal Component Analysis)
Reduce la dimensionalidad de los datos. Si tienes 45 tecnologías diferentes (45 dimensiones), PCA las reduce a 2 dimensiones para poder graficarlas en un scatter plot 2D.

### 2.6. Dashboard

Interfaz visual que muestra indicadores clave (KPIs), gráficas y filtros. En este proyecto se usa **Streamlit**, un framework de Python que convierte scripts en aplicaciones web interactivas con solo unas líneas de código.

### 2.7. Plotly

Librería de Python para crear gráficas interactivas (barras, dispersión, líneas, histogramas, etc.). A diferencia de imágenes estáticas, las gráficas de Plotly se pueden ampliar, pasar el mouse para ver valores, etc.

---

## 3. Arquitectura del sistema

### 3.1. Diagrama general

```
 ┌─────────────────────────────────────────────────────────────┐
 │                      FUENTES DE DATOS                        │
 │                                                              │
 │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
 │   │  Konzerta    │  │ Computrabajo │  │   CSV/Kaggle │      │
 │   │  (Scraping   │  │  (Scraping   │  │  (Dataset    │      │
 │   │  Playwright) │  │  BS4)        │  │   estático)  │      │
 │   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
 │          │                 │                 │               │
 └──────────┼─────────────────┼─────────────────┼───────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                     PIPELINE DE DATOS                        │
 │                                                              │
 │   1. INGESTA:   Descarga datos → data/raw/*.json             │
 │                                                              │
 │   2. LIMPIEZA:  Quitar nulos, duplicados, HTML, parsear $$   │
 │                                                              │
 │   3. TRANSFORMACIÓN: Mapear a esquema común + extraer techs  │
 │                                                              │
 │   4. DATASET UNIFICADO: data/processed/ofertas.csv           │
 └──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                    ANÁLISIS ML                               │
 │                                                              │
 │   K-Means Clustering  →  Agrupa ofertas por perfil tech     │
 │   RandomForest Reg.   →  Predice salarios (si hay datos)    │
 └──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                   DASHBOARD STREAMLIT                        │
 │                                                              │
 │   Gráficas interactivas + Filtros + Métricas + Tabla        │
 │   Acceso: http://localhost:8501                              │
 └─────────────────────────────────────────────────────────────┘
```

### 3.2. Esquema común de datos

Todas las ofertas, sin importar de qué fuente vengan, se transforman a este mismo formato:

| Campo | Tipo | Ejemplo | ¿De dónde sale? |
|-------|------|---------|-----------------|
| `titulo` | string | "python developer" | Limpiado del título original |
| `empresa` | string | "techcorp" | Nombre de la empresa |
| `ubicacion` | string | "ciudad de panamá" | Ubicación del puesto |
| `tecnologias` | lista | ["python", "django"] | Detectadas por regex |
| `salario_min` | float | 1500.0 | Min del rango salarial |
| `salario_max` | float | 2000.0 | Max del rango salarial |
| `fecha` | date | 2024-01-15 | Fecha de publicación |
| `fuente` | string | "konzerta" | Origen: konzerta/computrabajo/remotive/kaggle |
| `descripcion` | string | "buscamos developer..." | Texto completo de la oferta |

### 3.3. Principio de diseño clave: Degradación elegante

Cada fuente de datos puede fallar independientemente:
- Si Konzerta cambia su HTML → el scraper devuelve lista vacía
- Si Computrabajo bloquea el scraper → devuelve lista vacía
- Si la API de Remotive está caída → devuelve lista vacía
- Si el CSV de Kaggle no existe → devuelve DataFrame vacío

El pipeline **no se rompe**. Simplemente continúa con las fuentes que sí funcionaron.

---

## 4. Pipeline de datos (ETL)

### 4.1. Fase 1: Ingesta (Extracción)

#### Fuente 1: Konzerta Panamá (`scraper_konzerta.py`)

**¿Qué hace?** Navega https://www.konzerta.com/en-panama/empleos-area-tecnologia-sistemas-y-telecomunicaciones.html, extrae ofertas de tecnología.

**¿Cómo funciona?**
1. Abre un navegador Chrome invisible (headless) usando Playwright
2. Va a la URL de búsqueda de empleos tech
3. Espera que la página cargue completamente
4. Ejecuta JavaScript dentro del navegador para extraer datos con `page.evaluate()`
5. Itera por varias páginas (configurable, por defecto 5)
6. Guarda el resultado en `data/raw/konzerta_raw.json`
7. Si algo falla (sitio caído, cambio de estructura), retorna lista vacía

**¿Por qué Playwright y no solo requests?** Konzerta es una SPA (Single Page Application) — los datos no vienen en el HTML inicial, se cargan con JavaScript. Playwright controla un navegador real que ejecuta ese JS.

#### Fuente 2: Computrabajo Panamá (`scraper_computrabajo.py`)

**¿Qué hace?** Scrapea https://www.computrabajo.com.pa/empleos-de-informatica-y-sistemas.

**¿Cómo funciona?**
1. Hace requests HTTP con headers de navegador real
2. Parsea el HTML con BeautifulSoup
3. Busca contenedores de ofertas con múltiples selectores CSS de respaldo
4. Itera páginas con `time.sleep(1.5)` entre requests
5. Guarda en `data/raw/computrabajo_raw.json`

**Problema conocido:** Computrabajo puede cargar ofertas con JavaScript. Si el scraper no las encuentra, el pipeline continúa sin problema (degradación elegante).

#### Fuente 3: API de Remotive (`api_remotive.py`)

**¿Qué hace?** Consume la API pública de Remotive (https://remotive.com/api/remote-jobs) filtrando por categoría "software-dev".

**¿Por qué incluir empleos remotos?** Aunque Remotive lista empleos globales, un desarrollador panameño puede aplicar a trabajos remotos. Es relevante para el mercado IT panameño.

**¿Cómo funciona?**
1. Hace un GET request a la API con la categoría deseada
2. Recibe JSON con cientos de ofertas
3. Guarda el JSON crudo en `data/raw/remotive_raw.json`
4. No requiere API key, no tiene límite de requests

#### Fuente 4: Dataset CSV (`loader_dataset.py`)

**¿Qué hace?** Carga un archivo CSV desde `data/raw/` mediante un loader flexible.

**Flexibilidad:** El dataset puede venir con diferentes nombres de columna (job_title, title, titulo, position...). El loader tiene un diccionario de mapeo que prueba variantes hasta encontrar la correcta:

```python
COLUMNAS_MAPEO = {
    "titulo_raw": ["job_title", "title", "titulo", "position", "puesto", "job"],
    "empresa_raw": ["company", "company_name", "empresa", "employer", "organization"],
    ...
}
```

### 4.2. Fase 2: Limpieza (`limpieza.py`)

#### Limpiar texto (`limpiar_texto`)
1. Convierte HTML a texto plano (quita tags como `<p>`, `<b>`, etc.)
2. Normaliza espacios múltiples a uno solo
3. Convierte a minúsculas
4. Retorna string vacío si el valor es None

#### Parsear salarios (`parsear_salario`)
Los salarios vienen en formatos inconsistentes:
- `"B/. 1,500 - 2,000"` → (1500.0, 2000.0)
- `"USD 3000-4000"` → (3000.0, 4000.0)
- `"$2500"` → (2500.0, 2500.0)
- `"Competitive salary"` → (None, None)

La función:
1. Quita símbolos de moneda, coma de miles, texto
2. Extrae números ≥ 100 (filtra años)
3. Si hay 1 número → mismo min y max
4. Si hay 2+ números → min y max

#### Eliminar duplicados (`eliminar_duplicados_nulos`)
1. Quita filas sin título (no sirven)
2. Quita filas duplicadas (mismo título + descripción)

### 4.3. Fase 3: Extracción de tecnologías (`extraccion_tecnologias.py`)

**Esta es la función que reemplaza al LLM.** Es el corazón del procesamiento.

#### ¿Cómo funciona?

1. **Importa el diccionario maestro** de `config.py` con 45 tecnologías agrupadas en categorías:

   | Categoría | Tecnologías |
   |-----------|-------------|
   | Lenguajes | python, java, javascript, typescript, php, c#, go, ruby, kotlin, swift |
   | Frameworks | react, angular, vue, laravel, django, spring, node.js, .net, flask, fastapi |
   | Bases de datos | mysql, mariadb, postgresql, mongodb, redis, sql server, oracle, sqlite |
   | Cloud/DevOps | aws, azure, gcp, docker, kubernetes, git, jenkins, terraform, linux |
   | Otros | rest, graphql, html, css, sql, power bi, tableau, excel |

2. **Pre-compila patrones regex** al importar el módulo. Cada tecnología tiene variantes:
   ```python
   "node.js": ["node\\.js", "nodejs", "node"]
   "go": ["golang", "go"]   # "go" solo no matchearía, también usa "golang"
   ```

3. **Busca en el texto** de título + descripción. Si algún patrón matchea, registra la tecnología.

4. **Protege contra falsos positivos** usando `\b` (word boundary). Ejemplo: "go" dentro de "google" no matchea.

#### ¿Qué es exactamente una regex?

Una expresión regular es un patrón de búsqueda en texto. Ejemplos:

| Patrón | Significado | Matchea | No matchea |
|--------|-------------|---------|------------|
| `\bpython\b` | Palabra exacta "python" | "python dev" | "pythonista" |
| `\breact\b` | Palabra exacta "react" | "react developer" | "reactive" |
| `node\.js` | "node.js" (el punto es literal) | "node.js dev" | "nodejs" |
| `\bgolang\b` | Palabra exacta "golang" | "golang dev" | — |

### 4.4. Fase 4: Transformación y unificación (`transformacion.py`)

Toma los datos crudos de cada fuente y los mapea al esquema común:

```python
def transformar_konzerta(ofertas_crudas):
    for cada oferta:
        descripcion = limpiar_texto(original)
        titulo = limpiar_texto(original)
        techs = extraer_tecnologias(titulo + " " + descripcion)
        sal_min, sal_max = parsear_salario(original)
        guardar(titulo, empresa, ubicacion, techs, sal_min, sal_max, fecha, "konzerta", descripcion)
```

**El orquestador `construir_dataset_unificado()`**:
1. Scrapea Konzerta y transforma sus datos
2. Lee Computrabajo crudo (si existe) y transforma
3. Carga CSV de Kaggle y transforma
4. Concatena todo en un solo DataFrame
5. Elimina duplicados entre fuentes
6. Serializa tecnologías como "python|django|aws" (pipe-separated para CSV)
7. Guarda en `data/processed/ofertas.csv`

---

## 5. Machine Learning aplicado

### 5.1. Preparación de datos (`analisis.py`)

#### De texto a números (One-Hot Encoding)

Las tecnologías vienen como strings: `"python|django|postgresql"`. Pero los algoritmos ML solo entienden números.

**One-Hot Encoding** convierte cada tecnología en una columna de 0s y 1s:

| Oferta | python | django | postgresql | react | css | aws |
|--------|--------|--------|------------|-------|-----|-----|
| Dev 1  | 1      | 1      | 1          | 0     | 0   | 0   |
| Dev 2  | 0      | 0      | 0          | 1     | 1   | 0   |
| Dev 3  | 0      | 0      | 0          | 0     | 0   | 1   |

Esto se hace con `MultiLabelBinarizer` de scikit-learn.

### 5.2. K-Means Clustering (técnica principal)

**Proceso:**
1. Vectorizar tecnologías (one-hot encoding)
2. Encontrar K óptimo con método del codo
3. Aplicar K-Means con ese K
4. Para cada cluster, encontrar las tecnologías más comunes
5. Asignar nombre sugerido (ej. "python, django" → backend)

**Salida:**
```python
{
    0: {"n_ofertas": 15, "tecnologias_top": ["python", "django"], "nombre_sugerido": "python, django"},
    1: {"n_ofertas": 12, "tecnologias_top": ["react", "javascript"], "nombre_sugerido": "react, javascript"},
    2: {"n_ofertas": 8,  "tecnologias_top": ["aws", "docker"], "nombre_sugerido": "aws, docker"},
}
```

### 5.3. RandomForest Regression (técnica secundaria)

**Proceso:**
1. Filtrar ofertas con datos salariales
2. Calcular salario promedio por oferta (min+max)/2
3. Crear features: tecnologías (one-hot) + ubicación (dummy encoding)
4. Dividir en entrenamiento (80%) y prueba (20%)
5. Entrenar RandomForestRegressor
6. Predecir sobre datos de prueba
7. Calcular métricas: MAE (error promedio) y R² (precisión)

**¿Cuándo se ejecuta?** Solo si hay 20+ ofertas con información salarial.

**Métricas:**
- **MAE (Mean Absolute Error):** "En promedio, el modelo se equivoca por $X". Ejemplo: MAE = $500 significa que predice salarios con un error promedio de $500.
- **R² (R-squared):** "Qué tan bien explica el modelo la variación de los datos". 0 = no explica nada, 1 = explica todo.

---

## 6. Dashboard interactivo

### 6.1. Tecnología

- **Streamlit**: Framework que convierte scripts de Python en apps web
- **Plotly**: Gráficas interactivas
- **Pandas**: Manipulación de datos

### 6.2. Componentes del dashboard

#### Sidebar (panel izquierdo) — Filtros
- **Fuente de datos**: checkboxes para seleccionar fuentes
- **Tecnología**: multiselect de tecnologías disponibles
- **Ubicación**: multiselect de ubicaciones
- **Salario máximo**: slider para filtrar por rango salarial

Los filtros se aplican en cascada y todas las gráficas se actualizan automáticamente.

#### Métricas (indicadores principales)
| Métrica | Descripción |
|---------|-------------|
| Total Ofertas | Número de ofertas filtradas |
| Fuentes | Cuántas fuentes diferentes aportaron datos |
| Tecnologías únicas | Cuántas tecnologías distintas se detectaron |
| Salario prom. | Salario mínimo promedio en USD |

#### Gráfica 1: Top Tecnologías Demandadas
Gráfico de barras horizontales con las 20 tecnologías más mencionadas.

**Utilidad:** Responde "¿qué debería aprender para conseguir trabajo en Panamá?"

#### Gráfica 2: Distribución de Salarios
Histograma de salarios promedio, coloreado por fuente de datos.

**Utilidad:** Responde "¿cuánto se paga y qué fuente tiene mejores salarios?"

#### Gráfica 3: Ofertas por Fuente
Gráfico de pastel mostrando qué proporción de ofertas viene de cada fuente.

**Utilidad:** Evidencia el carácter multi-fuente del proyecto.

#### Gráfica 4: Clusters de Perfiles Tecnológicos
Scatter plot 2D usando PCA para reducir las tecnologías a 2 dimensiones, coloreado por cluster de K-Means.

**Utilidad:** Visualiza cómo K-Means agrupó las ofertas por perfil tecnológico.

#### Gráfica 5: Tendencia de Publicaciones
Gráfico de líneas mostrando ofertas por mes, separado por fuente.

**Utilidad:** Muestra la evolución temporal del mercado laboral.

#### Tabla de datos
Tabla filtrable con columnas: título, empresa, ubicación, fuente, salarios y fecha.

---

## 7. Estructura del código

### 7.1. Árbol completo (archivo por archivo)

```
mercado-it-panama/
│
├── run_pipeline.py                  ← ORQUESTADOR: ejecuta todo de principio a fin
├── requirements.txt                 ← Dependencias para pip install
├── .gitignore                       ← Archivos que git debe ignorar
├── README.md                        ← Documentación general
├── INICIO_RAPIDO.md                 ← Guía rápida en español
│
├── data/                            ← Datos (raw y processed están en .gitignore)
│   ├── raw/                         ← Datos crudos por fuente
│   │   └── .gitkeep                 ← Para mantener la carpeta en git
│   └── processed/                   ← Dataset unificado generado
│       └── .gitkeep
│
├── src/                             ← Código fuente principal
│   ├── __init__.py                  ← Marca src como paquete Python
│   ├── config.py                    ← Configuración global
│   │
│   ├── ingesta/                     ← CAPA DE EXTRACCIÓN
│   │   ├── __init__.py
│   │   ├── api_remotive.py          ← API Remotive
│   │   ├── scraper_computrabajo.py  ← Scraper Computrabajo
│   │   ├── scraper_konzerta.py      ← Scraper Konzerta (Playwright)
│   │   └── loader_dataset.py        ← Cargador CSV flexible
│   │
│   ├── procesamiento/               ← CAPA DE TRANSFORMACIÓN
│   │   ├── __init__.py
│   │   ├── limpieza.py              ← Normalización, parseo de salarios
│   │   ├── extraccion_tecnologias.py ← Matching de tecnologías (sin LLM)
│   │   └── transformacion.py        ← Unificación al esquema común
│   │
│   └── ml/                          ← CAPA DE MACHINE LEARNING
│       ├── __init__.py
│       └── analisis.py              ← K-Means + RandomForest
│
├── dashboard/                       ← CAPA DE VISUALIZACIÓN
│   ├── __init__.py
│   └── app.py                       ← Streamlit dashboard
│
└── tests/                           ← PRUEBAS UNITARIAS
    ├── __init__.py
    ├── test_api_remotive.py         ← 2 tests
    ├── test_scraper.py              ← 3 tests (Computrabajo)
    ├── test_loader_dataset.py       ← 3 tests
    ├── test_procesamiento.py        ← 14 tests
    └── test_ml.py                   ← 5 tests
    TOTAL: 27 tests
```

### 7.2. Descripción de cada archivo clave

| Archivo | Líneas | ¿Qué hace? |
|---------|--------|------------|
| `config.py` | 73 | Define rutas de archivos y el diccionario maestro de 45 tecnologías con sus variantes regex |
| `api_remotive.py` | 51 | GET request a API Remotive, guarda JSON, maneja errores |
| `scraper_konzerta.py` | 200 | Playwright scraping de Konzerta con selectores reales y JS injection |
| `scraper_computrabajo.py` | 133 | Requests+BS4 scraping de Computrabajo con múltiples selectores de respaldo |
| `loader_dataset.py` | 64 | Carga CSV con mapeo flexible de columnas |
| `limpieza.py` | 74 | Limpieza de texto, parseo de salarios, eliminación de duplicados |
| `extraccion_tecnologias.py` | 66 | Pre-compila patrones regex y busca tecnologías en texto |
| `transformacion.py` | 185 | Mapea cada fuente al esquema común y unifica todo en un CSV |
| `analisis.py` | 148 | K-Means clustering + RandomForest regression |
| `app.py` | 182 | Dashboard interactivo con 6 visualizaciones y filtros |
| `run_pipeline.py` | 67 | Orquestador que ejecuta todo en orden |

---

## 8. Cómo ejecutar el proyecto

### 8.1. Prerrequisitos

- **Python 3.10+** — verificar con `python --version`
- **Git** — verificar con `git --version`
- **Conexión a internet** — para scrapear y usar la API

### 8.2. Instalación paso a paso

```bash
# 1. Clonar el repositorio
git clone https://github.com/Gabriel1Garci/Topicos.git
cd Topicos/mercado-it-panama

# 2. Crear entorno virtual (aisla las dependencias del proyecto)
python -m venv venv

# 3. Activar el entorno virtual
source venv/bin/activate          # Linux/Mac
# .\venv\Scripts\activate         # Windows PowerShell

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. (Opcional) Instalar Playwright para scraper Konzerta
playwright install chromium
```

### 8.3. Ejecutar el pipeline

```bash
python run_pipeline.py
```

**Salida esperada:**
```
============================================================
  PIPELINE: Mercado Laboral IT en Panamá
============================================================

[1/4] Scrapeando Konzerta Panama (5 páginas)...
      OK Konzerta: <cantidad de ofertas>

[2/4] Scrapeando Computrabajo Panama...
      OK Computrabajo: 0 ofertas (usa JS)
      (Nota: Computrabajo usa JS — pipeline continua con otras fuentes)

[3/4] Procesamiento, transformacion y ML...
      OK Dataset unificado: <cantidad de ofertas>
      OK Fuentes: <conteo por fuente disponible>
      OK Clusters encontrados: <cantidad de clusters>

[4/4] Generando modelo estrella para Power BI...
      OK <cantidad de tablas> tablas escritas en <ruta de salida>

============================================================
  Pipeline completado con exito.
  Dataset: data/processed/ofertas.csv
  Dashboard: streamlit run dashboard/app.py
============================================================
```

### 8.4. Iniciar el dashboard

```bash
streamlit run dashboard/app.py
```

Abrir en el navegador: **http://localhost:8501**

---

## 9. Pruebas (tests)

### 9.1. ¿Por qué son importantes?

Los tests verifican que el código funciona correctamente. Si alguien modifica algo, los tests detectan si algo se rompió.

### 9.2. Ejecutar tests

```bash
pytest tests/ -v
```

### 9.3. Cobertura de tests

| Archivo | Tests | ¿Qué cubren? |
|---------|-------|--------------|
| `test_api_remotive.py` | 2 | La API devuelve lista; falla graceful |
| `test_scraper.py` | 3 | Scraper devuelve lista; fallo graceful; HTTP 403 |
| `test_loader_dataset.py` | 3 | Carga CSV; archivo inexistente; mapeo de columnas |
| `test_procesamiento.py` | 14 | Limpieza (6) + Extracción de tecnologías (6) + Duplicados (1) |
| `test_ml.py` | 5 | Features; K-Means; resumen clusters; regresión; análisis completo |
| **Total** | **27** | Pipeline completo |

### 9.4. Ejemplo de un test

```python
def test_parsear_salario_rango():
    sal_min, sal_max = parsear_salario("B/. 1,500 - 2,000")
    assert sal_min == 1500.0
    assert sal_max == 2000.0
```

Este test verifica que la función `parsear_salario` convierte correctamente el string panameño "B/. 1,500 - 2,000" a los números 1500.0 y 2000.0.

---

## 10. Posibles mejoras y trabajo futuro

### 10.1. Corto plazo

1. **Crear dataset de ejemplo** (`ejemplo_kaggle.csv`) con 20 filas realistas para pruebas sin conexión
2. **Agregar Remotive al pipeline** (actualmente el orquestador omite esta fuente)
3. **Notebook de exploración** Jupyter para análisis ad-hoc

### 10.2. Mediano plazo

4. **Integrar más fuentes** panameñas (LinkedIn Jobs, Encuentra24, actualizacionvirtual.com)
5. **Scraping programado** con schedule para mantener datos frescos (ej. semanal)
6. **Exportar a Parquet** además de CSV (más eficiente para datasets grandes)

### 10.3. Largo plazo (fase siguiente del curso)

7. **LLM para extracción semántica** de habilidades (cuando el profesor lo autorice)
8. **Chatbot** que responda preguntas sobre el dataset en lenguaje natural
9. **Modelo predictivo** de tendencias (qué tecnologías crecerán en 6 meses)
10. **Despliegue web** del dashboard en la nube (Streamlit Community Cloud, Railway, etc.)

---

## 11. Glosario de términos

| Término | Definición |
|---------|------------|
| **API** | Interfaz que permite que programas se comuniquen entre sí |
| **BeautifulSoup4** | Librería Python para parsear HTML/XML |
| **Clustering** | Técnica ML que agrupa datos similares sin etiquetas previas |
| **Dashboard** | Panel visual con indicadores y gráficas |
| **DataFrame** | Estructura de datos 2D (filas y columnas) similar a hoja de cálculo |
| **Dataset** | Conjunto de datos estructurados |
| **Degradación elegante** | El sistema sigue funcionando aunque un componente falle |
| **Dummy encoding** | Convertir categorías (ej. ubicaciones) en columnas 0/1 |
| **ETL** | Extract, Transform, Load — proceso de mover y transformar datos |
| **Headless browser** | Navegador sin interfaz gráfica (se ejecuta en segundo plano) |
| **Inercia (K-Means)** | Suma de distancias al cuadrado de cada punto a su centroide |
| **K-Means** | Algoritmo de clustering que divide datos en K grupos |
| **MAE** | Mean Absolute Error — promedio del error absoluto de predicción |
| **Método del codo** | Técnica visual para elegir K óptimo en K-Means |
| **MultiLabelBinarizer** | Transforma listas de etiquetas en matriz one-hot |
| **One-Hot Encoding** | Convertir categorías en columnas binarias (0/1) |
| **Orquestador** | Script que coordina la ejecución de múltiples pasos |
| **PCA** | Principal Component Analysis — reduce dimensionalidad de datos |
| **Playwright** | Librería que controla navegadores (Chrome, Firefox) |
| **Plotly** | Librería Python para gráficas interactivas |
| **R²** | R-squared — métrica que indica qué tan bien se ajusta un modelo |
| **RandomForest** | Algoritmo ML que combina múltiples árboles de decisión |
| **Regresión** | Técnica ML que predice valores numéricos |
| **Regex** | Expresiones regulares — patrones para búsqueda en texto |
| **Scikit-learn** | Librería Python de Machine Learning |
| **Scraping** | Extracción automatizada de datos de sitios web |
| **SPA** | Single Page Application — web que carga contenido con JS |
| **Streamlit** | Framework Python para crear dashboards web |
| **User-Agent** | String que identifica el navegador/cliente HTTP |
| **Word boundary (\b)** | En regex, marca el límite entre una palabra y un no-carácter |
| **venv** | Entorno virtual de Python que aísla dependencias |

---

> **Nota final:** Este proyecto es un ejemplo clásico de **Gestión de la Información** aplicada: tomar datos heterogéneos (HTML, JSON, CSV) de fuentes diversas (scraping, API, archivos), procesarlos de forma estructurada (limpieza, normalización, enriquecimiento), aplicar análisis avanzado (ML) y presentar resultados accionables (dashboard). Es el ciclo completo de dato → información → conocimiento → decisión.
