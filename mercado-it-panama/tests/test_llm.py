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

def test_generar_resumen_usa_ollama_si_disponible(monkeypatch):
    monkeypatch.setattr(oc, "ollama_disponible", lambda: True)
    monkeypatch.setattr(oc, "generar", lambda prompt: (True, "resumen de prueba"))
    resp = oc.generar_resumen(df_muestra())
    assert resp == "resumen de prueba"

def test_resumen_datos_missing_salario_min():
    """Verifies that resumen_datos degrades gracefully when salario_min column is missing."""
    # Create DataFrame without salario_min column
    df = pd.DataFrame([
        {"titulo": "dev python", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": "python|django", "fuente": "konzerta"},
        {"titulo": "react dev", "empresa": "globex", "ubicacion": "remoto",
         "tecnologias": "react", "fuente": "kaggle"},
    ])
    # Should not raise AttributeError; should return string with "N/D" for salary
    ctx = oc.resumen_datos(df)
    assert isinstance(ctx, str)
    assert "N/D" in ctx
    assert "2" in ctx  # total ofertas
    assert "python" in ctx.lower()


def test_resumen_datos_tecnologias_como_lista():
    """dashboard/app.py parsea `tecnologias` a listas de Python antes de llamar
    al LLM (ver `parsear_techs` en cargar_datos()). _techs_serie debe tolerar
    ese formato y no volcar el repr de la lista (p.ej. "['python', 'django']")."""
    df = pd.DataFrame([
        {"titulo": "dev python", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": ["python", "django"], "salario_min": 1000.0, "salario_max": 2000.0,
         "fuente": "konzerta"},
        {"titulo": "react dev", "empresa": "globex", "ubicacion": "remoto",
         "tecnologias": ["react"], "salario_min": None, "salario_max": None,
         "fuente": "kaggle"},
    ])
    ctx = oc.resumen_datos(df)
    assert "[" not in ctx and "]" not in ctx
    assert "python" in ctx.lower()
    assert "react" in ctx.lower()


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
