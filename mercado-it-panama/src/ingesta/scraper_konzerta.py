# src/ingesta/scraper_konzerta.py
"""
Scraper de Konzerta Panamá — empleos de tecnología/sistemas.
Usa Playwright porque el sitio es SPA (JavaScript rendering).
Respeta robots.txt: no usa parámetros bloqueados (?recientes, ?relevantes).

Selectores reales descubiertos (styled-components, clases dinámicas):
  - Tarjetas: a[href*="/empleos/"]  — cada <a> ES la tarjeta completa
  - Título:   primer h2 dentro de la tarjeta
  - Empresa:  segundo h3 dentro de la tarjeta (el primero es la fecha)
  - Fecha:    primer h3 dentro de la tarjeta
  - Descripción: primer <p> dentro de la tarjeta
  - Ubicación: segunda-última línea del innerText (antes de modalidad)
  - URL:      atributo href (relativo, se convierte a absoluto)
"""
import json
import time
import logging
from src.config import DATA_RAW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.konzerta.com/en-panama/empleos-area-tecnologia-sistemas-y-telecomunicaciones.html"
DOMAIN = "https://www.konzerta.com"
DELAY_SEGUNDOS = 2.0


def _extraer_ofertas_de_pagina(page) -> list:
    """Extrae las ofertas del objeto page de Playwright ya cargado.

    Usa evaluate() para correr JS en el contexto del navegador, evitando
    problemas de encoding en Windows con inner_text() de Python.
    """
    cards_data = page.evaluate("""() => {
        const links = document.querySelectorAll('a[href*="/empleos/"]');
        const results = [];
        links.forEach(link => {
            try {
                const href = link.getAttribute('href') || '';

                // Título: primer h2 dentro de la tarjeta
                const titleEl = link.querySelector('h2');
                const titulo = titleEl ? titleEl.textContent.trim() : '';
                if (!titulo) return;  // tarjeta sin título, ignorar

                // Fecha: primer h3 dentro de la tarjeta
                const h3s = link.querySelectorAll('h3');
                const fecha = h3s.length >= 1 ? h3s[0].textContent.trim() : '';

                // Empresa: segundo h3 dentro de la tarjeta
                const empresa = h3s.length >= 2 ? h3s[1].textContent.trim() : '';

                // Descripción: primer párrafo largo
                const pEls = link.querySelectorAll('p');
                let descripcion = '';
                for (let p of pEls) {
                    const txt = p.textContent.trim();
                    if (txt.length > 30) {
                        descripcion = txt;
                        break;
                    }
                }

                // Ubicación: extraer del innerText, es la línea antes del tipo de modalidad
                const fullText = link.innerText || '';
                const lines = fullText.split('\\n')
                    .map(l => l.trim())
                    .filter(l => l.length > 0);

                // Modalidades conocidas que aparecen al final
                const modalidades = new Set(['Presencial', 'Remoto', 'Híbrido', 'Hibrido', 'Home Office']);
                let ubicacion = '';
                let modalidad = '';
                // Recorrer las últimas líneas buscando ubicación y modalidad
                for (let i = lines.length - 1; i >= 0 && i >= lines.length - 4; i--) {
                    const line = lines[i];
                    if (modalidades.has(line)) {
                        modalidad = line;
                    } else if (!ubicacion && line.includes('Panamá') || line.includes('Panama') || line.includes('Ciudad')) {
                        ubicacion = line;
                        break;
                    } else if (!ubicacion && !modalidades.has(line) && line !== 'Postulación rápida' && line !== 'Postulacion rapida') {
                        // Could be a non-standard location
                        ubicacion = line;
                    }
                }
                if (!ubicacion) ubicacion = 'Panamá';

                results.push({
                    href,
                    titulo,
                    empresa,
                    fecha,
                    descripcion,
                    ubicacion,
                    modalidad
                });
            } catch(e) {
                // Skip malformed cards
            }
        });
        return results;
    }""")

    ofertas = []
    for card in (cards_data or []):
        href = card.get("href", "")
        url = DOMAIN + href if href.startswith("/") else href
        ofertas.append({
            "titulo": card.get("titulo", ""),
            "empresa": card.get("empresa", ""),
            "ubicacion": card.get("ubicacion", "Panamá"),
            "descripcion": card.get("descripcion", ""),
            "fecha": card.get("fecha", ""),
            "modalidad": card.get("modalidad", ""),
            "url": url,
            "fuente": "konzerta",
        })

    return ofertas


def scrapear_konzerta(max_paginas: int = 3) -> list:
    """
    Scrapea empleos IT de Konzerta Panamá.
    Retorna lista de dicts crudos. Si falla, retorna lista vacía.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning(
            "Playwright no instalado. "
            "Ejecutar: pip install playwright && playwright install chromium"
        )
        return []

    logger.info(f"Iniciando scraping Konzerta (máx. {max_paginas} páginas)...")
    todas_las_ofertas = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                extra_http_headers={"Accept-Language": "es-PA,es;q=0.9"},
            )
            page = context.new_page()

            for pagina in range(1, max_paginas + 1):
                url = BASE_URL if pagina == 1 else f"{BASE_URL}?page={pagina}"
                logger.info(f"Scrapeando página {pagina}: {url}")

                try:
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=20000)
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Página {pagina} no cargó: {e}")
                    break

                ofertas_pagina = _extraer_ofertas_de_pagina(page)
                logger.info(f"Página {pagina}: {len(ofertas_pagina)} ofertas encontradas.")

                if not ofertas_pagina:
                    logger.info("Sin más ofertas. Fin de paginación.")
                    break

                todas_las_ofertas.extend(ofertas_pagina)

                if pagina < max_paginas:
                    time.sleep(DELAY_SEGUNDOS)

            browser.close()

    except Exception as e:
        logger.warning(
            f"Konzerta falló: {e}. "
            f"Retornando {len(todas_las_ofertas)} ofertas parciales."
        )

    if todas_las_ofertas:
        DATA_RAW.mkdir(parents=True, exist_ok=True)
        konzerta_raw = DATA_RAW / "konzerta_raw.json"
        with open(konzerta_raw, "w", encoding="utf-8") as f:
            json.dump(todas_las_ofertas, f, ensure_ascii=False, indent=2)
        logger.info(f"Crudo guardado: {len(todas_las_ofertas)} ofertas en {konzerta_raw}")

    return todas_las_ofertas


if __name__ == "__main__":
    resultado = scrapear_konzerta(max_paginas=2)
    print(f"Ofertas obtenidas: {len(resultado)}")
    for o in resultado[:5]:
        print(f"  - {o.get('titulo')} @ {o.get('empresa')} ({o.get('ubicacion')})")
