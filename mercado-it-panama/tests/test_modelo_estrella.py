# tests/test_modelo_estrella.py
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.procesamiento.modelo_estrella import (
    construir_dim_empresa, construir_dim_ubicacion, construir_dim_fuente,
    construir_dim_tecnologia, construir_dim_cluster, construir_dim_fecha, fecha_a_id,
)

def df_muestra():
    return pd.DataFrame([
        {"titulo": "dev python", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": "python|django", "salario_min": 1000.0, "salario_max": 2000.0,
         "fecha": "2026-05-10", "fuente": "konzerta", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 0},
        {"titulo": "react dev", "empresa": "globex", "ubicacion": "remoto",
         "tecnologias": "react|javascript", "salario_min": None, "salario_max": None,
         "fecha": None, "fuente": "kaggle", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 1},
        {"titulo": "otro python", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": "python", "salario_min": 1500.0, "salario_max": 1500.0,
         "fecha": "2026-05-10", "fuente": "konzerta", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 0},
    ])

def test_dim_empresa_sin_duplicados():
    dim = construir_dim_empresa(df_muestra())
    assert list(dim.columns) == ["id_empresa", "nombre_empresa"]
    assert dim["id_empresa"].is_unique
    assert dim["nombre_empresa"].nunique() == 2  # acme, globex

def test_dim_ubicacion_marca_remoto():
    dim = construir_dim_ubicacion(df_muestra())
    remoto = dim[dim["ubicacion"] == "remoto"]["es_remoto"].iloc[0]
    panama = dim[dim["ubicacion"] == "panamá"]["es_remoto"].iloc[0]
    assert bool(remoto) is True
    assert bool(panama) is False

def test_dim_fuente():
    dim = construir_dim_fuente(df_muestra())
    assert set(dim["fuente"]) == {"konzerta", "kaggle"}
    assert dim["id_fuente"].is_unique

def test_dim_tecnologia_tiene_categoria():
    dim = construir_dim_tecnologia()
    assert set(dim.columns) == {"id_tecnologia", "tecnologia", "categoria"}
    assert (dim["categoria"] != "").all()
    assert dim["id_tecnologia"].is_unique

def test_dim_cluster():
    dim = construir_dim_cluster(df_muestra())
    assert set(dim["id_cluster"]) == {0, 1}

def test_dim_fecha_unica_y_atributos():
    dim = construir_dim_fecha(df_muestra())
    assert dim["id_fecha"].is_unique
    fila = dim[dim["id_fecha"] == 20260510].iloc[0]
    assert fila["anio"] == 2026 and fila["mes"] == 5 and fila["dia"] == 10

def test_fecha_a_id_nulo():
    assert fecha_a_id(None) == -1
    assert fecha_a_id("2026-05-10") == 20260510
