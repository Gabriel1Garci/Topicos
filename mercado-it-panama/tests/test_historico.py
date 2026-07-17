import sys, datetime
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.procesamiento.transformacion import anexar_historico, ESQUEMA_COLUMNAS

def _df_muestra(fecha_scrape):
    return pd.DataFrame([{
        "titulo": "dev python", "empresa": "acme", "ubicacion": "panamá",
        "tecnologias": "python|django", "salario_min": 1000.0, "salario_max": 2000.0,
        "fecha": None, "fuente": "konzerta", "descripcion": "desc",
        "fecha_scrape": fecha_scrape,
    }])

def test_fecha_scrape_en_esquema():
    assert "fecha_scrape" in ESQUEMA_COLUMNAS

def test_anexar_historico_acumula(tmp_path):
    ruta = tmp_path / "hist.csv"
    anexar_historico(_df_muestra("2026-07-16"), ruta=ruta)
    hist = anexar_historico(_df_muestra("2026-07-17"), ruta=ruta)
    assert len(hist) == 2
    assert set(hist["fecha_scrape"]) == {"2026-07-16", "2026-07-17"}
