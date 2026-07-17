# Modelo Estrella para Power BI + Integración LLM (Ollama) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar el dataset unificado en un modelo estrella (CSV) para Power BI, acumular un histórico por snapshots, e integrar un LLM local (Ollama) para consultas en lenguaje natural, resúmenes, extracción de skills y skills emergentes.

**Architecture:** El pipeline actual gana un campo `fecha_scrape` y un histórico acumulado (`data/processed/ofertas_historico.csv`). Un módulo nuevo (`modelo_estrella.py`) lee ese histórico y produce 8 CSV dimensionales en `data/powerbi/`. Un módulo LLM (`src/llm/ollama_cliente.py`) habla con Ollama por HTTP local con degradación elegante. El dashboard Streamlit gana una pestaña "Asistente IA".

**Tech Stack:** Python 3.10+, pandas, scikit-learn, Streamlit, Plotly, `requests` (para Ollama HTTP), pytest. Ollama local con modelo `llama3.2:3b`.

## Global Constraints

- Lenguaje: Python 3.10+. Plataforma: Windows 10/11.
- Sin dependencias nuevas pesadas: Ollama se consume vía HTTP con `requests` (ya está en `requirements.txt`).
- El LLM SIEMPRE degrada con elegancia: si Ollama no está corriendo, ninguna función lanza excepción — retornan un mensaje de *fallback*. El pipeline, el ML, el dashboard base y el modelo estrella funcionan sin Ollama.
- La extracción por regex (`extraccion_tecnologias.py`) sigue siendo el camino por defecto; el LLM es opcional.
- Los CSV del modelo estrella se escriben en `data/powerbi/`.
- Mantener los 27 tests actuales en verde.
- Nomenclatura y estilo en español, consistente con el código existente.
- URL Ollama: `http://localhost:11434`. Modelo por defecto: `llama3.2:3b` (configurable con env `OLLAMA_MODEL`).

## File Structure

- `src/config.py` — MODIFICAR: rutas `DATA_POWERBI`, `OFERTAS_HISTORICO_CSV`; dict `TECH_CATEGORIAS`; config Ollama.
- `src/procesamiento/transformacion.py` — MODIFICAR: añadir `fecha_scrape` al esquema y función `anexar_historico`.
- `src/procesamiento/modelo_estrella.py` — CREAR: builders de dimensiones + hechos + puente + orquestador.
- `src/llm/__init__.py` — CREAR: paquete.
- `src/llm/ollama_cliente.py` — CREAR: cliente Ollama + 4 funciones.
- `run_pipeline.py` — MODIFICAR: llamar a `anexar_historico` y `construir_modelo_estrella`.
- `dashboard/app.py` — MODIFICAR: envolver en pestañas y añadir pestaña "Asistente IA".
- `tests/test_modelo_estrella.py` — CREAR.
- `tests/test_llm.py` — CREAR.
- `tests/test_config.py` — CREAR.
- `docs/JUSTIFICACION_ML.md` — CREAR: justificación del modelo ML + conceptos y resultados.
- `docs/GUIA_POWERBI.md` — CREAR: guía de importación y relaciones.
- `README.md` — MODIFICAR: nuevas secciones.

---

### Task 1: Configuración — rutas, categorías de tecnologías y Ollama

**Files:**
- Modify: `src/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `DATA_POWERBI: Path`, `OFERTAS_HISTORICO_CSV: Path`, `TECH_CATEGORIAS: dict[str,str]`, `OLLAMA_URL: str`, `OLLAMA_MODEL: str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import TECH_DICT, TECH_CATEGORIAS, DATA_POWERBI, OFERTAS_HISTORICO_CSV, OLLAMA_URL, OLLAMA_MODEL

CATEGORIAS_VALIDAS = {"lenguaje", "framework", "base_datos", "cloud_devops", "otro"}

def test_toda_tech_tiene_categoria():
    faltantes = [t for t in TECH_DICT if t not in TECH_CATEGORIAS]
    assert faltantes == [], f"Techs sin categoría: {faltantes}"

def test_categorias_son_validas():
    invalidas = {c for c in TECH_CATEGORIAS.values() if c not in CATEGORIAS_VALIDAS}
    assert invalidas == set(), f"Categorías inválidas: {invalidas}"

def test_rutas_y_ollama_definidos():
    assert DATA_POWERBI.name == "powerbi"
    assert str(OFERTAS_HISTORICO_CSV).endswith("ofertas_historico.csv")
    assert OLLAMA_URL.startswith("http")
    assert OLLAMA_MODEL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL con `ImportError` (TECH_CATEGORIAS / DATA_POWERBI no existen).

- [ ] **Step 3: Implement — añadir al final de `src/config.py`**

Añadir `import os` al inicio del archivo (junto a `from pathlib import Path`), y al final:

```python
# Modelo estrella / Power BI
DATA_POWERBI = BASE_DIR / "data" / "powerbi"
OFERTAS_HISTORICO_CSV = DATA_PROCESSED / "ofertas_historico.csv"

# Categoría por tecnología (para dim_tecnologia del modelo estrella)
TECH_CATEGORIAS = {
    # Lenguajes
    "python": "lenguaje", "java": "lenguaje", "javascript": "lenguaje",
    "typescript": "lenguaje", "php": "lenguaje", "c#": "lenguaje",
    "go": "lenguaje", "ruby": "lenguaje", "kotlin": "lenguaje", "swift": "lenguaje",
    # Frameworks
    "react": "framework", "angular": "framework", "vue": "framework",
    "laravel": "framework", "django": "framework", "spring": "framework",
    "node.js": "framework", ".net": "framework", "flask": "framework", "fastapi": "framework",
    # Bases de datos
    "mysql": "base_datos", "mariadb": "base_datos", "postgresql": "base_datos",
    "mongodb": "base_datos", "redis": "base_datos", "sql server": "base_datos",
    "oracle": "base_datos", "sqlite": "base_datos",
    # Cloud / DevOps
    "aws": "cloud_devops", "azure": "cloud_devops", "gcp": "cloud_devops",
    "docker": "cloud_devops", "kubernetes": "cloud_devops", "git": "cloud_devops",
    "jenkins": "cloud_devops", "terraform": "cloud_devops", "linux": "cloud_devops",
    # Otros
    "rest": "otro", "graphql": "otro", "html": "otro", "css": "otro",
    "sql": "otro", "power bi": "otro", "tableau": "otro", "excel": "otro",
}

# Ollama (LLM local)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/test_config.py
git commit -m "feat: config de modelo estrella, categorías de tech y Ollama"
```

---

### Task 2: Pipeline temporal — `fecha_scrape` e histórico

**Files:**
- Modify: `src/procesamiento/transformacion.py`
- Test: `tests/test_historico.py` (crear)

**Interfaces:**
- Consumes: `OFERTAS_HISTORICO_CSV` (Task 1), `ESQUEMA_COLUMNAS`.
- Produces: `anexar_historico(df: pd.DataFrame, ruta=OFERTAS_HISTORICO_CSV) -> pd.DataFrame` (retorna el histórico completo tras anexar). El esquema unificado ahora incluye la columna `fecha_scrape` (str ISO `YYYY-MM-DD`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_historico.py
import sys, datetime
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.procesamiento.transformacion import anexar_historico, ESQUEMA_COLUMNAS

def _df_muestra(fecha_scrape):
    return pd.DataFrame([{
        "titulo": "dev python", "empresa": "acme", "ubicacion": "panamá",
        "tecnologias": "python|django", "salario_min": 1000.0, "salario_max": 2000.0,
        "fecha": None, "fuente": "konzerta", "descripcion": "desc",
        "fecha_scrape": fecha_scrape,
    }])

def test_fecha_scrape_en_esquema():
    assert "fecha_scrape" in ESQUEMA_COLUMNAS

def test_anexar_historico_acumula(tmp_path):
    ruta = tmp_path / "hist.csv"
    anexar_historico(_df_muestra("2026-07-16"), ruta=ruta)
    hist = anexar_historico(_df_muestra("2026-07-17"), ruta=ruta)
    assert len(hist) == 2
    assert set(hist["fecha_scrape"]) == {"2026-07-16", "2026-07-17"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_historico.py -v`
Expected: FAIL (`anexar_historico` no existe / `fecha_scrape` no está en el esquema).

- [ ] **Step 3: Implement**

En `src/procesamiento/transformacion.py`:

1. Añadir `import datetime` arriba.
2. Cambiar `ESQUEMA_COLUMNAS` para incluir `fecha_scrape`:

```python
ESQUEMA_COLUMNAS = [
    "titulo", "empresa", "ubicacion", "tecnologias",
    "salario_min", "salario_max", "fecha", "fuente", "descripcion", "fecha_scrape",
]
```

3. En CADA una de las cuatro funciones `transformar_*`, añadir la clave `"fecha_scrape"` al dict de cada fila, justo después de `"descripcion"`:

```python
            "descripcion": descripcion,
            "fecha_scrape": datetime.date.today().isoformat(),
```

4. Importar la ruta del histórico al inicio (junto a los otros imports de config):

```python
from src.config import (
    COMPUTRABAJO_RAW, KONZERTA_RAW, KAGGLE_EJEMPLO,
    OFERTAS_CSV, DATA_PROCESSED, OFERTAS_HISTORICO_CSV
)
```

5. Añadir la función al final del archivo:

```python
def anexar_historico(df: pd.DataFrame, ruta=OFERTAS_HISTORICO_CSV) -> pd.DataFrame:
    """
    Anexa el snapshot actual (df) al histórico acumulado en `ruta`.
    Cada corrida agrega sus filas; se conserva todo el historial temporal.
    Retorna el histórico completo tras anexar.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if ruta.exists():
        previo = pd.read_csv(ruta)
        total = pd.concat([previo, df], ignore_index=True)
    else:
        total = df.copy()
    total.to_csv(ruta, index=False)
    logger.info(f"Histórico: {len(total)} filas acumuladas en {ruta}")
    return total
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_historico.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Verify no regressions**

Run: `python -m pytest tests/ -v`
Expected: todos los tests previos siguen PASS.

- [ ] **Step 6: Commit**

```bash
git add src/procesamiento/transformacion.py tests/test_historico.py
git commit -m "feat: fecha_scrape en el esquema y anexar_historico por snapshots"
```

---

### Task 3: Modelo estrella — dimensiones

**Files:**
- Create: `src/procesamiento/modelo_estrella.py`
- Test: `tests/test_modelo_estrella.py`

**Interfaces:**
- Consumes: `TECH_CATEGORIAS` (Task 1), esquema con `fecha_scrape` (Task 2).
- Produces:
  - `construir_dim_empresa(df) -> pd.DataFrame` cols `[id_empresa, nombre_empresa]`
  - `construir_dim_ubicacion(df) -> pd.DataFrame` cols `[id_ubicacion, ubicacion, es_remoto]`
  - `construir_dim_fuente(df) -> pd.DataFrame` cols `[id_fuente, fuente]`
  - `construir_dim_tecnologia() -> pd.DataFrame` cols `[id_tecnologia, tecnologia, categoria]`
  - `construir_dim_cluster(df) -> pd.DataFrame` cols `[id_cluster, nombre_perfil]`
  - `construir_dim_fecha(df) -> pd.DataFrame` cols `[id_fecha, fecha, anio, mes, nombre_mes, trimestre, dia]`
  - `fecha_a_id(valor) -> int` (YYYYMMDD, o -1 si nulo/ inválido)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_modelo_estrella.py
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.procesamiento.modelo_estrella import (
    construir_dim_empresa, construir_dim_ubicacion, construir_dim_fuente,
    construir_dim_tecnologia, construir_dim_cluster, construir_dim_fecha, fecha_a_id,
)

def df_muestra():
    return pd.DataFrame([
        {"titulo": "dev python", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": "python|django", "salario_min": 1000.0, "salario_max": 2000.0,
         "fecha": "2026-05-10", "fuente": "konzerta", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 0},
        {"titulo": "react dev", "empresa": "globex", "ubicacion": "remoto",
         "tecnologias": "react|javascript", "salario_min": None, "salario_max": None,
         "fecha": None, "fuente": "kaggle", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 1},
        {"titulo": "otro python", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": "python", "salario_min": 1500.0, "salario_max": 1500.0,
         "fecha": "2026-05-10", "fuente": "konzerta", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 0},
    ])

def test_dim_empresa_sin_duplicados():
    dim = construir_dim_empresa(df_muestra())
    assert list(dim.columns) == ["id_empresa", "nombre_empresa"]
    assert dim["id_empresa"].is_unique
    assert dim["nombre_empresa"].nunique() == 2  # acme, globex

def test_dim_ubicacion_marca_remoto():
    dim = construir_dim_ubicacion(df_muestra())
    remoto = dim[dim["ubicacion"] == "remoto"]["es_remoto"].iloc[0]
    panama = dim[dim["ubicacion"] == "panamá"]["es_remoto"].iloc[0]
    assert bool(remoto) is True
    assert bool(panama) is False

def test_dim_fuente():
    dim = construir_dim_fuente(df_muestra())
    assert set(dim["fuente"]) == {"konzerta", "kaggle"}
    assert dim["id_fuente"].is_unique

def test_dim_tecnologia_tiene_categoria():
    dim = construir_dim_tecnologia()
    assert set(dim.columns) == {"id_tecnologia", "tecnologia", "categoria"}
    assert (dim["categoria"] != "").all()
    assert dim["id_tecnologia"].is_unique

def test_dim_cluster():
    dim = construir_dim_cluster(df_muestra())
    assert set(dim["id_cluster"]) == {0, 1}

def test_dim_fecha_unica_y_atributos():
    dim = construir_dim_fecha(df_muestra())
    assert dim["id_fecha"].is_unique
    fila = dim[dim["id_fecha"] == 20260510].iloc[0]
    assert fila["anio"] == 2026 and fila["mes"] == 5 and fila["dia"] == 10

def test_fecha_a_id_nulo():
    assert fecha_a_id(None) == -1
    assert fecha_a_id("2026-05-10") == 20260510
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_modelo_estrella.py -v`
Expected: FAIL (módulo no existe).

- [ ] **Step 3: Implement — crear `src/procesamiento/modelo_estrella.py`**

```python
# src/procesamiento/modelo_estrella.py
"""
Construye un modelo estrella (dimensiones + hechos + puente) a partir del
histórico de ofertas, y lo exporta como CSV en data/powerbi/ para Power BI.
"""
import logging
import pandas as pd
from pathlib import Path

from src.config import TECH_DICT, TECH_CATEGORIAS, DATA_POWERBI, OFERTAS_HISTORICO_CSV

logger = logging.getLogger(__name__)

_MESES_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_a_id(valor) -> int:
    """Convierte una fecha (str/date/Timestamp) a id entero YYYYMMDD. -1 si es nula."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return -1
    try:
        ts = pd.to_datetime(valor, errors="coerce")
        if pd.isna(ts):
            return -1
        return int(ts.strftime("%Y%m%d"))
    except Exception:
        return -1


def _dim_desde_columna(df, columna, col_id, col_valor, default="desconocido"):
    """Crea una dimensión simple de valores únicos con id surrogate 1..N."""
    valores = (
        df[columna].fillna(default).replace("", default).astype(str).drop_duplicates()
        .sort_values().reset_index(drop=True)
    )
    return pd.DataFrame({col_id: range(1, len(valores) + 1), col_valor: valores})


def construir_dim_empresa(df):
    return _dim_desde_columna(df, "empresa", "id_empresa", "nombre_empresa")


def construir_dim_fuente(df):
    return _dim_desde_columna(df, "fuente", "id_fuente", "fuente")


def construir_dim_ubicacion(df):
    dim = _dim_desde_columna(df, "ubicacion", "id_ubicacion", "ubicacion")
    dim["es_remoto"] = dim["ubicacion"].str.contains("remot", case=False, na=False)
    return dim


def construir_dim_tecnologia():
    filas = [
        {"id_tecnologia": i, "tecnologia": t, "categoria": TECH_CATEGORIAS.get(t, "otro")}
        for i, t in enumerate(sorted(TECH_DICT.keys()), start=1)
    ]
    return pd.DataFrame(filas, columns=["id_tecnologia", "tecnologia", "categoria"])


def construir_dim_cluster(df):
    if "cluster" not in df.columns:
        df = df.assign(cluster=0)
    filas = []
    for cid in sorted(df["cluster"].dropna().unique()):
        sub = df[df["cluster"] == cid]
        techs = (
            sub["tecnologias"].fillna("").astype(str)
            .str.split("|").explode().str.strip()
        )
        techs = techs[techs != ""]
        top = techs.value_counts().head(2).index.tolist()
        nombre = ", ".join(top) if top else f"Cluster {int(cid)}"
        filas.append({"id_cluster": int(cid), "nombre_perfil": nombre})
    return pd.DataFrame(filas, columns=["id_cluster", "nombre_perfil"])


def construir_dim_fecha(df):
    fechas = pd.concat([df["fecha"], df["fecha_scrape"]], ignore_index=True)
    ts = pd.to_datetime(fechas, errors="coerce").dropna().drop_duplicates()
    filas = []
    for t in sorted(ts):
        filas.append({
            "id_fecha": int(t.strftime("%Y%m%d")),
            "fecha": t.date().isoformat(),
            "anio": t.year, "mes": t.month, "nombre_mes": _MESES_ES[t.month],
            "trimestre": (t.month - 1) // 3 + 1, "dia": t.day,
        })
    # Miembro centinela para fechas nulas
    filas.append({"id_fecha": -1, "fecha": None, "anio": None, "mes": None,
                  "nombre_mes": "sin fecha", "trimestre": None, "dia": None})
    return pd.DataFrame(filas)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_modelo_estrella.py -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add src/procesamiento/modelo_estrella.py tests/test_modelo_estrella.py
git commit -m "feat: dimensiones del modelo estrella"
```

---

### Task 4: Modelo estrella — hechos, puente y orquestador

**Files:**
- Modify: `src/procesamiento/modelo_estrella.py`
- Test: `tests/test_modelo_estrella.py` (añadir tests)

**Interfaces:**
- Consumes: builders de la Task 3.
- Produces:
  - `construir_fact_y_bridge(df, dims: dict) -> tuple[pd.DataFrame, pd.DataFrame]` — `fact_ofertas` cols `[id_oferta, id_empresa, id_ubicacion, id_fuente, id_fecha_scrape, id_fecha_publicacion, id_cluster, salario_min, salario_max, salario_promedio, num_tecnologias, titulo]`; `bridge` cols `[id_oferta, id_tecnologia]`.
  - `construir_modelo_estrella(df=None, salida_dir=DATA_POWERBI) -> dict[str, pd.DataFrame]` — orquesta todo, escribe los 8 CSV y retorna el dict de tablas. Si `df` es None, carga el histórico.

- [ ] **Step 1: Write the failing test**

```python
# añadir a tests/test_modelo_estrella.py
from src.procesamiento.modelo_estrella import construir_fact_y_bridge, construir_modelo_estrella

def _dims(df):
    return {
        "dim_empresa": construir_dim_empresa(df),
        "dim_ubicacion": construir_dim_ubicacion(df),
        "dim_fuente": construir_dim_fuente(df),
        "dim_tecnologia": construir_dim_tecnologia(),
        "dim_cluster": construir_dim_cluster(df),
        "dim_fecha": construir_dim_fecha(df),
    }

def test_fact_fks_validas():
    df = df_muestra()
    dims = _dims(df)
    fact, bridge = construir_fact_y_bridge(df, dims)
    assert len(fact) == 3
    assert fact["id_empresa"].isin(dims["dim_empresa"]["id_empresa"]).all()
    assert fact["id_fuente"].isin(dims["dim_fuente"]["id_fuente"]).all()
    # fecha nula → id_fecha_publicacion == -1 (fila 2)
    assert (fact["id_fecha_publicacion"] == -1).sum() == 1

def test_fact_salario_promedio():
    df = df_muestra()
    fact, _ = construir_fact_y_bridge(df, _dims(df))
    fila0 = fact[fact["id_oferta"] == 0].iloc[0]
    assert fila0["salario_promedio"] == 1500.0  # (1000+2000)/2

def test_bridge_cubre_tecnologias():
    df = df_muestra()
    dims = _dims(df)
    _, bridge = construir_fact_y_bridge(df, dims)
    # oferta 0 tiene python+django → 2 filas puente
    assert (bridge["id_oferta"] == 0).sum() == 2
    assert bridge["id_tecnologia"].isin(dims["dim_tecnologia"]["id_tecnologia"]).all()

def test_orquestador_escribe_8_csv(tmp_path):
    tablas = construir_modelo_estrella(df=df_muestra(), salida_dir=tmp_path)
    esperados = ["dim_empresa", "dim_ubicacion", "dim_fuente", "dim_tecnologia",
                 "dim_cluster", "dim_fecha", "fact_ofertas", "bridge_oferta_tecnologia"]
    for nombre in esperados:
        assert (tmp_path / f"{nombre}.csv").exists(), f"falta {nombre}.csv"
        assert nombre in tablas
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_modelo_estrella.py -v`
Expected: FAIL (`construir_fact_y_bridge` no existe).

- [ ] **Step 3: Implement — añadir a `modelo_estrella.py`**

```python
def _mapa(dim, col_id, col_valor):
    return dict(zip(dim[col_valor].astype(str), dim[col_id]))


def construir_fact_y_bridge(df, dims):
    df = df.reset_index(drop=True)
    if "cluster" not in df.columns:
        df = df.assign(cluster=0)

    m_emp = _mapa(dims["dim_empresa"], "id_empresa", "nombre_empresa")
    m_ubi = _mapa(dims["dim_ubicacion"], "id_ubicacion", "ubicacion")
    m_fue = _mapa(dims["dim_fuente"], "id_fuente", "fuente")
    m_tec = _mapa(dims["dim_tecnologia"], "id_tecnologia", "tecnologia")

    filas_fact, filas_bridge = [], []
    for i, fila in df.iterrows():
        smin = fila.get("salario_min")
        smax = fila.get("salario_max")
        if pd.notna(smin) and pd.notna(smax):
            sprom = (float(smin) + float(smax)) / 2
        else:
            sprom = None
        techs = [t.strip() for t in str(fila.get("tecnologias") or "").split("|") if t.strip()]
        filas_fact.append({
            "id_oferta": i,
            "id_empresa": m_emp.get(str(fila.get("empresa") or "desconocido"), -1),
            "id_ubicacion": m_ubi.get(str(fila.get("ubicacion") or "desconocido"), -1),
            "id_fuente": m_fue.get(str(fila.get("fuente") or "desconocido"), -1),
            "id_fecha_scrape": fecha_a_id(fila.get("fecha_scrape")),
            "id_fecha_publicacion": fecha_a_id(fila.get("fecha")),
            "id_cluster": int(fila.get("cluster") if pd.notna(fila.get("cluster")) else 0),
            "salario_min": smin if pd.notna(smin) else None,
            "salario_max": smax if pd.notna(smax) else None,
            "salario_promedio": sprom,
            "num_tecnologias": len(techs),
            "titulo": fila.get("titulo"),
        })
        for t in techs:
            if t in m_tec:
                filas_bridge.append({"id_oferta": i, "id_tecnologia": m_tec[t]})

    fact = pd.DataFrame(filas_fact)
    bridge = pd.DataFrame(filas_bridge, columns=["id_oferta", "id_tecnologia"])
    return fact, bridge


def construir_modelo_estrella(df=None, salida_dir=DATA_POWERBI):
    """Orquesta dimensiones + hechos + puente y escribe los 8 CSV en salida_dir."""
    if df is None:
        if not Path(OFERTAS_HISTORICO_CSV).exists():
            logger.warning("No hay histórico; modelo estrella no generado.")
            return {}
        df = pd.read_csv(OFERTAS_HISTORICO_CSV)

    dims = {
        "dim_empresa": construir_dim_empresa(df),
        "dim_ubicacion": construir_dim_ubicacion(df),
        "dim_fuente": construir_dim_fuente(df),
        "dim_tecnologia": construir_dim_tecnologia(),
        "dim_cluster": construir_dim_cluster(df),
        "dim_fecha": construir_dim_fecha(df),
    }
    fact, bridge = construir_fact_y_bridge(df, dims)
    tablas = {**dims, "fact_ofertas": fact, "bridge_oferta_tecnologia": bridge}

    salida = Path(salida_dir)
    salida.mkdir(parents=True, exist_ok=True)
    for nombre, tabla in tablas.items():
        tabla.to_csv(salida / f"{nombre}.csv", index=False)
    logger.info(f"Modelo estrella: {len(tablas)} tablas escritas en {salida}")
    return tablas
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_modelo_estrella.py -v`
Expected: PASS (11 tests en el archivo).

- [ ] **Step 5: Commit**

```bash
git add src/procesamiento/modelo_estrella.py tests/test_modelo_estrella.py
git commit -m "feat: hechos, puente y orquestador del modelo estrella"
```

---

### Task 5: Integrar histórico y modelo estrella en el pipeline

**Files:**
- Modify: `run_pipeline.py`

**Interfaces:**
- Consumes: `anexar_historico` (Task 2), `construir_modelo_estrella` (Task 4), `ejecutar_analisis_completo`.

- [ ] **Step 1: Modificar `run_pipeline.py`**

Reemplazar el bloque del Paso 3 (líneas ~39-51, desde `# ── Paso 3` hasta la línea `print(f"      OK Fuentes...")`) por:

```python
    # ── Paso 3: Procesamiento + ML ────────────────────────────
    print("\n[3/4] Procesamiento, transformacion y ML...")
    from src.procesamiento.transformacion import construir_dataset_unificado, anexar_historico
    from src.ml.analisis import ejecutar_analisis_completo
    from src.config import OFERTAS_CSV

    df = construir_dataset_unificado()
    resultados_ml = ejecutar_analisis_completo(df)   # añade columna 'cluster'
    df.to_csv(OFERTAS_CSV, index=False)
    anexar_historico(df)                             # acumula snapshot (con cluster)

    print(f"      OK Dataset unificado: {len(df)} ofertas")
    print(f"      OK Fuentes: {df['fuente'].value_counts().to_dict()}")
    print(f"      OK Clusters encontrados: {len(resultados_ml.get('clusters', {}))}")

    # ── Paso 4: Modelo estrella para Power BI ─────────────────
    print("\n[4/4] Generando modelo estrella para Power BI...")
    from src.procesamiento.modelo_estrella import construir_modelo_estrella
    from src.config import DATA_POWERBI
    tablas = construir_modelo_estrella()
    print(f"      OK {len(tablas)} tablas escritas en {DATA_POWERBI}")
```

También cambiar los rótulos `[1/3]` y `[2/3]` por `[1/4]` y `[2/4]` en los prints de los pasos 1 y 2.

- [ ] **Step 2: Run the pipeline end-to-end**

Run: `python run_pipeline.py`
Expected: termina sin error; crea `data/processed/ofertas_historico.csv` y 8 CSV en `data/powerbi/`.

- [ ] **Step 3: Verify outputs**

Run: `python -c "from pathlib import Path; print(sorted(p.name for p in Path('data/powerbi').glob('*.csv')))"`
Expected: lista con los 8 CSV (`bridge_oferta_tecnologia.csv`, `dim_*.csv`, `fact_ofertas.csv`).

- [ ] **Step 4: Commit**

```bash
git add run_pipeline.py
git commit -m "feat: pipeline genera histórico y modelo estrella"
```

---

### Task 6: Cliente Ollama — conexión, consultas y resúmenes

**Files:**
- Create: `src/llm/__init__.py`, `src/llm/ollama_cliente.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Consumes: `OLLAMA_URL`, `OLLAMA_MODEL` (Task 1).
- Produces:
  - `ollama_disponible() -> bool`
  - `generar(prompt: str) -> tuple[bool, str]` (ok, texto/mensaje)
  - `resumen_datos(df: pd.DataFrame) -> str` (contexto compacto de estadísticas)
  - `consulta_natural(pregunta: str, df: pd.DataFrame) -> str`
  - `generar_resumen(df: pd.DataFrame) -> str`
  - Constante `MSG_FALLBACK: str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm.py
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm import ollama_cliente as oc

def df_muestra():
    return pd.DataFrame([
        {"titulo": "dev python", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": "python|django", "salario_min": 1000.0, "salario_max": 2000.0,
         "fuente": "konzerta"},
        {"titulo": "react dev", "empresa": "globex", "ubicacion": "remoto",
         "tecnologias": "react", "salario_min": None, "salario_max": None,
         "fuente": "kaggle"},
    ])

def test_resumen_datos_incluye_totales():
    ctx = oc.resumen_datos(df_muestra())
    assert "2" in ctx           # total ofertas
    assert "python" in ctx.lower()

def test_consulta_fallback_si_no_disponible(monkeypatch):
    monkeypatch.setattr(oc, "ollama_disponible", lambda: False)
    resp = oc.consulta_natural("¿cuáles techs?", df_muestra())
    assert resp == oc.MSG_FALLBACK

def test_consulta_usa_ollama_si_disponible(monkeypatch):
    monkeypatch.setattr(oc, "ollama_disponible", lambda: True)
    monkeypatch.setattr(oc, "generar", lambda prompt: (True, "respuesta de prueba"))
    resp = oc.consulta_natural("¿cuáles techs?", df_muestra())
    assert resp == "respuesta de prueba"

def test_generar_resumen_fallback(monkeypatch):
    monkeypatch.setattr(oc, "ollama_disponible", lambda: False)
    assert oc.generar_resumen(df_muestra()) == oc.MSG_FALLBACK
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_llm.py -v`
Expected: FAIL (módulo no existe).

- [ ] **Step 3: Implement**

Crear `src/llm/__init__.py` vacío.

Crear `src/llm/ollama_cliente.py`:

```python
# src/llm/ollama_cliente.py
"""
Cliente para Ollama (LLM local). Degrada con elegancia: si Ollama no está
corriendo, las funciones retornan MSG_FALLBACK sin lanzar excepción.
"""
import logging
from collections import Counter
import requests
import pandas as pd

from src.config import OLLAMA_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

MSG_FALLBACK = (
    "⚠️ Ollama no está disponible. Inícialo con `ollama serve` y descarga el "
    f"modelo con `ollama pull {OLLAMA_MODEL}`. El resto del proyecto funciona igual."
)
_TIMEOUT = 120


def ollama_disponible() -> bool:
    """True si el servicio de Ollama responde."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def generar(prompt: str):
    """Envía un prompt a Ollama. Retorna (ok, texto). Nunca lanza excepción."""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        return True, r.json().get("response", "").strip()
    except Exception as e:
        logger.warning(f"Fallo al generar con Ollama: {e}")
        return False, MSG_FALLBACK


def _techs_serie(df):
    return (df["tecnologias"].fillna("").astype(str).str.split("|").explode().str.strip())


def resumen_datos(df: pd.DataFrame) -> str:
    """Contexto compacto con estadísticas del dataset para el prompt."""
    techs = _techs_serie(df)
    techs = techs[techs != ""]
    top = Counter(techs).most_common(10)
    top_str = ", ".join(f"{t} ({n})" for t, n in top) or "sin datos"
    sal = pd.to_numeric(df.get("salario_min"), errors="coerce").dropna()
    sal_prom = f"${sal.mean():,.0f}" if len(sal) else "N/D"
    fuentes = ", ".join(sorted(df["fuente"].dropna().astype(str).unique()))
    return (
        f"Total de ofertas: {len(df)}. "
        f"Fuentes: {fuentes}. "
        f"Salario promedio: {sal_prom}. "
        f"Top tecnologías demandadas: {top_str}."
    )


def consulta_natural(pregunta: str, df: pd.DataFrame) -> str:
    if not ollama_disponible():
        return MSG_FALLBACK
    contexto = resumen_datos(df)
    prompt = (
        "Eres un analista del mercado laboral IT en Panamá. Responde en español, "
        "breve y claro, USANDO SOLO estos datos:\n"
        f"{contexto}\n\nPregunta: {pregunta}\nRespuesta:"
    )
    ok, texto = generar(prompt)
    return texto if ok else MSG_FALLBACK


def generar_resumen(df: pd.DataFrame) -> str:
    if not ollama_disponible():
        return MSG_FALLBACK
    contexto = resumen_datos(df)
    prompt = (
        "Eres un analista de datos. Escribe en español un resumen ejecutivo de 4-6 "
        "líneas del mercado laboral IT en Panamá con base en estos datos:\n"
        f"{contexto}\n\nResumen ejecutivo:"
    )
    ok, texto = generar(prompt)
    return texto if ok else MSG_FALLBACK
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_llm.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/llm/__init__.py src/llm/ollama_cliente.py tests/test_llm.py
git commit -m "feat: cliente Ollama con consultas y resúmenes (con fallback)"
```

---

### Task 7: LLM — extracción de skills y skills emergentes

**Files:**
- Modify: `src/llm/ollama_cliente.py`
- Test: `tests/test_llm.py` (añadir tests)

**Interfaces:**
- Consumes: `generar`, `ollama_disponible` (Task 6), `TECH_DICT` (config).
- Produces:
  - `extraer_skills_llm(texto: str) -> list[str]` (con caché en dict de módulo; fallback: lista vacía).
  - `skills_emergentes(df_historico: pd.DataFrame) -> str` (necesita ≥2 snapshots por `fecha_scrape`).

- [ ] **Step 1: Write the failing test**

```python
# añadir a tests/test_llm.py

def test_extraer_skills_fallback_lista_vacia(monkeypatch):
    monkeypatch.setattr(oc, "ollama_disponible", lambda: False)
    assert oc.extraer_skills_llm("dev python y react") == []

def test_extraer_skills_parsea_respuesta(monkeypatch):
    oc._CACHE_SKILLS.clear()
    monkeypatch.setattr(oc, "ollama_disponible", lambda: True)
    monkeypatch.setattr(oc, "generar", lambda p: (True, "python, react, herramienta_x"))
    skills = oc.extraer_skills_llm("buscamos dev python y react")
    assert "python" in skills and "react" in skills
    assert "herramienta_x" not in skills  # solo techs conocidas del TECH_DICT

def test_skills_emergentes_requiere_dos_snapshots(monkeypatch):
    monkeypatch.setattr(oc, "ollama_disponible", lambda: True)
    df = pd.DataFrame([{"tecnologias": "python", "fecha_scrape": "2026-07-16"}])
    resp = oc.skills_emergentes(df)
    assert "snapshot" in resp.lower()

def test_skills_emergentes_llama_llm(monkeypatch):
    monkeypatch.setattr(oc, "ollama_disponible", lambda: True)
    monkeypatch.setattr(oc, "generar", lambda p: (True, "análisis de tendencias"))
    df = pd.DataFrame([
        {"tecnologias": "python", "fecha_scrape": "2026-07-16"},
        {"tecnologias": "python|rust", "fecha_scrape": "2026-07-17"},
    ])
    assert oc.skills_emergentes(df) == "análisis de tendencias"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_llm.py -v`
Expected: FAIL (`extraer_skills_llm` / `_CACHE_SKILLS` no existen).

- [ ] **Step 3: Implement — añadir a `ollama_cliente.py`**

Añadir `from src.config import TECH_DICT` a los imports de config y este código:

```python
_CACHE_SKILLS: dict = {}


def extraer_skills_llm(texto: str) -> list:
    """
    Extrae tecnologías del texto usando el LLM, filtrando contra TECH_DICT.
    Paso OPCIONAL que complementa el regex. Cachea por texto. Fallback: [].
    """
    if not texto:
        return []
    if texto in _CACHE_SKILLS:
        return _CACHE_SKILLS[texto]
    if not ollama_disponible():
        return []
    conocidas = ", ".join(sorted(TECH_DICT.keys()))
    prompt = (
        "Extrae las tecnologías mencionadas en la siguiente oferta de empleo. "
        "Responde SOLO con una lista separada por comas, sin explicaciones. "
        f"Elige únicamente de esta lista: {conocidas}.\n\nOferta: {texto}\nTecnologías:"
    )
    ok, respuesta = generar(prompt)
    if not ok:
        return []
    candidatas = [c.strip().lower() for c in respuesta.split(",")]
    skills = [t for t in candidatas if t in TECH_DICT]
    _CACHE_SKILLS[texto] = skills
    return skills


def skills_emergentes(df_historico: pd.DataFrame) -> str:
    """
    Compara los dos últimos snapshots del histórico y pide al LLM que explique
    qué tecnologías están creciendo. Necesita ≥2 valores de fecha_scrape.
    """
    if not ollama_disponible():
        return MSG_FALLBACK
    snapshots = sorted(df_historico["fecha_scrape"].dropna().astype(str).unique())
    if len(snapshots) < 2:
        return ("Se necesitan al menos 2 snapshots (corridas del pipeline en fechas "
                "distintas) para analizar skills emergentes. Corre el pipeline otro día.")

    def conteo(fecha):
        sub = df_historico[df_historico["fecha_scrape"].astype(str) == fecha]
        techs = _techs_serie(sub)
        return Counter(techs[techs != ""])

    prev, ult = conteo(snapshots[-2]), conteo(snapshots[-1])
    deltas = {t: ult.get(t, 0) - prev.get(t, 0) for t in set(prev) | set(ult)}
    crecen = sorted(deltas.items(), key=lambda kv: kv[1], reverse=True)[:8]
    detalle = ", ".join(f"{t}: {'+' if d >= 0 else ''}{d}" for t, d in crecen)
    prompt = (
        "Eres analista de tendencias tech. Con estos cambios en la demanda de "
        f"tecnologías entre {snapshots[-2]} y {snapshots[-1]} (variación en nº de "
        f"ofertas): {detalle}. Explica en español (4-6 líneas) qué tecnologías están "
        "emergiendo y qué recomiendas aprender.\nAnálisis:"
    )
    ok, texto = generar(prompt)
    return texto if ok else MSG_FALLBACK
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_llm.py -v`
Expected: PASS (8 tests en el archivo).

- [ ] **Step 5: Commit**

```bash
git add src/llm/ollama_cliente.py tests/test_llm.py
git commit -m "feat: extracción de skills con LLM y análisis de skills emergentes"
```

---

### Task 8: Dashboard — pestaña "Asistente IA"

**Files:**
- Modify: `dashboard/app.py`

**Interfaces:**
- Consumes: `consulta_natural`, `generar_resumen`, `skills_emergentes`, `ollama_disponible` (Tasks 6-7); `OFERTAS_HISTORICO_CSV`.

- [ ] **Step 1: Implementar pestañas**

En `dashboard/app.py`, tras las líneas del header (después de `st.caption(...)` en la línea ~76), envolver TODO el contenido restante (métricas, gráficas, tabla) dentro de una pestaña, y añadir la pestaña IA.

1. Añadir import tras `from src.config import OFERTAS_CSV`:

```python
from src.config import OFERTAS_HISTORICO_CSV
from src.llm.ollama_cliente import (
    consulta_natural, generar_resumen, skills_emergentes, ollama_disponible,
)
```

2. Justo después del `st.caption(...)` del header, insertar:

```python
tab_dash, tab_ia = st.tabs(["📊 Dashboard", "🤖 Asistente IA"])
```

3. Indentar todo el contenido existente desde `# ── Métricas resumen` hasta la tabla filtrable (antes del `st.caption` final) bajo `with tab_dash:`. (El sidebar de filtros queda fuera, compartido por ambas pestañas.)

4. Antes del `st.caption(...)` final del archivo, añadir el bloque de la pestaña IA:

```python
with tab_ia:
    st.subheader("🤖 Asistente IA (Ollama local)")
    if not ollama_disponible():
        st.warning(
            "Ollama no está corriendo. Inícialo con `ollama serve` y descarga el "
            "modelo con `ollama pull llama3.2:3b` para usar el asistente."
        )
    else:
        st.success("Ollama conectado ✔")

    st.markdown("#### Consulta en lenguaje natural")
    pregunta = st.text_input(
        "Pregúntale a los datos",
        placeholder="Ej: ¿cuáles son las 5 tecnologías más demandadas?",
    )
    if st.button("Preguntar") and pregunta:
        with st.spinner("Pensando..."):
            st.info(consulta_natural(pregunta, df_f))

    st.divider()
    st.markdown("#### Resumen ejecutivo")
    if st.button("Generar resumen del mercado"):
        with st.spinner("Generando resumen..."):
            st.write(generar_resumen(df_f))

    st.divider()
    st.markdown("#### Skills emergentes")
    if st.button("Analizar skills emergentes"):
        with st.spinner("Analizando tendencia entre snapshots..."):
            if OFERTAS_HISTORICO_CSV.exists():
                hist = pd.read_csv(OFERTAS_HISTORICO_CSV)
                st.write(skills_emergentes(hist))
            else:
                st.info("Aún no hay histórico. Corre el pipeline al menos una vez.")
```

- [ ] **Step 2: Smoke test manual**

Run: `streamlit run dashboard/app.py`
Expected: abre en `http://localhost:8501`, se ven dos pestañas; "Asistente IA" muestra el aviso si Ollama está apagado, o los controles si está encendido. El dashboard base sigue funcionando igual.

- [ ] **Step 3: Verify no regressions**

Run: `python -m pytest tests/ -v`
Expected: todos los tests PASS (Streamlit no se testea aquí; se valida manual).

- [ ] **Step 4: Commit**

```bash
git add dashboard/app.py
git commit -m "feat: pestaña Asistente IA en el dashboard"
```

---

### Task 9: Documentación — justificación ML, guía Power BI y README

**Files:**
- Create: `docs/JUSTIFICACION_ML.md`, `docs/GUIA_POWERBI.md`
- Modify: `README.md`

- [ ] **Step 1: Crear `docs/JUSTIFICACION_ML.md`**

```markdown
# Justificación del Modelo de Machine Learning

## Problema
Queremos (1) descubrir qué perfiles tecnológicos existen en el mercado IT de Panamá
y (2) estimar el salario según tecnologías y ubicación. Son dos problemas distintos:
uno no supervisado (agrupar sin etiquetas) y uno supervisado (predecir un número).

## Técnica principal: K-Means (clustering)
**Por qué es la adecuada:** no tenemos etiquetas de "tipo de puesto"; queremos que los
datos revelen agrupaciones por sí mismos. K-Means agrupa las ofertas según las
tecnologías que comparten (codificadas one-hot con `MultiLabelBinarizer`), descubriendo
familias como frontend, backend, data o devops.

**Conceptos:**
- *One-hot de tecnologías*: cada oferta es un vector binario (tiene o no cada tecnología).
- *Método del codo*: probamos k=2..8 y elegimos el k donde la inercia deja de bajar
  fuerte (mayor caída marginal). Implementado en `_seleccionar_k_optimo`.
- *Inercia*: suma de distancias al cuadrado de cada punto a su centroide.

**Resultados:** cada cluster reporta nº de ofertas y sus tecnologías top, que usamos
como "nombre de perfil" en `dim_cluster`.

## Técnica secundaria: Regresión RandomForest
**Por qué:** el salario es numérico y depende de forma no lineal de muchas tecnologías y
la ubicación. RandomForest maneja bien no linealidades e interacciones sin escalar datos.
Se ejecuta solo si hay ≥20 ofertas con salario.

**Métricas:**
- *MAE* (Error Absoluto Medio): en promedio, cuántos dólares nos equivocamos.
- *R²*: proporción de la variación del salario explicada por el modelo (1.0 = perfecto).

## Limitaciones
El volumen y la calidad salarial de las fuentes locales limitan la regresión; por eso el
clustering es la técnica principal y la regresión es complementaria.
```

- [ ] **Step 2: Crear `docs/GUIA_POWERBI.md`**

```markdown
# Guía: Importar el Modelo Estrella en Power BI

## 1. Generar los CSV
Corre el pipeline: `python run_pipeline.py`. Esto crea 8 CSV en `data/powerbi/`.

## 2. Importar en Power BI Desktop
`Inicio → Obtener datos → Texto/CSV` e importa las 8 tablas:
`dim_empresa, dim_ubicacion, dim_fuente, dim_fecha, dim_tecnologia, dim_cluster,
fact_ofertas, bridge_oferta_tecnologia`.

## 3. Crear las relaciones (vista Modelo)
Arrastra para crear estas relaciones (1 → muchos, dirección simple desde la dimensión
hacia la tabla de hechos):

| Dimensión (1) | Columna | Hechos (muchos) | Columna |
|---|---|---|---|
| dim_empresa | id_empresa | fact_ofertas | id_empresa |
| dim_ubicacion | id_ubicacion | fact_ofertas | id_ubicacion |
| dim_fuente | id_fuente | fact_ofertas | id_fuente |
| dim_cluster | id_cluster | fact_ofertas | id_cluster |
| dim_fecha | id_fecha | fact_ofertas | id_fecha_scrape |
| dim_fecha | id_fecha | fact_ofertas | id_fecha_publicacion (inactiva) |

Para la tabla puente (tecnologías):
- `dim_tecnologia (1) → bridge (muchos)` por `id_tecnologia`
- `fact_ofertas (1) → bridge (muchos)` por `id_oferta`

## 4. KPIs sugeridos (medidas DAX)
```
Total Ofertas = COUNTROWS(fact_ofertas)
Salario Promedio = AVERAGE(fact_ofertas[salario_promedio])
% Remoto = DIVIDE(CALCULATE(COUNTROWS(fact_ofertas), dim_ubicacion[es_remoto]=TRUE()), [Total Ofertas])
Tecnologías Únicas = DISTINCTCOUNT(bridge_oferta_tecnologia[id_tecnologia])
```

## 5. Visualizaciones sugeridas
- Barras: top tecnologías (dim_tecnologia + conteo del bridge).
- Líneas: ofertas por mes (dim_fecha[anio-mes]) → tendencia temporal.
- Tarjetas: los KPIs de arriba.
- Segmentador por `dim_tecnologia[categoria]` y `dim_fuente[fuente]`.
```

- [ ] **Step 3: Actualizar `README.md`**

En la sección "Cómo ejecutar", tras el bloque de comandos, añadir:

```markdown
### Power BI
Tras `python run_pipeline.py`, los CSV del modelo estrella quedan en `data/powerbi/`.
Ver `docs/GUIA_POWERBI.md` para importarlos y crear las relaciones.

### Asistente IA (Ollama)
1. Instala [Ollama](https://ollama.com) y ejecútalo: `ollama serve`
2. Descarga el modelo: `ollama pull llama3.2:3b`
3. Abre el dashboard y ve a la pestaña "🤖 Asistente IA".
Si Ollama no está corriendo, el resto del proyecto funciona igual.
```

En la sección "Limitaciones y trabajo futuro", reemplazar la línea de "LLMs / Chatbot"
por:

```markdown
- **LLM (Ollama local):** consultas en lenguaje natural, resúmenes, extracción de skills
  y análisis de skills emergentes. Ver pestaña "Asistente IA" del dashboard.
```

- [ ] **Step 4: Commit**

```bash
git add docs/JUSTIFICACION_ML.md docs/GUIA_POWERBI.md README.md
git commit -m "docs: justificación ML, guía Power BI y actualización de README"
```

---

## Self-Review

**Spec coverage:**
- Modelo estrella (fact + bridge + 6 dims) → Tasks 3-4. ✅
- Histórico con `fecha_scrape` → Task 2. ✅
- LLM 4 funciones (consultas, resúmenes, extracción skills, skills emergentes) → Tasks 6-7. ✅
- Fallback sin Ollama → Task 6 (`MSG_FALLBACK`, tests de fallback). ✅
- Streamlit + pestaña IA → Task 8. ✅
- KPIs ampliados → Task 9 (guía DAX) + dashboard existente. ✅
- Justificación ML + conceptos/resultados → Task 9 (`JUSTIFICACION_ML.md`). ✅
- Guía import Power BI → Task 9 (`GUIA_POWERBI.md`). ✅
- Mantener 27 tests → verificado en Tasks 2 y 8. ✅

**Placeholder scan:** sin TBD/TODO; todo el código está completo en cada step. ✅

**Type consistency:** nombres de funciones y columnas verificados entre tasks
(`construir_modelo_estrella`, `construir_fact_y_bridge`, `fecha_a_id`, `ollama_disponible`,
`generar`, `consulta_natural`, `generar_resumen`, `extraer_skills_llm`, `skills_emergentes`,
`_CACHE_SKILLS`, `MSG_FALLBACK`, columnas `id_*`). ✅
