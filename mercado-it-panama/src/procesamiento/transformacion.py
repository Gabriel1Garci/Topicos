# src/procesamiento/transformacion.py
"""
Normaliza las salidas crudas de las fuentes al esquema común y
genera el dataset unificado en data/processed/ofertas.csv.
Solo incluye fuentes del mercado laboral de Panamá.
"""
import json
import logging
import datetime
import pandas as pd
from pathlib import Path

from src.config import (
    COMPUTRABAJO_RAW, KONZERTA_RAW, KAGGLE_EJEMPLO,
    OFERTAS_CSV, DATA_PROCESSED, OFERTAS_HISTORICO_CSV
)
from src.procesamiento.limpieza import limpiar_texto, parsear_salario, eliminar_duplicados_nulos
from src.procesamiento.extraccion_tecnologias import extraer_tecnologias

logger = logging.getLogger(__name__)

ESQUEMA_COLUMNAS = [
    "titulo", "empresa", "ubicacion", "tecnologias",
    "salario_min", "salario_max", "fecha", "fuente", "descripcion", "fecha_scrape",
]


def _parsear_fecha(valor):
    if not valor or (isinstance(valor, float)):
        return None
    try:
        from dateutil import parser as dateparser
        return dateparser.parse(str(valor)).date()
    except Exception:
        return None


def transformar_remotive(ofertas_crudas: list) -> pd.DataFrame:
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
            "fecha_scrape": datetime.date.today().isoformat(),
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
            "fecha_scrape": datetime.date.today().isoformat(),
        })
    logger.info(f"Kaggle: {len(filas)} ofertas transformadas.")
    return pd.DataFrame(filas, columns=ESQUEMA_COLUMNAS)


def transformar_computrabajo(ofertas_crudas: list) -> pd.DataFrame:
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
            "fecha_scrape": datetime.date.today().isoformat(),
        })
    logger.info(f"Computrabajo: {len(filas)} ofertas transformadas.")
    return pd.DataFrame(filas, columns=ESQUEMA_COLUMNAS)


def transformar_konzerta(ofertas_crudas: list) -> pd.DataFrame:
    """Mapea lista de dicts crudos del scraper Konzerta al esquema común."""
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
            "fuente":      "konzerta",
            "descripcion": descripcion,
            "fecha_scrape": datetime.date.today().isoformat(),
        })
    logger.info(f"Konzerta: {len(filas)} ofertas transformadas.")
    return pd.DataFrame(filas, columns=ESQUEMA_COLUMNAS)


def construir_dataset_unificado() -> pd.DataFrame:
    """
    Orquesta la transformación de las fuentes del mercado laboral panameño
    y guarda el dataset unificado en data/processed/ofertas.csv.
    Fuentes: Konzerta Panamá, Computrabajo Panamá, dataset CSV Panamá.
    """
    from src.ingesta.loader_dataset import cargar_dataset

    dfs = []

    # Fuente 1: Konzerta Panamá (scraper principal)
    try:
        from src.ingesta.scraper_konzerta import scrapear_konzerta
        ofertas_kz = scrapear_konzerta(max_paginas=5)
        dfs.append(transformar_konzerta(ofertas_kz))
    except Exception as e:
        logger.warning(f"Konzerta no disponible: {e}")

    # Fuente 2: Computrabajo Panamá (si existe el crudo descargado)
    if COMPUTRABAJO_RAW.exists():
        try:
            with open(COMPUTRABAJO_RAW, "r", encoding="utf-8") as f:
                computrabajo_raw = json.load(f)
            dfs.append(transformar_computrabajo(computrabajo_raw))
        except Exception as e:
            logger.warning(f"No se pudo cargar Computrabajo crudo: {e}")

    # Fuente 3: Dataset CSV Panamá (Kaggle u otro CSV local de empleos panameños)
    kaggle_df = cargar_dataset(KAGGLE_EJEMPLO)
    dfs.append(transformar_kaggle(kaggle_df))

    dfs_validos = [d for d in dfs if not d.empty]
    if not dfs_validos:
        logger.warning("Todas las fuentes retornaron datos vacíos. Dataset unificado vacío.")
        df_total = pd.DataFrame(columns=ESQUEMA_COLUMNAS)
    else:
        df_total = pd.concat(dfs_validos, ignore_index=True)
    df_total = eliminar_duplicados_nulos(df_total)

    # Serializar tecnologias como string pipe-separated para CSV
    df_total["tecnologias"] = df_total["tecnologias"].apply(
        lambda x: "|".join(x) if isinstance(x, list) else ""
    )

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_total.to_csv(OFERTAS_CSV, index=False)
    logger.info(f"Dataset unificado: {len(df_total)} filas guardadas en {OFERTAS_CSV}")

    return df_total


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
