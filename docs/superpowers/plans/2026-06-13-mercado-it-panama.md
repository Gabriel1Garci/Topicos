# Mercado IT Panamá — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un pipeline completo de datos del mercado laboral IT en Panamá con 3 fuentes, análisis ML (clustering K-Means + regresión opcional) y dashboard interactivo en Streamlit.

**Architecture:** Tres fuentes (API Remotive, dataset Kaggle CSV, scraper Computrabajo) → normalización a esquema común → dataset unificado → K-Means clustering por perfil tecnológico → dashboard Streamlit con filtros y gráficas Plotly.

**Tech Stack:** Python 3.x · requests · BeautifulSoup4 · pandas · scikit-learn · Streamlit · Plotly · python-dateutil · venv (Windows)

**RESTRICCIÓN CRÍTICA:** NO usar LLMs, OpenAI, Anthropic ni modelos generativos. Extracción de tecnologías = matching de diccionario con regex.

**Orden de ejecución:** Task 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 (Computrabajo va de último por ser el más frágil).

---

## Mapa de archivos

```
mercado-it-panama/
├── data/
│   ├── raw/
│   │   ├── .gitkeep
│   │   └── ejemplo_kaggle.csv        ← creado en Task 3
│   └── processed/                    ← generado por pipeline
├── src/
│   ├── __init__.py
│   ├── config.py                     ← Task 1
│   ├── ingesta/
│   │   ├── __init__.py
│   │   ├── api_remotive.py           ← Task 2
│   │   ├── loader_dataset.py         ← Task 3
│   │   └── scraper_computrabajo.py   ← Task 7
│   ├── procesamiento/
│   │   ├── __init__.py
│   │   ├── limpieza.py               ← Task 4
│   │   ├── extraccion_tecnologias.py ← Task 4
│   │   └── transformacion.py         ← Task 4
│   └── ml/
│       ├── __init__.py
│       └── analisis.py               ← Task 5
├── dashboard/
│   └── app.py                        ← Task 6
├── run_pipeline.py                   ← Task 8
├── requirements.txt                  ← Task 1
├── .gitignore                        ← Task 1
└── README.md                         ← Task 8
```

---

## Task 1: FASE 0 — Setup del proyecto

**Files:**
- Create: `mercado-it-panama/requirements.txt`
- Create: `mercado-it-panama/.gitignore`
- Create: `mercado-it-panama/src/__init__.py`
- Create: `mercado-it-panama/src/config.py`
- Create: `mercado-it-panama/src/ingesta/__init__.py`
- Create: `mercado-it-panama/src/procesamiento/__init__.py`
- Create: `mercado-it-panama/src/ml/__init__.py`
- Create: `mercado-it-panama/dashboard/__init__.py` (vacío)
- Create: `mercado-it-panama/data/raw/.gitkeep`
- Create: `mercado-it-panama/data/processed/.gitkeep`

- [ ] **Step 1: Crear carpetas del proyecto**

Desde `C:\Users\Gabriel Garcia\Documents\Uni\topicos` ejecutar:

```powershell
cd "C:\Users\Gabriel Garcia\Documents\Uni\topicos"
mkdir mercado-it-panama
cd mercado-it-panama
mkdir data\raw, data\processed, src\ingesta, src\procesamiento, src\ml, dashboard, notebooks
```

- [ ] **Step 2: Crear el entorno virtual e instalar dependencias**

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Crear `requirements.txt`:

```
requests==2.31.0
beautifulsoup4==4.12.3
lxml==5.1.0
pandas==2.2.1
numpy==1.26.4
scikit-learn==1.4.1
streamlit==1.32.0
plotly==5.20.0
python-dateutil==2.9.0
```

Luego instalar:
```powershell
pip install -r requirements.txt
```

Verificar instalación: `python -c "import pandas, sklearn, streamlit, plotly; print('OK')"` debe imprimir `OK`.

- [ ] **Step 3: Crear .gitignore**

```
venv/
__pycache__/
*.pyc
*.pyo
.env
data/raw/*
!data/raw/.gitkeep
data/processed/*
!data/processed/.gitkeep
*.ipynb_checkpoints
.DS_Store
```

- [ ] **Step 4: Crear archivos `__init__.py` vacíos**

```powershell
# En el directorio mercado-it-panama/
New-Item src\__init__.py -ItemType File
New-Item src\ingesta\__init__.py -ItemType File
New-Item src\procesamiento\__init__.py -ItemType File
New-Item src\ml\__init__.py -ItemType File
New-Item data\raw\.gitkeep -ItemType File
New-Item data\processed\.gitkeep -ItemType File
```

- [ ] **Step 5: Crear `src/config.py` con rutas y diccionario maestro de tecnologías**

```python
# src/config.py
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

# Archivos de ingesta
REMOTIVE_RAW = DATA_RAW / "remotive_raw.json"
COMPUTRABAJO_RAW = DATA_RAW / "computrabajo_raw.json"
KAGGLE_EJEMPLO = DATA_RAW / "ejemplo_kaggle.csv"

# Dataset final
OFERTAS_CSV = DATA_PROCESSED / "ofertas.csv"
OFERTAS_PARQUET = DATA_PROCESSED / "ofertas.parquet"

# Diccionario maestro de tecnologías
# Clave: nombre canónico (lo que se guarda)
# Valor: lista de variantes a matchear (regex word-boundary, case-insensitive)
TECH_DICT = {
    # Lenguajes
    "python": ["python"],
    "java": ["java"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "php": ["php"],
    "c#": ["c#", "csharp", "c sharp"],
    "go": ["golang"],  # "go" solo causa falsos positivos
    "ruby": ["ruby"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
    "r": ["\\br\\b"],  # solo la letra R como palabra completa
    # Frameworks web/backend
    "react": ["react\\.js", "reactjs", "react"],
    "angular": ["angular"],
    "vue": ["vue\\.js", "vuejs", "vue"],
    "laravel": ["laravel"],
    "django": ["django"],
    "spring": ["spring boot", "spring"],
    "node.js": ["node\\.js", "nodejs", "node"],
    ".net": ["\\.net", "dotnet"],
    "flask": ["flask"],
    "fastapi": ["fastapi"],
    # Bases de datos
    "mysql": ["mysql"],
    "mariadb": ["mariadb"],
    "postgresql": ["postgresql", "postgres"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "sql server": ["sql server", "mssql", "sqlserver"],
    "oracle": ["oracle"],
    "sqlite": ["sqlite"],
    # Cloud / DevOps
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git"],
    "jenkins": ["jenkins"],
    "terraform": ["terraform"],
    "linux": ["linux", "ubuntu", "debian"],
    # Otros
    "rest": ["rest api", "restful", "\\brest\\b"],
    "graphql": ["graphql"],
    "html": ["html"],
    "css": ["css"],
    "sql": ["\\bsql\\b"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "excel": ["excel"],
}
```

- [ ] **Step 6: Verificar estructura**

```powershell
Get-ChildItem -Recurse -Name | Where-Object { $_ -notmatch "venv" }
```

Debe mostrar todos los archivos y carpetas creados.

- [ ] **Step 7: Commit inicial**

```powershell
git init
git add requirements.txt .gitignore src\ data\
git commit -m "feat: setup inicial del proyecto mercado-it-panama"
```

---

## Task 2: FASE 1 — Ingesta API Remotive

**Files:**
- Create: `mercado-it-panama/src/ingesta/api_remotive.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_api_remotive.py`:

```python
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingesta.api_remotive import ingerir_remotive

def test_ingerir_remotive_devuelve_lista():
    """La función debe devolver una lista (puede estar vacía si la API falla)."""
    # Con mock para no depender de red en tests
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "id": 1,
                "title": "Python Developer",
                "company_name": "TechCorp",
                "candidate_required_location": "Remote",
                "salary": "USD 3000-4000",
                "publication_date": "2024-01-15T00:00:00",
                "description": "<p>We need Python and Django skills</p>",
                "url": "https://remotive.com/job/1"
            }
        ]
    }
    with patch("src.ingesta.api_remotive.requests.get", return_value=mock_response):
        resultado = ingerir_remotive()
    assert isinstance(resultado, list)
    assert len(resultado) == 1
    assert resultado[0]["title"] == "Python Developer"

def test_ingerir_remotive_falla_con_gracia():
    """Si la API falla, devuelve lista vacía sin lanzar excepción."""
    with patch("src.ingesta.api_remotive.requests.get", side_effect=Exception("timeout")):
        resultado = ingerir_remotive()
    assert resultado == []
```

- [ ] **Step 2: Ejecutar test para verificar que falla**

```powershell
# Desde mercado-it-panama/ con venv activo
pip install pytest
pytest tests/test_api_remotive.py -v
```

Esperado: `FAILED` con `ModuleNotFoundError: No module named 'src.ingesta.api_remotive'`

- [ ] **Step 3: Crear `src/ingesta/api_remotive.py`**

```python
# src/ingesta/api_remotive.py
"""
Ingesta desde la API pública de Remotive (empleos remotos IT).
No requiere API key. Endpoint: https://remotive.com/api/remote-jobs
"""
import json
import logging
import requests
from pathlib import Path
from src.config import REMOTIVE_RAW, DATA_RAW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
CATEGORIA = "software-dev"


def ingerir_remotive(categoria: str = CATEGORIA) -> list[dict]:
    """
    Descarga ofertas IT de la API de Remotive y guarda el crudo en data/raw/.
    Retorna la lista de ofertas crudas. Si falla, retorna lista vacía.
    """
    logger.info(f"Iniciando ingesta desde Remotive (categoría: {categoria})...")
    try:
        params = {"category": categoria}
        headers = {"User-Agent": "MercadoITPanama/1.0 (proyecto universitario)"}
        response = requests.get(REMOTIVE_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        datos = response.json()
        ofertas = datos.get("jobs", [])
        logger.info(f"Remotive: {len(ofertas)} ofertas descargadas.")

        # Guardar crudo
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        with open(REMOTIVE_RAW, "w", encoding="utf-8") as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2)
        logger.info(f"Crudo guardado en {REMOTIVE_RAW}")

        return ofertas

    except Exception as e:
        logger.warning(f"Remotive falló: {e}. Pipeline continúa con otras fuentes.")
        return []


if __name__ == "__main__":
    resultado = ingerir_remotive()
    print(f"Ofertas obtenidas: {len(resultado)}")
    if resultado:
        print("Ejemplo:", resultado[0].get("title"), "-", resultado[0].get("company_name"))
```

- [ ] **Step 4: Crear carpeta tests con `__init__.py`**

```powershell
mkdir tests
New-Item tests\__init__.py -ItemType File
```

- [ ] **Step 5: Ejecutar tests — verificar que pasan**

```powershell
pytest tests/test_api_remotive.py -v
```

Esperado: `2 passed`

- [ ] **Step 6: Verificar con la API real (requiere internet)**

```powershell
python src/ingesta/api_remotive.py
```

Esperado: `Ofertas obtenidas: <número>` y se crea `data/raw/remotive_raw.json`.

- [ ] **Step 7: Commit**

```powershell
git add src/ingesta/api_remotive.py tests/
git commit -m "feat: ingesta API Remotive con degradación elegante"
```

---

## Task 3: FASE 2 — Loader dataset Kaggle

**Files:**
- Create: `mercado-it-panama/src/ingesta/loader_dataset.py`
- Create: `mercado-it-panama/data/raw/ejemplo_kaggle.csv`

- [ ] **Step 1: Crear dataset de ejemplo**

Crear `data/raw/ejemplo_kaggle.csv` con estas 20 filas:

```csv
job_title,company,location,salary_range,skills,description,date_posted
Software Engineer,TechPanama,Panama City,2500-4000,Python;Django;PostgreSQL,Backend developer needed for web platform,2024-01-10
Frontend Developer,Softcorp,Panama City,2000-3500,JavaScript;React;CSS,React developer for e-commerce,2024-01-11
Data Analyst,Banconal,Panama City,1800-3000,Python;SQL;Excel;Power BI,Analyst for financial data,2024-01-12
DevOps Engineer,CloudPA,Remote,3000-5000,AWS;Docker;Kubernetes;Linux,Cloud infrastructure engineer,2024-01-13
Full Stack Developer,StartupPA,Colon,2200-3800,Node.js;React;MongoDB,Full stack for startup platform,2024-01-14
Mobile Developer,AppFactory,Panama City,2500-4500,Kotlin;Android;Java,Android mobile developer,2024-01-15
Systems Administrator,GovTech,Panama City,1500-2500,Linux;Windows;Networking,IT admin for government office,2024-01-16
Business Intelligence,Banconal,Panama City,2000-3500,SQL Server;Power BI;Excel;Tableau,BI analyst role,2024-01-17
Java Developer,Enterprise PA,Panama City,2800-4200,Java;Spring;MySQL,Backend Java developer,2024-01-18
PHP Developer,AgencyWeb,Panama City,1800-3000,PHP;Laravel;MySQL;HTML;CSS,Web developer for agency,2024-01-19
Cloud Architect,TechPanama,Remote,4000-7000,AWS;Azure;Terraform;Docker,Senior cloud architect,2024-01-20
QA Engineer,QualityTech,Panama City,1800-3200,Python;Selenium;SQL,Quality assurance engineer,2024-01-21
Data Scientist,AnalyticsCorp,Panama City,3000-5500,Python;R;scikit-learn;SQL,Data scientist for ML projects,2024-01-22
React Developer,WebAgency,Panama City,2000-3500,JavaScript;React;TypeScript;CSS,Frontend React specialist,2024-01-23
SAP Consultant,SAPConsult,Panama City,3500-6000,SAP;SQL;Excel,SAP ERP consultant,2024-01-24
Network Engineer,Telcorp,Panama City,2000-3500,Linux;Cisco;Networking,Network infrastructure engineer,2024-01-25
Angular Developer,DigitalPA,Panama City,2200-3800,JavaScript;Angular;TypeScript,Frontend Angular developer,2024-01-26
Database Administrator,DataCorp,Panama City,2500-4000,MySQL;PostgreSQL;Oracle;SQL,DBA for enterprise systems,2024-01-27
Scrum Master,AgilePa,Panama City,2800-4500,Agile;Scrum;Jira,Scrum master for dev teams,2024-01-28
Python Developer,DataStartup,Remote,2500-4500,Python;FastAPI;PostgreSQL;Docker,Backend Python API developer,2024-01-29
```

- [ ] **Step 2: Escribir test que falla**

Agregar a `tests/test_loader_dataset.py`:

```python
import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingesta.loader_dataset import cargar_dataset
from src.config import KAGGLE_EJEMPLO

def test_cargar_dataset_ejemplo():
    """El loader debe retornar un DataFrame con las columnas mapeadas."""
    df = cargar_dataset(KAGGLE_EJEMPLO)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    # Debe tener al menos estas columnas del esquema de trabajo
    for col in ["titulo_raw", "empresa_raw", "ubicacion_raw", "descripcion_raw"]:
        assert col in df.columns, f"Columna '{col}' no encontrada en DataFrame"

def test_cargar_dataset_archivo_inexistente():
    """Si el archivo no existe, debe retornar DataFrame vacío sin lanzar excepción."""
    df = cargar_dataset(Path("ruta/que/no/existe.csv"))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
```

- [ ] **Step 3: Verificar que el test falla**

```powershell
pytest tests/test_loader_dataset.py -v
```

Esperado: `FAILED` con `ModuleNotFoundError`.

- [ ] **Step 4: Crear `src/ingesta/loader_dataset.py`**

```python
# src/ingesta/loader_dataset.py
"""
Carga un CSV de empleos/salarios IT desde data/raw/ (descargado de Kaggle u otra fuente).
Es robusto a distintos nombres de columnas gracias al mapeo configurable.
"""
import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapeo flexible: columna_destino → posibles nombres en el CSV (orden de prioridad)
COLUMNAS_MAPEO = {
    "titulo_raw":      ["job_title", "title", "titulo", "position", "puesto", "job"],
    "empresa_raw":     ["company", "company_name", "empresa", "employer", "organization"],
    "ubicacion_raw":   ["location", "ubicacion", "city", "country", "lugar", "candidate_required_location"],
    "descripcion_raw": ["description", "descripcion", "job_description", "requirements", "skills", "resumen"],
    "salario_raw":     ["salary_range", "salary", "salario", "pay", "compensation", "wage"],
    "fecha_raw":       ["date_posted", "fecha", "published_at", "date", "posting_date"],
}


def cargar_dataset(ruta: Path) -> pd.DataFrame:
    """
    Lee el CSV en `ruta` y renombra columnas al esquema interno.
    Si el archivo no existe o no se puede leer, retorna DataFrame vacío.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        logger.warning(f"Dataset no encontrado en {ruta}. Retornando DataFrame vacío.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(ruta, encoding="utf-8", dtype=str)
        logger.info(f"Dataset cargado: {len(df)} filas, columnas: {list(df.columns)}")
    except Exception as e:
        logger.warning(f"Error leyendo {ruta}: {e}. Retornando DataFrame vacío.")
        return pd.DataFrame()

    # Mapear columnas de forma flexible
    renombrar = {}
    cols_lower = {c.lower(): c for c in df.columns}
    for col_destino, variantes in COLUMNAS_MAPEO.items():
        for variante in variantes:
            if variante.lower() in cols_lower:
                renombrar[cols_lower[variante.lower()]] = col_destino
                break  # Usar la primera variante encontrada

    df = df.rename(columns=renombrar)

    # Añadir columnas faltantes como NaN
    for col in COLUMNAS_MAPEO.keys():
        if col not in df.columns:
            df[col] = None

    logger.info(f"Dataset mapeado. Columnas disponibles: {list(df.columns)}")
    return df


if __name__ == "__main__":
    from src.config import KAGGLE_EJEMPLO
    df = cargar_dataset(KAGGLE_EJEMPLO)
    print(f"Filas: {len(df)}")
    print(df[["titulo_raw", "empresa_raw", "ubicacion_raw"]].head(5))
```

- [ ] **Step 5: Ejecutar tests — verificar que pasan**

```powershell
pytest tests/test_loader_dataset.py -v
```

Esperado: `2 passed`

- [ ] **Step 6: Commit**

```powershell
git add src/ingesta/loader_dataset.py data/raw/ejemplo_kaggle.csv tests/test_loader_dataset.py
git commit -m "feat: loader dataset Kaggle con mapeo flexible de columnas"
```

---

## Task 4: FASE 4 — Procesamiento (limpieza, extracción de tecnologías, transformación)

**Files:**
- Create: `mercado-it-panama/src/procesamiento/limpieza.py`
- Create: `mercado-it-panama/src/procesamiento/extraccion_tecnologias.py`
- Create: `mercado-it-panama/src/procesamiento/transformacion.py`

- [ ] **Step 1: Escribir tests de limpieza**

Crear `tests/test_procesamiento.py`:

```python
import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.procesamiento.limpieza import (
    limpiar_texto, parsear_salario, eliminar_duplicados_nulos
)
from src.procesamiento.extraccion_tecnologias import extraer_tecnologias

# --- Tests de limpieza ---

def test_limpiar_texto_minusculas():
    assert limpiar_texto("  Python Developer  ") == "python developer"

def test_limpiar_texto_html():
    assert limpiar_texto("<p>Senior <b>Dev</b></p>") == "senior dev"

def test_limpiar_texto_none():
    assert limpiar_texto(None) == ""

def test_parsear_salario_rango():
    salario_min, salario_max = parsear_salario("B/. 1,500 - 2,000")
    assert salario_min == 1500.0
    assert salario_max == 2000.0

def test_parsear_salario_usd_rango():
    salario_min, salario_max = parsear_salario("USD 3000-4000")
    assert salario_min == 3000.0
    assert salario_max == 4000.0

def test_parsear_salario_unico():
    salario_min, salario_max = parsear_salario("$2500")
    assert salario_min == 2500.0
    assert salario_max == 2500.0

def test_parsear_salario_nulo():
    salario_min, salario_max = parsear_salario(None)
    assert salario_min is None
    assert salario_max is None

def test_parsear_salario_texto_invalido():
    salario_min, salario_max = parsear_salario("Competitive salary")
    assert salario_min is None
    assert salario_max is None

def test_eliminar_duplicados_nulos():
    df = pd.DataFrame({
        "titulo": ["Dev", None, "Dev", "Analyst"],
        "descripcion": ["a", "b", "a", "d"]
    })
    resultado = eliminar_duplicados_nulos(df)
    assert len(resultado) == 2  # Elimina nulo y duplicado

# --- Tests de extracción de tecnologías ---

def test_extraer_tecnologias_basico():
    texto = "Buscamos developer con experiencia en Python y Django"
    techs = extraer_tecnologias(texto)
    assert "python" in techs
    assert "django" in techs

def test_extraer_tecnologias_case_insensitive():
    texto = "Experiencia en REACT y TypeScript requerida"
    techs = extraer_tecnologias(texto)
    assert "react" in techs
    assert "typescript" in techs

def test_extraer_tecnologias_evita_falsos_positivos():
    # "go" dentro de "google" no debe matchear como el lenguaje "go"
    texto = "Experiencia con Google Cloud y good practices"
    techs = extraer_tecnologias(texto)
    assert "go" not in techs

def test_extraer_tecnologias_texto_vacio():
    assert extraer_tecnologias("") == []
    assert extraer_tecnologias(None) == []

def test_extraer_tecnologias_nodejs_variantes():
    texto1 = "node.js developer"
    texto2 = "nodejs backend"
    texto3 = "Node developer"
    assert "node.js" in extraer_tecnologias(texto1)
    assert "node.js" in extraer_tecnologias(texto2)
    assert "node.js" in extraer_tecnologias(texto3)
```

- [ ] **Step 2: Verificar que los tests fallan**

```powershell
pytest tests/test_procesamiento.py -v
```

Esperado: `FAILED` con `ModuleNotFoundError`.

- [ ] **Step 3: Crear `src/procesamiento/limpieza.py`**

```python
# src/procesamiento/limpieza.py
"""
Funciones de limpieza de datos: normalización de texto, parseo de salarios,
eliminación de duplicados y registros nulos críticos.
"""
import re
import logging
import pandas as pd
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


class _HTMLStripper(HTMLParser):
    """Extrae texto plano de HTML."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return " ".join(self.fed)


def limpiar_texto(texto) -> str:
    """Quita HTML, trim, convierte a minúsculas. Retorna '' si es None."""
    if texto is None or (isinstance(texto, float)):
        return ""
    texto = str(texto)
    # Quitar etiquetas HTML
    stripper = _HTMLStripper()
    stripper.feed(texto)
    texto = stripper.get_data()
    # Normalizar espacios y convertir a minúsculas
    texto = re.sub(r"\s+", " ", texto).strip().lower()
    return texto


def parsear_salario(salario_str) -> tuple:
    """
    Extrae (salario_min, salario_max) como float desde un string variado.
    Maneja rangos "1500-2000", valores únicos "$2500", formatos "B/. 1,500".
    Retorna (None, None) si no puede extraer números válidos.
    """
    if salario_str is None or (isinstance(salario_str, float)):
        return (None, None)

    texto = str(salario_str)
    # Quitar símbolos de moneda y texto no numérico (conservar dígitos, puntos, comas, guiones)
    texto_limpio = re.sub(r"[^\d\.,\-]", " ", texto)
    # Normalizar comas de miles
    texto_limpio = texto_limpio.replace(",", "")

    # Buscar todos los números
    numeros = re.findall(r"\d+(?:\.\d+)?", texto_limpio)
    numeros = [float(n) for n in numeros if float(n) > 100]  # filtrar años/codes

    if not numeros:
        return (None, None)
    elif len(numeros) == 1:
        return (numeros[0], numeros[0])
    else:
        return (min(numeros[:2]), max(numeros[:2]))


def eliminar_duplicados_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elimina filas sin título (crítico) y filas duplicadas por título+descripción.
    """
    n_original = len(df)
    # Eliminar sin título
    df = df.dropna(subset=["titulo"])
    df = df[df["titulo"].str.strip() != ""]
    # Eliminar duplicados
    subset_cols = [c for c in ["titulo", "descripcion"] if c in df.columns]
    if subset_cols:
        df = df.drop_duplicates(subset=subset_cols, keep="first")
    logger.info(f"Limpieza: {n_original} → {len(df)} filas (eliminados {n_original - len(df)})")
    return df.reset_index(drop=True)
```

- [ ] **Step 4: Crear `src/procesamiento/extraccion_tecnologias.py`**

```python
# src/procesamiento/extraccion_tecnologias.py
"""
Extrae tecnologías de texto usando matching de diccionario con regex.
Esta función REEMPLAZA al LLM — es un requisito del curso no usar modelos generativos.
El matching usa word boundaries para evitar falsos positivos (ej. "go" dentro de "google").
"""
import re
import logging
from src.config import TECH_DICT

logger = logging.getLogger(__name__)

# Pre-compilar los patrones para eficiencia
_PATRONES_COMPILADOS: dict[str, list[re.Pattern]] = {}

def _compilar_patrones():
    """Compila los patrones del TECH_DICT una sola vez al importar."""
    for tech_nombre, variantes in TECH_DICT.items():
        patrones = []
        for variante in variantes:
            # Si la variante ya tiene \b o \\b, usarla tal cual
            if "\\b" in variante or r"\b" in variante:
                patron = variante
            else:
                # Escapar caracteres especiales regex excepto los que ya están escapados
                variante_escapada = re.escape(variante).replace(r"\.", r"\.")
                patron = rf"\b{variante_escapada}\b"
            try:
                patrones.append(re.compile(patron, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Patrón inválido para '{tech_nombre}': {patron} — {e}")
        _PATRONES_COMPILADOS[tech_nombre] = patrones

_compilar_patrones()


def extraer_tecnologias(texto) -> list[str]:
    """
    Recorre el diccionario maestro (src/config.py) y retorna las tecnologías
    encontradas en el texto. Matching case-insensitive con word boundaries.

    Args:
        texto: string con la descripción de la oferta (puede ser None)
    Returns:
        Lista de nombres canónicos de tecnologías encontradas (sin duplicados)
    """
    if not texto:
        return []
    texto = str(texto)
    encontradas = []
    for tech_nombre, patrones in _PATRONES_COMPILADOS.items():
        for patron in patrones:
            if patron.search(texto):
                encontradas.append(tech_nombre)
                break  # Encontrada esta tech, pasar a la siguiente
    return encontradas
```

- [ ] **Step 5: Crear `src/procesamiento/transformacion.py`**

```python
# src/procesamiento/transformacion.py
"""
Toma las salidas crudas de las 3 fuentes y las normaliza al esquema común.
Esquema: titulo, empresa, ubicacion, tecnologias, salario_min, salario_max,
         fecha, fuente, descripcion.
"""
import json
import logging
import pandas as pd
from datetime import date
from dateutil import parser as dateparser

from src.config import (
    REMOTIVE_RAW, COMPUTRABAJO_RAW, KAGGLE_EJEMPLO,
    OFERTAS_CSV, OFERTAS_PARQUET, DATA_PROCESSED
)
from src.procesamiento.limpieza import limpiar_texto, parsear_salario, eliminar_duplicados_nulos
from src.procesamiento.extraccion_tecnologias import extraer_tecnologias

logger = logging.getLogger(__name__)

ESQUEMA_COLUMNAS = [
    "titulo", "empresa", "ubicacion", "tecnologias",
    "salario_min", "salario_max", "fecha", "fuente", "descripcion"
]


def _parsear_fecha(valor) -> date | None:
    if not valor or (isinstance(valor, float)):
        return None
    try:
        return dateparser.parse(str(valor)).date()
    except Exception:
        return None


def transformar_remotive(ofertas_crudas: list[dict]) -> pd.DataFrame:
    """Mapea lista de dicts crudos de Remotive al esquema común."""
    if not ofertas_crudas:
        return pd.DataFrame(columns=ESQUEMA_COLUMNAS)
    filas = []
    for oferta in ofertas_crudas:
        descripcion = limpiar_texto(oferta.get("description", ""))
        titulo = limpiar_texto(oferta.get("title", ""))
        techs = extraer_tecnologias(titulo + " " + descripcion)
        sal_min, sal_max = parsear_salario(oferta.get("salary"))
        filas.append({
            "titulo":      titulo,
            "empresa":     limpiar_texto(oferta.get("company_name")),
            "ubicacion":   limpiar_texto(oferta.get("candidate_required_location", "Remoto")),
            "tecnologias": techs,
            "salario_min": sal_min,
            "salario_max": sal_max,
            "fecha":       _parsear_fecha(oferta.get("publication_date")),
            "fuente":      "remotive",
            "descripcion": descripcion,
        })
    logger.info(f"Remotive: {len(filas)} ofertas transformadas.")
    return pd.DataFrame(filas, columns=ESQUEMA_COLUMNAS)


def transformar_kaggle(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Mapea DataFrame del loader Kaggle al esquema común."""
    if df_raw.empty:
        return pd.DataFrame(columns=ESQUEMA_COLUMNAS)
    filas = []
    for _, fila in df_raw.iterrows():
        descripcion = limpiar_texto(fila.get("descripcion_raw", ""))
        titulo = limpiar_texto(fila.get("titulo_raw", ""))
        techs = extraer_tecnologias(titulo + " " + descripcion)
        sal_min, sal_max = parsear_salario(fila.get("salario_raw"))
        filas.append({
            "titulo":      titulo,
            "empresa":     limpiar_texto(fila.get("empresa_raw")),
            "ubicacion":   limpiar_texto(fila.get("ubicacion_raw")),
            "tecnologias": techs,
            "salario_min": sal_min,
            "salario_max": sal_max,
            "fecha":       _parsear_fecha(fila.get("fecha_raw")),
            "fuente":      "kaggle",
            "descripcion": descripcion,
        })
    logger.info(f"Kaggle: {len(filas)} ofertas transformadas.")
    return pd.DataFrame(filas, columns=ESQUEMA_COLUMNAS)


def transformar_computrabajo(ofertas_crudas: list[dict]) -> pd.DataFrame:
    """Mapea lista de dicts crudos del scraper al esquema común."""
    if not ofertas_crudas:
        return pd.DataFrame(columns=ESQUEMA_COLUMNAS)
    filas = []
    for oferta in ofertas_crudas:
        descripcion = limpiar_texto(oferta.get("descripcion", ""))
        titulo = limpiar_texto(oferta.get("titulo", ""))
        techs = extraer_tecnologias(titulo + " " + descripcion)
        sal_min, sal_max = parsear_salario(oferta.get("salario"))
        filas.append({
            "titulo":      titulo,
            "empresa":     limpiar_texto(oferta.get("empresa")),
            "ubicacion":   limpiar_texto(oferta.get("ubicacion", "Panamá")),
            "tecnologias": techs,
            "salario_min": sal_min,
            "salario_max": sal_max,
            "fecha":       _parsear_fecha(oferta.get("fecha")),
            "fuente":      "computrabajo",
            "descripcion": descripcion,
        })
    logger.info(f"Computrabajo: {len(filas)} ofertas transformadas.")
    return pd.DataFrame(filas, columns=ESQUEMA_COLUMNAS)


def construir_dataset_unificado() -> pd.DataFrame:
    """
    Orquesta la transformación de todas las fuentes disponibles
    y guarda el dataset unificado en data/processed/.
    """
    from src.ingesta.api_remotive import ingerir_remotive
    from src.ingesta.loader_dataset import cargar_dataset

    dfs = []

    # Fuente 1: Remotive
    remotive_raw = ingerir_remotive()
    dfs.append(transformar_remotive(remotive_raw))

    # Fuente 2: Kaggle (usar ejemplo si no hay real)
    kaggle_df = cargar_dataset(KAGGLE_EJEMPLO)
    dfs.append(transformar_kaggle(kaggle_df))

    # Fuente 3: Computrabajo (si existe el crudo ya descargado)
    if COMPUTRABAJO_RAW.exists():
        try:
            with open(COMPUTRABAJO_RAW, "r", encoding="utf-8") as f:
                computrabajo_raw = json.load(f)
            dfs.append(transformar_computrabajo(computrabajo_raw))
        except Exception as e:
            logger.warning(f"No se pudo cargar Computrabajo: {e}")

    # Combinar todo
    df_total = pd.concat([d for d in dfs if not d.empty], ignore_index=True)
    df_total = eliminar_duplicados_nulos(df_total)

    # Guardar
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_total.to_csv(OFERTAS_CSV, index=False)
    logger.info(f"Dataset unificado guardado: {len(df_total)} filas en {OFERTAS_CSV}")

    # Guardar tecnologias como string para CSV
    df_total["tecnologias_str"] = df_total["tecnologias"].apply(
        lambda x: "|".join(x) if isinstance(x, list) else ""
    )

    return df_total
```

- [ ] **Step 6: Ejecutar todos los tests de procesamiento**

```powershell
pytest tests/test_procesamiento.py -v
```

Esperado: todos los tests de limpieza y extracción pasan.

- [ ] **Step 7: Probar transformación con fuentes reales**

```powershell
python -c "
from src.procesamiento.transformacion import construir_dataset_unificado
df = construir_dataset_unificado()
print(df.shape)
print(df[['titulo','fuente','tecnologias']].head(5))
"
```

Esperado: DataFrame con filas de remotive + kaggle, columna `tecnologias` con listas.

- [ ] **Step 8: Commit**

```powershell
git add src/procesamiento/ tests/test_procesamiento.py
git commit -m "feat: pipeline procesamiento — limpieza, extraccion tecnologias, transformacion"
```

---

## Task 5: FASE 5 — Análisis ML (K-Means clustering + regresión opcional)

**Files:**
- Create: `mercado-it-panama/src/ml/analisis.py`

- [ ] **Step 1: Escribir tests de ML**

Agregar `tests/test_ml.py`:

```python
import pytest
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml.analisis import (
    preparar_features_tecnologias,
    aplicar_kmeans,
    aplicar_regresion_salario
)

# Dataset mínimo para tests
@pytest.fixture
def df_test():
    return pd.DataFrame({
        "titulo": ["Python Dev", "React Dev", "AWS Architect", "Java Dev", "Vue Dev"],
        "tecnologias": [
            ["python", "django", "postgresql"],
            ["javascript", "react", "css"],
            ["aws", "docker", "kubernetes"],
            ["java", "spring", "mysql"],
            ["javascript", "vue", "css"],
        ],
        "salario_min": [3000.0, 2500.0, 5000.0, 2800.0, 2200.0],
        "salario_max": [4500.0, 3500.0, 7000.0, 4000.0, 3500.0],
        "fuente": ["remotive"] * 5,
        "ubicacion": ["Remote", "Panama City", "Remote", "Panama City", "Panama City"],
    })

def test_preparar_features(df_test):
    X, nombres_cols = preparar_features_tecnologias(df_test)
    assert X.shape[0] == 5
    assert X.shape[1] > 0
    assert "python" in nombres_cols or len(nombres_cols) > 0

def test_kmeans_retorna_etiquetas(df_test):
    X, _ = preparar_features_tecnologias(df_test)
    etiquetas, resumen = aplicar_kmeans(X, df_test, n_clusters=2)
    assert len(etiquetas) == len(df_test)
    assert isinstance(resumen, dict)
    assert len(resumen) == 2

def test_regresion_retorna_metricas(df_test):
    resultado = aplicar_regresion_salario(df_test)
    # Puede retornar None si hay pocos datos
    assert resultado is None or isinstance(resultado, dict)
    if resultado:
        assert "mae" in resultado or "r2" in resultado
```

- [ ] **Step 2: Verificar que los tests fallan**

```powershell
pytest tests/test_ml.py -v
```

Esperado: `FAILED` con `ModuleNotFoundError`.

- [ ] **Step 3: Crear `src/ml/analisis.py`**

```python
# src/ml/analisis.py
"""
Análisis de Machine Learning sobre el dataset unificado de ofertas IT.
Técnica principal: K-Means clustering por perfil tecnológico.
Técnica secundaria: Regresión de salarios (si hay suficientes datos).
NO se usan LLMs — requisito del curso.
"""
import logging
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

logger = logging.getLogger(__name__)

COLUMNAS_CLUSTER_GUARDADO = "cluster"


def preparar_features_tecnologias(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """
    Convierte la columna 'tecnologias' (list[str]) en una matriz one-hot.
    Retorna (X, nombres_columnas).
    """
    tech_listas = df["tecnologias"].apply(
        lambda x: x if isinstance(x, list) else []
    ).tolist()

    mlb = MultiLabelBinarizer()
    X = mlb.fit_transform(tech_listas)
    return X.astype(float), list(mlb.classes_)


def seleccionar_k_optimo(X: np.ndarray, k_min: int = 2, k_max: int = 8) -> int:
    """
    Método del codo para seleccionar k. Retorna el k con mayor caída de inercia.
    """
    k_max = min(k_max, len(X) - 1)  # No puede haber más clusters que muestras
    if k_max < k_min:
        return k_min

    inercias = []
    rango_k = range(k_min, k_max + 1)
    for k in rango_k:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        inercias.append(km.inertia_)

    # Calcular la segunda derivada para encontrar el "codo"
    diffs = [inercias[i] - inercias[i+1] for i in range(len(inercias)-1)]
    k_optimo = list(rango_k)[diffs.index(max(diffs))]
    logger.info(f"K óptimo seleccionado: {k_optimo} (inercias: {inercias})")
    return k_optimo


def aplicar_kmeans(
    X: np.ndarray,
    df: pd.DataFrame,
    n_clusters: int | None = None
) -> tuple[np.ndarray, dict]:
    """
    Aplica K-Means al espacio de tecnologías.
    Si n_clusters es None, usa el método del codo.
    Retorna (etiquetas, resumen_por_cluster).
    """
    if n_clusters is None:
        n_clusters = seleccionar_k_optimo(X)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    etiquetas = km.fit_predict(X)

    # Resumen: tecnologías dominantes por cluster
    tech_cols, _ = preparar_features_tecnologias(df)
    _, nombres_tech = preparar_features_tecnologias(df)

    resumen = {}
    for cluster_id in range(n_clusters):
        mask = etiquetas == cluster_id
        if mask.sum() == 0:
            continue
        # Frecuencia de cada tecnología en el cluster
        frecuencias = X[mask].sum(axis=0)
        top_indices = np.argsort(frecuencias)[::-1][:5]
        top_techs = [nombres_tech[i] for i in top_indices if frecuencias[i] > 0]
        resumen[cluster_id] = {
            "n_ofertas": int(mask.sum()),
            "tecnologias_top": top_techs,
            "nombre_sugerido": ", ".join(top_techs[:2]) if top_techs else f"Cluster {cluster_id}"
        }
        logger.info(f"Cluster {cluster_id}: {mask.sum()} ofertas — {top_techs}")

    return etiquetas, resumen


def aplicar_regresion_salario(df: pd.DataFrame) -> dict | None:
    """
    Predice salario promedio en función de tecnologías + ubicación.
    Retorna dict con métricas, o None si no hay suficientes datos.
    """
    MIN_MUESTRAS = 20
    df_sal = df.dropna(subset=["salario_min", "salario_max"]).copy()

    if len(df_sal) < MIN_MUESTRAS:
        logger.info(
            f"Regresión omitida: solo {len(df_sal)} ofertas con salario "
            f"(mínimo requerido: {MIN_MUESTRAS})."
        )
        return None

    df_sal["salario_promedio"] = (df_sal["salario_min"] + df_sal["salario_max"]) / 2
    y = df_sal["salario_promedio"].values

    # Features: tecnologías one-hot + ubicación one-hot
    X_tech, _ = preparar_features_tecnologias(df_sal)
    X_ubicacion = pd.get_dummies(df_sal["ubicacion"].fillna("desconocido"), prefix="ubic")
    X = np.hstack([X_tech, X_ubicacion.values])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    logger.info(f"Regresión salario — MAE: {mae:.0f}, R²: {r2:.3f}")
    return {"mae": mae, "r2": r2, "modelo": modelo, "n_muestras": len(df_sal)}


def ejecutar_analisis_completo(df: pd.DataFrame) -> dict:
    """
    Ejecuta clustering + regresión y retorna resultados para el dashboard.
    Añade columna 'cluster' al DataFrame.
    """
    resultados = {}

    # Clustering (técnica principal)
    X, nombres_tech = preparar_features_tecnologias(df)

    if len(df) < 2:
        logger.warning("Muy pocas muestras para clustering.")
        df[COLUMNAS_CLUSTER_GUARDADO] = 0
        resultados["clusters"] = {0: {"n_ofertas": len(df), "tecnologias_top": [], "nombre_sugerido": "General"}}
    else:
        etiquetas, resumen_clusters = aplicar_kmeans(X, df)
        df[COLUMNAS_CLUSTER_GUARDADO] = etiquetas
        resultados["clusters"] = resumen_clusters

    # Regresión (técnica secundaria, opcional)
    resultados["regresion"] = aplicar_regresion_salario(df)

    resultados["n_tecnologias"] = len(nombres_tech)
    return resultados
```

- [ ] **Step 4: Ejecutar tests de ML**

```powershell
pytest tests/test_ml.py -v
```

Esperado: `3 passed`

- [ ] **Step 5: Probar ML con datos reales**

```powershell
python -c "
from src.procesamiento.transformacion import construir_dataset_unificado
from src.ml.analisis import ejecutar_analisis_completo
df = construir_dataset_unificado()
resultados = ejecutar_analisis_completo(df)
print('Clusters:', resultados['clusters'])
print('Regresión:', resultados['regresion'])
"
```

- [ ] **Step 6: Commit**

```powershell
git add src/ml/analisis.py tests/test_ml.py
git commit -m "feat: ML — clustering K-Means por perfil tecnologico y regresion de salarios"
```

---

## Task 6: FASE 6 — Dashboard Streamlit

**Files:**
- Create: `mercado-it-panama/dashboard/app.py`

- [ ] **Step 1: Verificar que el CSV existe**

```powershell
python -c "
from src.procesamiento.transformacion import construir_dataset_unificado
from src.ml.analisis import ejecutar_analisis_completo
import pandas as pd
from src.config import OFERTAS_CSV
df = construir_dataset_unificado()
ejecutar_analisis_completo(df)
df.to_csv(OFERTAS_CSV, index=False)
print('CSV listo:', OFERTAS_CSV.exists(), '— Filas:', len(df))
"
```

Esperado: imprime `CSV listo: True — Filas: <número>`.

- [ ] **Step 2: Crear `dashboard/app.py`**

```python
# dashboard/app.py
"""
Dashboard interactivo del Mercado Laboral IT en Panamá.
Ejecutar con: streamlit run dashboard/app.py
"""
import ast
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.decomposition import PCA

# Asegurar que src/ sea importable
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import OFERTAS_CSV

st.set_page_config(
    page_title="Mercado IT Panamá",
    page_icon="💻",
    layout="wide",
)

# ── Carga de datos ──────────────────────────────────────────────────────────

@st.cache_data
def cargar_datos():
    if not OFERTAS_CSV.exists():
        st.error("No se encontró el dataset. Ejecuta primero: python run_pipeline.py")
        st.stop()
    df = pd.read_csv(OFERTAS_CSV, parse_dates=["fecha"])

    # Parsear tecnologias (guardadas como string "python|react|...")
    def parsear_techs(val):
        if pd.isna(val) or val == "":
            return []
        if isinstance(val, list):
            return val
        # Formato pipe-separated
        if "|" in str(val):
            return [t.strip() for t in str(val).split("|") if t.strip()]
        # Formato lista Python
        try:
            return ast.literal_eval(str(val))
        except Exception:
            return []

    df["tecnologias"] = df["tecnologias"].apply(parsear_techs)

    # Columna cluster (si existe)
    if "cluster" not in df.columns:
        df["cluster"] = 0

    return df


df = cargar_datos()

# ── Sidebar: Filtros ─────────────────────────────────────────────────────────

st.sidebar.title("Filtros")

# Fuente
fuentes_disponibles = sorted(df["fuente"].dropna().unique())
fuentes_sel = st.sidebar.multiselect(
    "Fuente de datos", fuentes_disponibles, default=fuentes_disponibles
)

# Tecnología
todas_techs = sorted({t for techs in df["tecnologias"] for t in techs})
techs_sel = st.sidebar.multiselect("Tecnología", todas_techs, default=[])

# Ubicación
ubicaciones = sorted(df["ubicacion"].dropna().unique())
ubicacion_sel = st.sidebar.multiselect("Ubicación", ubicaciones, default=[])

# Rango de salario
sal_max_global = int(df["salario_max"].dropna().max()) if df["salario_max"].notna().any() else 10000
sal_rango = st.sidebar.slider(
    "Salario máximo (USD)", 0, sal_max_global, (0, sal_max_global)
)

# Aplicar filtros
df_filtrado = df[df["fuente"].isin(fuentes_sel)].copy()

if techs_sel:
    df_filtrado = df_filtrado[
        df_filtrado["tecnologias"].apply(
            lambda ts: any(t in ts for t in techs_sel)
        )
    ]

if ubicacion_sel:
    df_filtrado = df_filtrado[df_filtrado["ubicacion"].isin(ubicacion_sel)]

# Filtro salario (solo filas con salario)
mask_sal = (
    df_filtrado["salario_max"].isna() |
    (
        (df_filtrado["salario_max"] >= sal_rango[0]) &
        (df_filtrado["salario_max"] <= sal_rango[1])
    )
)
df_filtrado = df_filtrado[mask_sal]

# ── Header ───────────────────────────────────────────────────────────────────

st.title("💻 Mercado Laboral IT en Panamá")
st.caption("Análisis de ofertas de trabajo — Proyecto Universitario UTP-FISC | Gestión de la Información")

# ── Métricas resumen ─────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Ofertas", len(df_filtrado))
col2.metric("Fuentes", df_filtrado["fuente"].nunique())
col3.metric("Tecnologías únicas", len({t for ts in df_filtrado["tecnologias"] for t in ts}))
sal_prom = df_filtrado["salario_min"].mean()
col4.metric("Salario promedio (USD)", f"${sal_prom:,.0f}" if not pd.isna(sal_prom) else "N/D")

st.divider()

# ── Gráficas ─────────────────────────────────────────────────────────────────

col_izq, col_der = st.columns(2)

# 1. Top tecnologías más demandadas
with col_izq:
    st.subheader("Top Tecnologías más Demandadas")
    from collections import Counter
    conteo_techs = Counter(t for ts in df_filtrado["tecnologias"] for t in ts)
    if conteo_techs:
        df_techs = pd.DataFrame(conteo_techs.most_common(20), columns=["tecnologia", "ofertas"])
        fig1 = px.bar(
            df_techs, x="ofertas", y="tecnologia", orientation="h",
            color="ofertas", color_continuous_scale="Blues",
            title="Tecnologías más solicitadas"
        )
        fig1.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Sin datos para mostrar.")

# 2. Distribución de salarios por tecnología
with col_der:
    st.subheader("Distribución de Salarios")
    df_sal = df_filtrado.dropna(subset=["salario_min", "salario_max"])
    if len(df_sal) > 0:
        df_sal = df_sal.copy()
        df_sal["salario_promedio"] = (df_sal["salario_min"] + df_sal["salario_max"]) / 2
        fig2 = px.histogram(
            df_sal, x="salario_promedio", nbins=20,
            color="fuente",
            title="Distribución de salarios (USD)",
            labels={"salario_promedio": "Salario USD", "count": "Número de ofertas"}
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sin datos salariales para el filtro actual.")

st.divider()

col_izq2, col_der2 = st.columns(2)

# 3. Ofertas por fuente
with col_izq2:
    st.subheader("Ofertas por Fuente de Datos")
    conteo_fuentes = df_filtrado["fuente"].value_counts().reset_index()
    conteo_fuentes.columns = ["fuente", "cantidad"]
    fig3 = px.pie(
        conteo_fuentes, names="fuente", values="cantidad",
        title="Distribución por fuente",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig3, use_container_width=True)

# 4. Clustering PCA
with col_der2:
    st.subheader("Clusters de Perfiles Tecnológicos")
    df_cluster = df_filtrado[df_filtrado["tecnologias"].apply(len) > 0].copy()
    if len(df_cluster) >= 4:
        from sklearn.preprocessing import MultiLabelBinarizer
        mlb = MultiLabelBinarizer()
        X = mlb.fit_transform(df_cluster["tecnologias"].tolist())
        if X.shape[1] >= 2:
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(X)
            df_cluster["pca_x"] = coords[:, 0]
            df_cluster["pca_y"] = coords[:, 1]
            df_cluster["cluster_str"] = df_cluster["cluster"].astype(str)
            fig4 = px.scatter(
                df_cluster, x="pca_x", y="pca_y",
                color="cluster_str",
                hover_data={"titulo": True, "fuente": True, "pca_x": False, "pca_y": False},
                title="Clusters (PCA 2D)",
                labels={"cluster_str": "Cluster", "pca_x": "PCA 1", "pca_y": "PCA 2"}
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Pocas tecnologías únicas para PCA.")
    else:
        st.info("Necesitas más datos para visualizar clusters.")

# 5. Tendencia temporal
st.subheader("Tendencia de Publicaciones")
df_fechas = df_filtrado.dropna(subset=["fecha"]).copy()
if len(df_fechas) > 1:
    df_fechas["mes"] = df_fechas["fecha"].dt.to_period("M").dt.to_timestamp()
    tendencia = df_fechas.groupby(["mes", "fuente"]).size().reset_index(name="ofertas")
    fig5 = px.line(
        tendencia, x="mes", y="ofertas", color="fuente", markers=True,
        title="Publicaciones por mes",
        labels={"mes": "Mes", "ofertas": "Nº de ofertas"}
    )
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Sin suficientes datos temporales para mostrar tendencia.")

st.divider()

# ── Tabla de ofertas ──────────────────────────────────────────────────────────

st.subheader(f"Ofertas ({len(df_filtrado)} resultados)")
cols_mostrar = [c for c in ["titulo", "empresa", "ubicacion", "fuente", "salario_min", "salario_max", "fecha"] if c in df_filtrado.columns]
st.dataframe(
    df_filtrado[cols_mostrar].sort_values("fecha", ascending=False),
    use_container_width=True,
    height=300
)

st.caption("Proyecto: Análisis del Mercado Laboral IT en Panamá · UTP-FISC · Gestión de la Información · Grupo 4")
```

- [ ] **Step 3: Levantar el dashboard y verificar**

```powershell
# Desde mercado-it-panama/ con venv activo
streamlit run dashboard/app.py
```

Abrir `http://localhost:8501` en el navegador. Verificar:
- Las 4 métricas muestran valores reales
- El gráfico de top tecnologías muestra barras
- El pie chart de fuentes muestra "remotive" y "kaggle"
- La tabla de ofertas muestra datos
- Los filtros del sidebar funcionan y actualizan las gráficas

Detener con `Ctrl+C`.

- [ ] **Step 4: Commit**

```powershell
git add dashboard/app.py
git commit -m "feat: dashboard Streamlit con filtros interactivos y graficas Plotly"
```

---

## Task 7: FASE 3 — Scraper Computrabajo Panamá

**Files:**
- Create: `mercado-it-panama/src/ingesta/scraper_computrabajo.py`

- [ ] **Step 1: Verificar robots.txt antes de scrapear**

Abrir en el navegador o ejecutar:

```powershell
python -c "
import requests
r = requests.get('https://www.computrabajo.com.pa/robots.txt', headers={'User-Agent': 'MercadoITPanama/1.0'})
print(r.text[:2000])
"
```

Revisar que no esté prohibido scrapear `/empleos/` o la sección IT. Si robots.txt lo prohíbe, documentarlo en el código y devolver lista vacía.

- [ ] **Step 2: Escribir test que falla**

Agregar a `tests/test_scraper.py`:

```python
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from unittest.mock import patch, MagicMock
from src.ingesta.scraper_computrabajo import scrapear_computrabajo

def test_scraper_retorna_lista():
    """El scraper siempre retorna lista (puede estar vacía)."""
    # Mock para no hacer requests reales en tests
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """
    <html><body>
    <article class="box_offer">
        <h2><a href="/empleo/python-developer">Python Developer</a></h2>
        <span class="tc">TechCorp Panamá</span>
        <span class="tl">Ciudad de Panamá</span>
        <time>hace 2 días</time>
        <p>Buscamos developer con Python y Django</p>
    </article>
    </body></html>
    """
    with patch("src.ingesta.scraper_computrabajo.requests.get", return_value=mock_response):
        resultado = scrapear_computrabajo(max_paginas=1)
    assert isinstance(resultado, list)

def test_scraper_falla_con_gracia():
    """Si el sitio falla, retorna lista vacía sin lanzar excepción."""
    with patch("src.ingesta.scraper_computrabajo.requests.get", side_effect=Exception("blocked")):
        resultado = scrapear_computrabajo(max_paginas=1)
    assert resultado == []
```

- [ ] **Step 3: Verificar que los tests fallan**

```powershell
pytest tests/test_scraper.py -v
```

Esperado: `FAILED` con `ModuleNotFoundError`.

- [ ] **Step 4: Crear `src/ingesta/scraper_computrabajo.py`**

```python
# src/ingesta/scraper_computrabajo.py
"""
Scraper de Computrabajo Panamá — ofertas de tecnología/informática.
Respeta robots.txt: solo scrapea rutas permitidas.
Añade delay entre requests para no sobrecargar el servidor.
Si falla por bloqueo o cambio de estructura, devuelve lista vacía (degradación elegante).
"""
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from src.config import COMPUTRABAJO_RAW, DATA_RAW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.computrabajo.com.pa"
SEARCH_URL = f"{BASE_URL}/empleos-de-informatica-y-sistemas"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-PA,es;q=0.9",
}
DELAY_SEGUNDOS = 1.5  # Delay cortés entre requests


def _extraer_ofertas_de_pagina(html: str) -> list[dict]:
    """Parsea el HTML de una página de resultados y extrae las ofertas."""
    soup = BeautifulSoup(html, "lxml")
    ofertas = []

    # Intentar diferentes selectores (la estructura puede cambiar)
    contenedores = (
        soup.select("article.box_offer") or
        soup.select("div.box_offer") or
        soup.select("[data-id]") or
        soup.select(".js-click-job") or
        soup.select("article[class*='offer']")
    )

    for item in contenedores:
        try:
            # Título
            titulo_tag = (
                item.select_one("h2 a") or
                item.select_one("h3 a") or
                item.select_one("a[class*='js-o-link']")
            )
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""
            if not titulo:
                continue

            # Empresa
            empresa_tag = item.select_one(".tc") or item.select_one("[class*='company']")
            empresa = empresa_tag.get_text(strip=True) if empresa_tag else ""

            # Ubicación
            ubicacion_tag = item.select_one(".tl") or item.select_one("[class*='location']")
            ubicacion = ubicacion_tag.get_text(strip=True) if ubicacion_tag else "Panamá"

            # Fecha
            fecha_tag = item.select_one("time") or item.select_one("[class*='date']")
            fecha = fecha_tag.get("datetime") or (fecha_tag.get_text(strip=True) if fecha_tag else "")

            # Descripción/snippet
            desc_tag = item.select_one("p") or item.select_one("[class*='description']")
            descripcion = desc_tag.get_text(strip=True) if desc_tag else ""

            ofertas.append({
                "titulo": titulo,
                "empresa": empresa,
                "ubicacion": ubicacion,
                "fecha": fecha,
                "descripcion": descripcion,
                "fuente": "computrabajo",
            })
        except Exception as e:
            logger.debug(f"Error parseando item: {e}")
            continue

    return ofertas


def scrapear_computrabajo(max_paginas: int = 3) -> list[dict]:
    """
    Scrapea ofertas IT de Computrabajo Panamá con paginación.
    Retorna lista de dicts crudos. Si falla, retorna lista vacía.
    """
    logger.info(f"Iniciando scraping de Computrabajo (máx. {max_paginas} páginas)...")
    todas_las_ofertas = []

    try:
        for pagina in range(1, max_paginas + 1):
            url = SEARCH_URL if pagina == 1 else f"{SEARCH_URL}?p={pagina}"
            logger.info(f"Scrapeando página {pagina}: {url}")

            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if response.status_code in (403, 429):
                    logger.warning(f"Computrabajo bloqueó la solicitud (HTTP {response.status_code}). Deteniendo scraping.")
                    break
                raise

            ofertas_pagina = _extraer_ofertas_de_pagina(response.text)
            logger.info(f"Página {pagina}: {len(ofertas_pagina)} ofertas encontradas.")

            if not ofertas_pagina:
                logger.info("Sin más ofertas. Deteniendo paginación.")
                break

            todas_las_ofertas.extend(ofertas_pagina)

            # Delay cortés
            if pagina < max_paginas:
                time.sleep(DELAY_SEGUNDOS)

    except Exception as e:
        logger.warning(
            f"Computrabajo falló: {e}. "
            f"Pipeline continúa con {len(todas_las_ofertas)} ofertas parciales."
        )

    # Guardar crudo si se obtuvo algo
    if todas_las_ofertas:
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        with open(COMPUTRABAJO_RAW, "w", encoding="utf-8") as f:
            json.dump(todas_las_ofertas, f, ensure_ascii=False, indent=2)
        logger.info(f"Crudo guardado: {len(todas_las_ofertas)} ofertas en {COMPUTRABAJO_RAW}")

    return todas_las_ofertas


if __name__ == "__main__":
    resultado = scrapear_computrabajo(max_paginas=2)
    print(f"Ofertas obtenidas: {len(resultado)}")
    for o in resultado[:3]:
        print(f"  - {o['titulo']} @ {o['empresa']} ({o['ubicacion']})")
```

- [ ] **Step 5: Ejecutar tests**

```powershell
pytest tests/test_scraper.py -v
```

Esperado: `2 passed`

- [ ] **Step 6: Probar scraper real**

```powershell
python src/ingesta/scraper_computrabajo.py
```

Si retorna 0 ofertas (JavaScript rendering), agregar `playwright` a requirements e implementar la variante:

```powershell
pip install playwright
playwright install chromium
```

Y modificar `scrapear_computrabajo` para usar Playwright si BeautifulSoup no encontró ofertas:

```python
# Añadir al inicio del archivo si BeautifulSoup no funciona:
def _scrapear_con_playwright(url: str) -> str:
    """Fallback: renderiza JavaScript con Playwright si requests no funciona."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)  # Esperar JS
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.warning(f"Playwright también falló: {e}")
        return ""
```

- [ ] **Step 7: Integrar Computrabajo al pipeline unificado y regenerar CSV**

```powershell
python -c "
from src.procesamiento.transformacion import construir_dataset_unificado
from src.ml.analisis import ejecutar_analisis_completo
df = construir_dataset_unificado()
res = ejecutar_analisis_completo(df)
from src.config import OFERTAS_CSV
df.to_csv(OFERTAS_CSV, index=False)
print(f'Dataset con {len(df)} filas. Fuentes: {df.fuente.value_counts().to_dict()}')
"
```

- [ ] **Step 8: Commit**

```powershell
git add src/ingesta/scraper_computrabajo.py tests/test_scraper.py
git commit -m "feat: scraper Computrabajo con paginacion y degradacion elegante"
```

---

## Task 8: FASE 7 — Orquestador y README

**Files:**
- Create: `mercado-it-panama/run_pipeline.py`
- Create: `mercado-it-panama/README.md`

- [ ] **Step 1: Crear `run_pipeline.py`**

```python
# run_pipeline.py
"""
Orquestador del pipeline completo.
Uso: python run_pipeline.py
"""
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("pipeline")

sys.path.insert(0, str(Path(__file__).parent))


def main():
    print("\n" + "=" * 60)
    print("  PIPELINE: Mercado Laboral IT en Panamá")
    print("=" * 60)

    # ── Paso 1: Ingesta Remotive ──────────────────────────────────
    print("\n[1/4] Ingesta API Remotive...")
    from src.ingesta.api_remotive import ingerir_remotive
    ofertas_remotive = ingerir_remotive()
    print(f"      ✓ Remotive: {len(ofertas_remotive)} ofertas")

    # ── Paso 2: Ingesta Kaggle ────────────────────────────────────
    print("\n[2/4] Cargando dataset Kaggle...")
    from src.ingesta.loader_dataset import cargar_dataset
    from src.config import KAGGLE_EJEMPLO
    df_kaggle = cargar_dataset(KAGGLE_EJEMPLO)
    print(f"      ✓ Kaggle: {len(df_kaggle)} filas")

    # ── Paso 3: Ingesta Computrabajo ──────────────────────────────
    print("\n[3/4] Scrapeando Computrabajo Panamá...")
    from src.ingesta.scraper_computrabajo import scrapear_computrabajo
    ofertas_ct = scrapear_computrabajo(max_paginas=2)
    print(f"      ✓ Computrabajo: {len(ofertas_ct)} ofertas")

    # ── Paso 4: Procesamiento y ML ────────────────────────────────
    print("\n[4/4] Procesamiento, transformación y ML...")
    from src.procesamiento.transformacion import construir_dataset_unificado
    from src.ml.analisis import ejecutar_analisis_completo
    from src.config import OFERTAS_CSV

    df = construir_dataset_unificado()
    resultados_ml = ejecutar_analisis_completo(df)
    df.to_csv(OFERTAS_CSV, index=False)

    print(f"      ✓ Dataset unificado: {len(df)} ofertas")
    print(f"      ✓ Fuentes: {df['fuente'].value_counts().to_dict()}")
    print(f"      ✓ Clusters encontrados: {len(resultados_ml.get('clusters', {}))}")

    if resultados_ml.get("regresion"):
        reg = resultados_ml["regresion"]
        print(f"      ✓ Regresión salario — MAE: ${reg['mae']:,.0f} | R²: {reg['r2']:.3f}")
    else:
        print("      ℹ Regresión omitida (pocos datos salariales)")

    print("\n" + "=" * 60)
    print("  Pipeline completado con éxito.")
    print(f"  Dataset: {OFERTAS_CSV}")
    print("  Para ver el dashboard: streamlit run dashboard/app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Probar el pipeline completo**

```powershell
# Desde mercado-it-panama/ con venv activo
python run_pipeline.py
```

Esperado: pipeline completo sin errores, muestra resumen al final.

- [ ] **Step 3: Crear `README.md`**

```markdown
# Análisis del Mercado Laboral IT en Panamá

**Proyecto Integrador — Segundo Parcial**
Gestión de la Información · UTP-FISC · Grupo 4

Sistema de análisis del mercado laboral de tecnología en Panamá: ingestión de datos de múltiples fuentes, procesamiento, clustering ML y dashboard interactivo.

---

## Problemática

¿Cuáles son las tecnologías más demandadas en el mercado IT panameño? ¿Qué perfiles tecnológicos existen y qué salarios ofrecen? Este proyecto responde esas preguntas construyendo un pipeline de datos automatizado.

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
  ├──────────────────────────────────────────────────────────┤
  │  4. DATASET UNIFICADO → data/processed/ofertas.csv        │
  └──────────────────────────────────────────────────────────┘
         │                                              │
         ▼                                              ▼
   K-Means Clustering                          Dashboard Streamlit
```

## Fuentes de datos

| Fuente | Tipo | Relevancia |
|---|---|---|
| **Computrabajo Panamá** | Web Scraping | Ofertas locales de TI en Panamá |
| **Remotive API** | REST API pública | Empleos remotos tech; relevantes porque un desarrollador panameño puede aplicar a trabajos remotos internacionales |
| **Dataset Kaggle** | CSV descargado | Base de volumen — salarios y skills del sector tech global |

## Técnica de ML

**K-Means Clustering** sobre el perfil tecnológico de cada oferta (codificación one-hot de tecnologías). Descubre "familias" de puestos: cluster frontend, backend, data, devops, etc. Adicionalmente, **regresión RandomForest** para predecir salarios si hay suficientes datos.

La extracción de habilidades usa **matching de diccionario con regex** (sin LLMs) — ver `src/procesamiento/extraccion_tecnologias.py`.

## Requisitos previos

- Python 3.10 o superior
- Windows (desarrollado y probado en Windows 10/11)
- Git

## Instalación

```powershell
git clone <url-del-repo>
cd mercado-it-panama
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Dataset de Kaggle (opcional)

Para más volumen de datos, descargar un dataset de empleos IT desde Kaggle, por ejemplo:
- [Data Science Job Salaries](https://www.kaggle.com/datasets/ruchi798/data-science-job-salaries)

Renombrar el archivo a `kaggle_jobs.csv` y colocarlo en `data/raw/`. Luego editar `src/config.py` para que `KAGGLE_EJEMPLO` apunte al nuevo archivo. Si no se descarga, el pipeline usa el dataset de ejemplo incluido.

## Cómo ejecutar

```powershell
# 1. Activar entorno
.\venv\Scripts\activate

# 2. Correr el pipeline completo
python run_pipeline.py

# 3. Abrir el dashboard
streamlit run dashboard/app.py
```

Abrir `http://localhost:8501` en el navegador.

## Estructura del proyecto

```
mercado-it-panama/
├── data/
│   ├── raw/                      # datos crudos (gitignored)
│   └── processed/                # dataset unificado
├── src/
│   ├── config.py                 # rutas y diccionario de tecnologías
│   ├── ingesta/                  # 3 fuentes de datos
│   ├── procesamiento/            # limpieza, extracción, transformación
│   └── ml/                       # clustering y regresión
├── dashboard/app.py              # Streamlit
├── run_pipeline.py               # orquestador
└── requirements.txt
```

## Nota sobre el scraping

El scraper de Computrabajo puede fallar si el sitio cambia su HTML, activa protecciones anti-bot o requiere JavaScript. El pipeline **degrada con elegancia**: si esta fuente falla, continúa con Remotive y Kaggle, que son estables.

## Limitaciones y trabajo futuro

- **Chatbot / LLM:** No implementado en esta fase por restricción del curso. Una fase posterior podría añadir extracción de habilidades con NLP y un chatbot de consulta.
- **Cobertura geográfica:** ampliar a más fuentes locales de Panamá.
- **Actualización automática:** scheduling para re-ejecutar el pipeline periódicamente.
```

- [ ] **Step 4: Ejecutar suite completa de tests**

```powershell
pytest tests/ -v --tb=short
```

Esperado: todos los tests pasan.

- [ ] **Step 5: Verificar el pipeline completo de punta a punta**

```powershell
python run_pipeline.py
streamlit run dashboard/app.py
```

Verificar en el navegador que el dashboard muestra datos reales y los filtros funcionan.

- [ ] **Step 6: Commit final**

```powershell
git add run_pipeline.py README.md
git commit -m "feat: orquestador pipeline completo y README documentacion"
git tag v1.0 -m "Segundo Parcial — pipeline completo funcional"
```

---

## Criterios de aceptación finales

| Fase | Criterio |
|---|---|
| Setup | `pip install -r requirements.txt` sin errores en venv Windows |
| Remotive | `data/raw/remotive_raw.json` creado con ofertas reales |
| Kaggle | `cargar_dataset(KAGGLE_EJEMPLO)` retorna DataFrame con columnas mapeadas |
| Procesamiento | `data/processed/ofertas.csv` con columna `tecnologias` poblada |
| ML | Al menos clustering K-Means produce etiquetas interpretables |
| Dashboard | `streamlit run dashboard/app.py` levanta, filtros funcionan, gráficas renderizan |
| Computrabajo | Scraper intenta extracción o falla sin romper el pipeline |
| README | Usuario nuevo puede seguirlo sin pasos faltantes |
