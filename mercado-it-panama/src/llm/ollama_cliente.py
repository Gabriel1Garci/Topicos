"""
Cliente para Ollama (LLM local). Degrada con elegancia: si Ollama no está
corriendo, las funciones retornan MSG_FALLBACK sin lanzar excepción.
"""
import logging
from collections import Counter
import requests
import pandas as pd

from src.config import OLLAMA_URL, OLLAMA_MODEL, TECH_DICT

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
    return (df.get("tecnologias", pd.Series(dtype=str)).fillna("").astype(str).str.split("|").explode().str.strip())


def resumen_datos(df: pd.DataFrame) -> str:
    """Contexto compacto con estadísticas del dataset para el prompt."""
    techs = _techs_serie(df)
    techs = techs[techs != ""]
    top = Counter(techs).most_common(10)
    top_str = ", ".join(f"{t} ({n})" for t, n in top) or "sin datos"
    sal = pd.to_numeric(df.get("salario_min", pd.Series(dtype=float)), errors="coerce").dropna()
    sal_prom = f"${sal.mean():,.0f}" if len(sal) else "N/D"
    fuentes = ", ".join(sorted(df.get("fuente", pd.Series(dtype=str)).dropna().astype(str).unique()))
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

    # Safe access to fecha_scrape column
    fecha_scrape_col = df_historico.get("fecha_scrape", pd.Series(dtype=str))
    snapshots = sorted(fecha_scrape_col.dropna().astype(str).unique())

    if len(snapshots) < 2:
        return ("Se necesitan al menos 2 snapshots (corridas del pipeline en fechas "
                "distintas) para analizar skills emergentes. Corre el pipeline otro día.")

    def conteo(fecha):
        # Safe access: reindex the boolean mask to align with DataFrame
        mask = (fecha_scrape_col.astype(str) == fecha).reindex(df_historico.index, fill_value=False)
        sub = df_historico[mask]
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
