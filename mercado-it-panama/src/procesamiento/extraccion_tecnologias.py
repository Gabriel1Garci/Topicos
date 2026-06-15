# src/procesamiento/extraccion_tecnologias.py
"""
Extrae tecnologías de texto usando matching de diccionario con regex.
Esta función REEMPLAZA al LLM — requisito del curso no usar modelos generativos.
Usa word boundaries para evitar falsos positivos.
"""
import re
import logging
from src.config import TECH_DICT

logger = logging.getLogger(__name__)

# Pre-compilar los patrones del TECH_DICT una sola vez al importar
_PATRONES_COMPILADOS: dict = {}

# Detecta si una cadena ya contiene metacaracteres regex
_REGEX_META = re.compile(r'[\\.*+?^${}()|[\]]')

# Detecta si el patrón empieza con un carácter no-palabra escapado (ej. \. para punto)
# En ese caso no se añade \b al inicio porque \b requiere borde palabra/no-palabra
_STARTS_ESCAPED_NONWORD = re.compile(r'^\\[^wWbBdDsS]')
_ENDS_ESCAPED_NONWORD = re.compile(r'\\[^wWbBdDsS]$')


def _compilar_patrones():
    for tech_nombre, variantes in TECH_DICT.items():
        patrones = []
        for variante in variantes:
            # Si la variante ya tiene metacaracteres regex (\b, ., *, +, etc.) no aplicar re.escape
            if _REGEX_META.search(variante):
                # Ya tiene \b explícito: usar directamente
                if variante.startswith(r"\b") or variante.startswith("\\b"):
                    patron = variante
                else:
                    # Determinar si añadir \b en cada extremo
                    # No añadir \b si el extremo empieza/termina con carácter no-palabra escapado
                    lead = "" if _STARTS_ESCAPED_NONWORD.match(variante) else r"\b"
                    trail = "" if _ENDS_ESCAPED_NONWORD.search(variante) else r"\b"
                    patron = f"{lead}{variante}{trail}"
            else:
                patron = rf"\b{re.escape(variante)}\b"
            try:
                patrones.append(re.compile(patron, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Patrón inválido para '{tech_nombre}': {patron} — {e}")
        _PATRONES_COMPILADOS[tech_nombre] = patrones


_compilar_patrones()


def extraer_tecnologias(texto) -> list:
    """
    Busca tecnologías en el texto usando el diccionario maestro de config.py.
    Matching case-insensitive. Retorna lista de nombres canónicos sin duplicados.
    """
    if not texto:
        return []
    texto = str(texto)
    encontradas = []
    for tech_nombre, patrones in _PATRONES_COMPILADOS.items():
        for patron in patrones:
            if patron.search(texto):
                encontradas.append(tech_nombre)
                break
    return encontradas
