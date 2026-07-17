# tests/test_modelo_estrella.py
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.procesamiento.modelo_estrella import (
    construir_dim_empresa, construir_dim_ubicacion, construir_dim_fuente,
    construir_dim_tecnologia, construir_dim_cluster, construir_dim_fecha, fecha_a_id,
    construir_fact_y_bridge, construir_modelo_estrella,
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

def test_dim_fecha_columnas_numericas_son_int64_nullable():
    dim = construir_dim_fecha(df_muestra())
    for col in ["anio", "mes", "trimestre", "dia"]:
        assert dim[col].dtype == "Int64"
    fila = dim[dim["id_fecha"] == 20260510].iloc[0]
    assert fila["anio"] == 2026
    centinela = dim[dim["id_fecha"] == -1].iloc[0]
    assert pd.isna(centinela["anio"])


def _dims(df):
    return {
        "dim_empresa": construir_dim_empresa(df),
        "dim_ubicacion": construir_dim_ubicacion(df),
        "dim_fuente": construir_dim_fuente(df),
        "dim_tecnologia": construir_dim_tecnologia(),
        "dim_cluster": construir_dim_cluster(df),
        "dim_fecha": construir_dim_fecha(df),
    }

def test_fact_fks_validas():
    df = df_muestra()
    dims = _dims(df)
    fact, bridge = construir_fact_y_bridge(df, dims)
    assert len(fact) == 3
    assert fact["id_empresa"].isin(dims["dim_empresa"]["id_empresa"]).all()
    assert fact["id_fuente"].isin(dims["dim_fuente"]["id_fuente"]).all()
    # fecha nula → id_fecha_publicacion == -1 (fila 2)
    assert (fact["id_fecha_publicacion"] == -1).sum() == 1

def test_fact_salario_promedio():
    df = df_muestra()
    fact, _ = construir_fact_y_bridge(df, _dims(df))
    fila0 = fact[fact["id_oferta"] == 0].iloc[0]
    assert fila0["salario_promedio"] == 1500.0  # (1000+2000)/2

def test_bridge_cubre_tecnologias():
    df = df_muestra()
    dims = _dims(df)
    _, bridge = construir_fact_y_bridge(df, dims)
    # oferta 0 tiene python+django → 2 filas puente
    assert (bridge["id_oferta"] == 0).sum() == 2
    assert bridge["id_tecnologia"].isin(dims["dim_tecnologia"]["id_tecnologia"]).all()

def test_orquestador_escribe_8_csv(tmp_path):
    tablas = construir_modelo_estrella(df=df_muestra(), salida_dir=tmp_path)
    esperados = ["dim_empresa", "dim_ubicacion", "dim_fuente", "dim_tecnologia",
                 "dim_cluster", "dim_fecha", "fact_ofertas", "bridge_oferta_tecnologia"]
    for nombre in esperados:
        assert (tmp_path / f"{nombre}.csv").exists(), f"falta {nombre}.csv"
        assert nombre in tablas

def test_orquestador_csv_fecha_sin_sufijo_flotante(tmp_path):
    construir_modelo_estrella(df=df_muestra(), salida_dir=tmp_path)
    contenido = (tmp_path / "dim_fecha.csv").read_text(encoding="utf-8")
    assert "2026.0" not in contenido
    assert "2026" in contenido


def test_fact_fks_validas_con_valores_nulos():
    # Reproduce el bug: NaN es truthy en Python, así que `valor or "desconocido"`
    # nunca hace fallback para un NaN real (a diferencia de None o "") y termina
    # convertido en el string literal "nan", que no existe en las dimensiones.
    df = pd.DataFrame([
        {"titulo": "dev con nulos", "empresa": float("nan"), "ubicacion": float("nan"),
         "tecnologias": "python", "salario_min": 1000.0, "salario_max": 2000.0,
         "fecha": "2026-05-10", "fuente": float("nan"), "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 0},
        {"titulo": "dev sin tecnologias", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": float("nan"), "salario_min": 1500.0, "salario_max": 1500.0,
         "fecha": "2026-05-10", "fuente": "konzerta", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 0},
    ])
    dims = _dims(df)
    fact, _ = construir_fact_y_bridge(df, dims)

    assert fact["id_empresa"].isin(dims["dim_empresa"]["id_empresa"]).all()
    assert fact["id_ubicacion"].isin(dims["dim_ubicacion"]["id_ubicacion"]).all()
    assert fact["id_fuente"].isin(dims["dim_fuente"]["id_fuente"]).all()

    fila_nan_tech = fact[fact["id_oferta"] == 1].iloc[0]
    assert fila_nan_tech["num_tecnologias"] == 0


def test_fact_fks_validas_con_string_vacio():
    # `_dim_desde_columna` normaliza "" -> "desconocido" al construir la
    # dimensión (no queda ninguna fila con clave ""), así que
    # `_valor_o_desconocido` debe hacer el mismo fallback para "" real
    # (no NaN, no None); si no, "" nunca matchearía en el mapa y el FK
    # caería a -1 (referencia inexistente).
    df = pd.DataFrame([
        {"titulo": "dev con vacios", "empresa": "", "ubicacion": "",
         "tecnologias": "python", "salario_min": 1000.0, "salario_max": 2000.0,
         "fecha": "2026-05-10", "fuente": "", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 0},
        {"titulo": "dev normal", "empresa": "acme", "ubicacion": "panamá",
         "tecnologias": "python", "salario_min": 1500.0, "salario_max": 1500.0,
         "fecha": "2026-05-10", "fuente": "konzerta", "descripcion": "d",
         "fecha_scrape": "2026-07-16", "cluster": 0},
    ])
    dims = _dims(df)
    fact, _ = construir_fact_y_bridge(df, dims)

    assert fact["id_empresa"].isin(dims["dim_empresa"]["id_empresa"]).all()
    assert fact["id_ubicacion"].isin(dims["dim_ubicacion"]["id_ubicacion"]).all()
    assert fact["id_fuente"].isin(dims["dim_fuente"]["id_fuente"]).all()

    fila_vacia = fact[fact["id_oferta"] == 0].iloc[0]
    assert fila_vacia["id_empresa"] != -1
    assert fila_vacia["id_ubicacion"] != -1
    assert fila_vacia["id_fuente"] != -1
