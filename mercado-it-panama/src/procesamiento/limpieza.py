# src/procesamiento/limpieza.py
"""
Funciones de limpieza: normalización de texto, parseo de salarios,
eliminación de duplicados y registros nulos críticos.
"""
import re
import logging
import pandas as pd
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


class _HTMLStripper(HTMLParser):
    """Extrae texto plano desde HTML."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return " ".join(self.fed)


def limpiar_texto(texto) -> str:
    """Quita HTML, normaliza espacios, convierte a minúsculas. Retorna '' si es None."""
    if texto is None or (isinstance(texto, float)):
        return ""
    texto = str(texto)
    stripper = _HTMLStripper()
    stripper.feed(texto)
    texto = stripper.get_data()
    texto = re.sub(r"\s+", " ", texto).strip().lower()
    return texto


def parsear_salario(salario_str) -> tuple:
    """
    Extrae (salario_min, salario_max) como float desde strings variados.
    Maneja: "B/. 1,500 - 2,000", "USD 3000-4000", "$2500", rangos "2500-4000".
    Retorna (None, None) si no encuentra números válidos.
    """
    if salario_str is None or (isinstance(salario_str, float)):
        return (None, None)

    texto = str(salario_str)
    # Quitar símbolos de moneda y texto, conservar dígitos, puntos, comas, guiones
    texto_limpio = re.sub(r"[^\d\.,\-]", " ", texto)
    texto_limpio = texto_limpio.replace(",", "")

    numeros = re.findall(r"\d+(?:\.\d+)?", texto_limpio)
    numeros = [float(n) for n in numeros if float(n) > 100]  # filtrar años y códigos

    if not numeros:
        return (None, None)
    elif len(numeros) == 1:
        return (numeros[0], numeros[0])
    else:
        return (min(numeros[:2]), max(numeros[:2]))


def eliminar_duplicados_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina filas sin título y filas duplicadas por título+descripción."""
    n_original = len(df)
    df = df.dropna(subset=["titulo"])
    df = df[df["titulo"].str.strip() != ""]
    subset_cols = [c for c in ["titulo", "descripcion"] if c in df.columns]
    if subset_cols:
        df = df.drop_duplicates(subset=subset_cols, keep="first")
    logger.info(f"Limpieza: {n_original} → {len(df)} filas (eliminados {n_original - len(df)})")
    return df.reset_index(drop=True)
