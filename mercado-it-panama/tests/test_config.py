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
