# Análisis del Mercado Laboral IT en Panamá

**Proyecto Integrador — Segundo Parcial**  
Gestión de la Información · UTP-FISC · **Grupo 4**

Sistema de análisis del mercado laboral de tecnología en Panamá: ingestión de datos desde múltiples fuentes heterogéneas, procesamiento con extracción de tecnologías, clustering ML y dashboard interactivo.

---

## Problemática

¿Cuáles son las tecnologías más demandadas en el mercado IT panameño? ¿Qué perfiles tecnológicos existen y qué salarios ofrecen? Este proyecto responde esas preguntas construyendo un pipeline de datos automatizado con tres fuentes diferentes.

---

## Arquitectura del pipeline

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
  │  3. TRANSFORMACIÓN → esquema común + extracción techs     │
  │     (matching de diccionario con regex — sin LLMs)        │
  ├──────────────────────────────────────────────────────────┤
  │  4. DATASET UNIFICADO → data/processed/ofertas.csv        │
  └──────────────────────────────────────────────────────────┘
         │                                              │
         ▼                                              ▼
   K-Means Clustering                          Dashboard Streamlit
   + Regresión RF                              (filtros + gráficas)
```

---

## Fuentes de datos

| Fuente | Tipo | Relevancia |
|---|---|---|
| **Computrabajo Panamá** | Web Scraping | Ofertas locales de TI en Panamá. Si el sitio usa JavaScript, el pipeline continúa con las otras fuentes. |
| **Remotive API** | REST API pública | Empleos remotos tech. Relevantes porque un desarrollador panameño puede aplicar a trabajos remotos internacionales. |
| **Dataset Kaggle** | CSV descargado | Base de volumen con salarios y skills del sector tech. Incluye dataset de ejemplo (20 filas) para correr sin descarga adicional. |

---

## Técnicas de Machine Learning

### K-Means Clustering (principal)
Agrupa las ofertas por perfil tecnológico usando codificación one-hot de las tecnologías detectadas. El número óptimo de clusters se selecciona automáticamente con el método del codo. Descubre "familias" de puestos: frontend, backend, data, devops, etc.

### Regresión RandomForest (secundaria)
Predice el salario promedio en función de las tecnologías y ubicación. Se ejecuta automáticamente si hay 20 o más ofertas con información salarial. Métricas reportadas: MAE y R².

> **Nota:** La extracción de habilidades usa **matching de diccionario con regex** (`src/procesamiento/extraccion_tecnologias.py`), no LLMs. Requisito del curso.

---

## Requisitos previos

- Python 3.10 o superior
- Windows 10/11
- Git
- Conexión a internet (para Remotive API)

---

## Instalación

```powershell
git clone <url-del-repositorio>
cd mercado-it-panama
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

---

## Dataset de Kaggle (opcional, para más volumen)

El proyecto incluye un dataset de ejemplo con 20 filas en `data/raw/ejemplo_kaggle.csv`. Para más datos:

1. Descargar un dataset de empleos IT desde [Kaggle](https://www.kaggle.com/search?q=tech+job+salaries)  
   Recomendado: *Data Science Job Salaries* o *LinkedIn Tech Jobs*
2. Colocar el CSV en `data/raw/`
3. Editar `src/config.py` → cambiar `KAGGLE_EJEMPLO` a la nueva ruta

El loader detecta automáticamente las columnas relevantes.

---

## Cómo ejecutar

```powershell
# 1. Activar entorno virtual
.\venv\Scripts\activate

# 2. Correr el pipeline completo (ingesta + procesamiento + ML)
python run_pipeline.py

# 3. Abrir el dashboard interactivo
streamlit run dashboard/app.py
```

Abrir `http://localhost:8501` en el navegador.

### Power BI
Tras `python run_pipeline.py`, los CSV del modelo estrella quedan en `data/powerbi/`.
Ver `docs/GUIA_POWERBI.md` para importarlos y crear las relaciones.

### Asistente IA (Ollama)
1. Instala [Ollama](https://ollama.com) y ejecútalo: `ollama serve`
2. Descarga el modelo: `ollama pull llama3.2:3b`
3. Abre el dashboard y ve a la pestaña "🤖 Asistente IA".
Si Ollama no está corriendo, el resto del proyecto funciona igual.

---

## Estructura del proyecto

```
mercado-it-panama/
├── data/
│   ├── raw/                          # Datos crudos por fuente (gitignored)
│   │   └── ejemplo_kaggle.csv        # Dataset de ejemplo incluido
│   └── processed/
│       └── ofertas.csv               # Dataset unificado generado por el pipeline
├── src/
│   ├── config.py                     # Rutas y diccionario maestro de tecnologías (45 techs)
│   ├── ingesta/
│   │   ├── api_remotive.py           # API REST Remotive
│   │   ├── loader_dataset.py         # Loader CSV flexible
│   │   └── scraper_computrabajo.py   # Scraper web con degradación elegante
│   ├── procesamiento/
│   │   ├── limpieza.py               # Normalización, parseo de salarios
│   │   ├── extraccion_tecnologias.py # Matching regex (sin LLMs)
│   │   └── transformacion.py         # Esquema común + dataset unificado
│   └── ml/
│       └── analisis.py               # K-Means + regresión RandomForest
├── dashboard/
│   └── app.py                        # Dashboard Streamlit + Plotly
├── tests/                            # 27 tests (pytest)
├── run_pipeline.py                   # Orquestador de punta a punta
├── requirements.txt
└── .gitignore
```

---

## Nota sobre el scraping

El scraper de Computrabajo puede devolver 0 resultados si el sitio renderiza contenido con JavaScript. El pipeline **degrada con elegancia**: si esta fuente falla, continúa con Remotive y Kaggle, que son estables. El proyecto es completamente funcional con solo esas dos fuentes.

---

## Limitaciones y trabajo futuro

- **LLM (Ollama local):** consultas en lenguaje natural, resúmenes, extracción de skills y análisis de skills emergentes. Ver pestaña "Asistente IA" del dashboard.
- **Cobertura geográfica:** Se puede ampliar a otras bolsas de trabajo de Panamá.
- **Actualización automática:** Se puede agregar scheduling para re-ejecutar el pipeline periódicamente y mantener los datos frescos.
- **Fuente Computrabajo:** Requiere Playwright/Selenium para sitios con JavaScript — identificado como mejora para la siguiente fase.
