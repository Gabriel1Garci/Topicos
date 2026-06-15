import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingesta.loader_dataset import cargar_dataset
from src.config import KAGGLE_EJEMPLO

def test_cargar_dataset_ejemplo():
    """El loader debe retornar DataFrame con columnas mapeadas."""
    df = cargar_dataset(KAGGLE_EJEMPLO)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    for col in ["titulo_raw", "empresa_raw", "ubicacion_raw", "descripcion_raw"]:
        assert col in df.columns, f"Columna '{col}' no encontrada"

def test_cargar_dataset_archivo_inexistente():
    """Si no existe el archivo, retorna DataFrame vacío sin excepción."""
    df = cargar_dataset(Path("ruta/que/no/existe.csv"))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0

def test_cargar_dataset_columnas_mapeadas():
    """Verifica que las columnas del CSV de ejemplo se mapean correctamente."""
    df = cargar_dataset(KAGGLE_EJEMPLO)
    assert "titulo_raw" in df.columns   # viene de "job_title"
    assert "empresa_raw" in df.columns  # viene de "company"
    assert len(df) == 20               # el ejemplo tiene 20 filas
