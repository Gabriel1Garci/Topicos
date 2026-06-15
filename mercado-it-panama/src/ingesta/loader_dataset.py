# src/ingesta/loader_dataset.py
"""
Carga CSV de empleos IT desde data/raw/.
Robusto a columnas variables: mapeo configurable al inicio del archivo.
"""
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Mapeo flexible: columna_destino → posibles nombres en el CSV (prioridad de arriba a abajo)
COLUMNAS_MAPEO = {
    "titulo_raw":      ["job_title", "title", "titulo", "position", "puesto", "job"],
    "empresa_raw":     ["company", "company_name", "empresa", "employer", "organization"],
    "ubicacion_raw":   ["location", "ubicacion", "city", "country", "lugar", "candidate_required_location"],
    "descripcion_raw": ["description", "descripcion", "job_description", "requirements", "skills", "resumen"],
    "salario_raw":     ["salary_range", "salary", "salario", "pay", "compensation", "wage"],
    "fecha_raw":       ["date_posted", "fecha", "published_at", "date", "posting_date"],
}


def cargar_dataset(ruta) -> pd.DataFrame:
    """
    Lee el CSV y renombra columnas al esquema interno.
    Si el archivo no existe o tiene error de lectura, retorna DataFrame vacío.
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

    # Mapear columnas de forma flexible (primera variante encontrada gana)
    renombrar = {}
    cols_lower = {c.lower(): c for c in df.columns}
    for col_destino, variantes in COLUMNAS_MAPEO.items():
        for variante in variantes:
            if variante.lower() in cols_lower:
                renombrar[cols_lower[variante.lower()]] = col_destino
                break

    df = df.rename(columns=renombrar)

    # Añadir columnas faltantes como NaN
    for col in COLUMNAS_MAPEO.keys():
        if col not in df.columns:
            df[col] = None

    logger.info(f"Dataset mapeado. Columnas: {list(df.columns)}")
    return df


if __name__ == "__main__":
    from src.config import KAGGLE_EJEMPLO
    df = cargar_dataset(KAGGLE_EJEMPLO)
    print(f"Filas: {len(df)}")
    print(df[["titulo_raw", "empresa_raw", "ubicacion_raw"]].head(5))
