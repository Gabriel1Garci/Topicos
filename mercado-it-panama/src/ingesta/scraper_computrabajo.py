# src/ingesta/scraper_computrabajo.py
"""
Scraper de Computrabajo Panamá — sección de tecnología/informática.
Respeta buenas prácticas: headers User-Agent realistas, delay entre requests.
Si falla por bloqueo o cambio de estructura, devuelve lista vacía (degradación elegante).
"""
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from src.config import COMPUTRABAJO_RAW, DATA_RAW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.computrabajo.com.pa"
SEARCH_URL = f"{BASE_URL}/empleos-de-informatica-y-sistemas"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-PA,es;q=0.9",
}
DELAY_SEGUNDOS = 1.5


def _extraer_ofertas_de_pagina(html: str) -> list:
    """Parsea el HTML de una página y extrae las ofertas encontradas."""
    soup = BeautifulSoup(html, "lxml")
    ofertas = []

    # Intentar varios selectores (la estructura puede cambiar)
    contenedores = (
        soup.select("article.box_offer") or
        soup.select("div.box_offer") or
        soup.select("[data-id]") or
        soup.select(".js-click-job") or
        soup.select("article[class*='offer']")
    )

    for item in contenedores:
        try:
            titulo_tag = (
                item.select_one("h2 a") or
                item.select_one("h3 a") or
                item.select_one("a[class*='js-o-link']")
            )
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""
            if not titulo:
                continue

            empresa_tag = item.select_one(".tc") or item.select_one("[class*='company']")
            empresa = empresa_tag.get_text(strip=True) if empresa_tag else ""

            ubicacion_tag = item.select_one(".tl") or item.select_one("[class*='location']")
            ubicacion = ubicacion_tag.get_text(strip=True) if ubicacion_tag else "Panamá"

            fecha_tag = item.select_one("time") or item.select_one("[class*='date']")
            fecha = fecha_tag.get("datetime") or (fecha_tag.get_text(strip=True) if fecha_tag else "")

            desc_tag = item.select_one("p") or item.select_one("[class*='description']")
            descripcion = desc_tag.get_text(strip=True) if desc_tag else ""

            ofertas.append({
                "titulo": titulo,
                "empresa": empresa,
                "ubicacion": ubicacion,
                "fecha": fecha,
                "descripcion": descripcion,
                "fuente": "computrabajo",
            })
        except Exception as e:
            logger.debug(f"Error parseando item: {e}")
            continue

    return ofertas


def scrapear_computrabajo(max_paginas: int = 3) -> list:
    """
    Scrapea ofertas IT de Computrabajo Panamá.
    Retorna lista de dicts crudos. Si falla, retorna lista vacía.
    """
    logger.info(f"Iniciando scraping Computrabajo (máx. {max_paginas} páginas)...")
    todas_las_ofertas = []

    try:
        for pagina in range(1, max_paginas + 1):
            url = SEARCH_URL if pagina == 1 else f"{SEARCH_URL}?p={pagina}"
            logger.info(f"Scrapeando página {pagina}: {url}")

            try:
                response = requests.get(url, headers=HEADERS, timeout=20)
                response.raise_for_status()
            except Exception as e:
                logger.warning(f"Página {pagina} falló: {e}. Deteniendo paginación.")
                break

            ofertas_pagina = _extraer_ofertas_de_pagina(response.text)
            logger.info(f"Página {pagina}: {len(ofertas_pagina)} ofertas encontradas.")

            if not ofertas_pagina:
                logger.info("Sin más ofertas. Fin de paginación.")
                break

            todas_las_ofertas.extend(ofertas_pagina)

            if pagina < max_paginas:
                time.sleep(DELAY_SEGUNDOS)

    except Exception as e:
        logger.warning(
            f"Computrabajo falló: {e}. "
            f"Pipeline continúa con {len(todas_las_ofertas)} ofertas parciales."
        )

    if todas_las_ofertas:
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        with open(COMPUTRABAJO_RAW, "w", encoding="utf-8") as f:
            json.dump(todas_las_ofertas, f, ensure_ascii=False, indent=2)
        logger.info(f"Crudo guardado: {len(todas_las_ofertas)} ofertas en {COMPUTRABAJO_RAW}")

    return todas_las_ofertas


if __name__ == "__main__":
    resultado = scrapear_computrabajo(max_paginas=2)
    print(f"Ofertas obtenidas: {len(resultado)}")
    for o in resultado[:3]:
        print(f"  - {o['titulo']} @ {o['empresa']} ({o['ubicacion']})")
