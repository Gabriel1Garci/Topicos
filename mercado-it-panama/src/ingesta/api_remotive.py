# src/ingesta/api_remotive.py
"""
Ingesta desde la API pública de Remotive (empleos remotos IT).
No requiere API key. Relevancia: devs panameños pueden aplicar a empleos remotos.
"""
import json
import logging
import requests
from src.config import REMOTIVE_RAW, DATA_RAW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
CATEGORIA_DEFAULT = "software-dev"


def ingerir_remotive(categoria: str = CATEGORIA_DEFAULT) -> list:
    """
    Descarga ofertas IT de la API de Remotive y guarda el JSON crudo.
    Retorna lista de ofertas. Si falla, retorna lista vacía (degradación elegante).
    """
    logger.info(f"Iniciando ingesta desde Remotive (categoría: {categoria})...")
    try:
        params = {"category": categoria}
        headers = {"User-Agent": "MercadoITPanama/1.0 (proyecto universitario UTP)"}
        response = requests.get(REMOTIVE_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        datos = response.json()
        ofertas = datos.get("jobs", [])
        logger.info(f"Remotive: {len(ofertas)} ofertas descargadas.")

        # Guardar crudo
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        with open(REMOTIVE_RAW, "w", encoding="utf-8") as f:
            json.dump(ofertas, f, ensure_ascii=False, indent=2)
        logger.info(f"Crudo guardado en {REMOTIVE_RAW}")

        return ofertas

    except Exception as e:
        logger.warning(f"Remotive falló: {e}. Pipeline continúa con otras fuentes.")
        return []


if __name__ == "__main__":
    resultado = ingerir_remotive()
    print(f"Ofertas obtenidas: {len(resultado)}")
    if resultado:
        print("Ejemplo:", resultado[0].get("title"), "-", resultado[0].get("company_name"))
