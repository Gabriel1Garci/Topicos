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
    dim = pd.DataFrame(filas)
    # Enteros nullable: evita que anio/mes/trimestre/dia se conviertan a
    # float64 (p.ej. 2026.0) al mezclar con los None de la fila centinela.
    for col in ["anio", "mes", "trimestre", "dia"]:
        dim[col] = dim[col].astype("Int64")
    return dim


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
