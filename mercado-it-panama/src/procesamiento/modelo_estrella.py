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
