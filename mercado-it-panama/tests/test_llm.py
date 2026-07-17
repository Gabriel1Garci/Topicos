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
