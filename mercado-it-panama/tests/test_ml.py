import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml.analisis import (
    preparar_features_tecnologias,
    aplicar_kmeans,
    aplicar_regresion_salario,
    ejecutar_analisis_completo,
)

@pytest.fixture
def df_test():
    return pd.DataFrame({
        "titulo": ["Python Dev", "React Dev", "AWS Architect", "Java Dev", "Vue Dev",
                   "Django Dev", "Node Dev", "Docker Dev"],
        "tecnologias": [
            "python|django|postgresql",
            "javascript|react|css",
            "aws|docker|kubernetes",
            "java|spring|mysql",
            "javascript|vue|css",
            "python|flask|postgresql",
            "javascript|node.js|mongodb",
            "docker|linux|aws",
        ],
        "salario_min": [3000.0, 2500.0, 5000.0, 2800.0, 2200.0, 2900.0, 2400.0, 4000.0],
        "salario_max": [4500.0, 3500.0, 7000.0, 4000.0, 3500.0, 4000.0, 3500.0, 5500.0],
        "fuente": ["remotive"] * 8,
        "ubicacion": ["Remote", "Panama City", "Remote", "Panama City", "Panama City",
                      "Remote", "Panama City", "Remote"],
        "descripcion": ["backend"] * 8,
    })

def test_preparar_features(df_test):
    X, nombres_cols = preparar_features_tecnologias(df_test)
    assert X.shape[0] == 8
    assert X.shape[1] > 0
    assert isinstance(nombres_cols, list)
    assert len(nombres_cols) > 0

def test_kmeans_retorna_etiquetas(df_test):
    X, nombres = preparar_features_tecnologias(df_test)
    etiquetas, resumen = aplicar_kmeans(X, nombres, n_clusters=2)
    assert len(etiquetas) == 8
    assert isinstance(resumen, dict)
    assert len(resumen) == 2

def test_kmeans_resumen_tiene_techs(df_test):
    X, nombres = preparar_features_tecnologias(df_test)
    etiquetas, resumen = aplicar_kmeans(X, nombres, n_clusters=2)
    for cluster_id, info in resumen.items():
        assert "n_ofertas" in info
        assert "tecnologias_top" in info
        assert isinstance(info["tecnologias_top"], list)

def test_regresion_retorna_none_si_pocos_datos():
    df_pequeño = pd.DataFrame({
        "tecnologias": ["python|django"],
        "salario_min": [3000.0],
        "salario_max": [4000.0],
        "ubicacion": ["Remote"],
    })
    resultado = aplicar_regresion_salario(df_pequeño)
    assert resultado is None

def test_ejecutar_analisis_completo(df_test):
    resultado = ejecutar_analisis_completo(df_test)
    assert "clusters" in resultado
    assert isinstance(resultado["clusters"], dict)
    assert "cluster" in df_test.columns  # debe añadir columna al df
