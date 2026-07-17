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
