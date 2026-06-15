# Computrabajo Playwright Scraper — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el scraper de Computrabajo basado en `requests`+BeautifulSoup por uno basado en Playwright que renderice el JavaScript del sitio y obtenga ofertas reales.

**Architecture:** Se sigue el patrón exacto de `scraper_konzerta.py`: `sync_playwright` + `chromium.launch(headless=True)` + `page.evaluate(JS)` para extracción. La función `_extraer_ofertas_de_pagina` pasa a recibir el objeto `page` de Playwright en lugar del HTML crudo.

**Tech Stack:** Python 3.10+, Playwright (ya en requirements.txt), pytest, unittest.mock

---

### Task 1: Actualizar tests para mockear Playwright

**Files:**
- Modify: `tests/test_scraper.py`

Los tests actuales mockean `requests.get`. Tras la migración, deben mockear `sync_playwright`.

- [ ] **Step 1: Reemplazar el contenido de `tests/test_scraper.py`**

```python
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from unittest.mock import patch, MagicMock


def _make_playwright_mock(ofertas_evaluate=None):
    """Construye la cadena de mocks para sync_playwright."""
    if ofertas_evaluate is None:
        ofertas_evaluate = []

    mock_page = MagicMock()
    mock_page.evaluate.return_value = ofertas_evaluate

    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page

    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_p = MagicMock()
    mock_p.chromium.launch.return_value = mock_browser

    mock_pw_cm = MagicMock()
    mock_pw_cm.__enter__ = MagicMock(return_value=mock_p)
    mock_pw_cm.__exit__ = MagicMock(return_value=False)

    return mock_pw_cm


def test_scraper_retorna_lista():
    """El scraper siempre retorna lista (puede estar vacía)."""
    ofertas_fake = [
        {
            "titulo": "Python Developer",
            "empresa": "TechCorp Panamá",
            "ubicacion": "Ciudad de Panamá",
            "fecha": "2026-06-15",
            "descripcion": "Buscamos developer con Python y Django",
        }
    ]
    mock_pw = _make_playwright_mock(ofertas_evaluate=ofertas_fake)

    with patch("src.ingesta.scraper_computrabajo.sync_playwright", return_value=mock_pw):
        from src.ingesta.scraper_computrabajo import scrapear_computrabajo
        resultado = scrapear_computrabajo(max_paginas=1)

    assert isinstance(resultado, list)
    assert len(resultado) == 1
    assert resultado[0]["titulo"] == "Python Developer"
    assert resultado[0]["fuente"] == "computrabajo"


def test_scraper_falla_con_gracia():
    """Si Playwright lanza excepción, retorna lista vacía sin propagar el error."""
    mock_pw_cm = MagicMock()
    mock_pw_cm.__enter__ = MagicMock(side_effect=Exception("playwright crash"))
    mock_pw_cm.__exit__ = MagicMock(return_value=False)

    with patch("src.ingesta.scraper_computrabajo.sync_playwright", return_value=mock_pw_cm):
        from src.ingesta.scraper_computrabajo import scrapear_computrabajo
        resultado = scrapear_computrabajo(max_paginas=1)

    assert resultado == []


def test_scraper_pagina_sin_ofertas_detiene_paginacion():
    """Si una página devuelve lista vacía, no se intenta la siguiente."""
    mock_pw = _make_playwright_mock(ofertas_evaluate=[])  # evaluate devuelve vacío

    with patch("src.ingesta.scraper_computrabajo.sync_playwright", return_value=mock_pw):
        from src.ingesta.scraper_computrabajo import scrapear_computrabajo
        resultado = scrapear_computrabajo(max_paginas=3)

    # Solo debe haber llamado goto una vez (página 1 → vacío → para)
    page = mock_pw.__enter__.return_value.chromium.launch.return_value.new_context.return_value.new_page.return_value
    assert page.goto.call_count == 1
    assert resultado == []
```

- [ ] **Step 2: Ejecutar los tests para confirmar que FALLAN (implementación aún usa requests)**

```powershell
cd mercado-it-panama
.\venv\Scripts\activate
pytest tests/test_scraper.py -v
```

Resultado esperado: los 3 tests fallan con `ImportError` o `AssertionError` porque el módulo aún importa `requests`.

---

### Task 2: Reescribir `scraper_computrabajo.py` con Playwright

**Files:**
- Modify: `src/ingesta/scraper_computrabajo.py`

- [ ] **Step 3: Reemplazar el contenido completo del archivo**

```python
# src/ingesta/scraper_computrabajo.py
"""
Scraper de Computrabajo Panamá — sección de tecnología/informática.
Usa Playwright porque el sitio renderiza ofertas con JavaScript.
Si falla por bloqueo o cambio de estructura, devuelve lista vacía (degradación elegante).
"""
import json
import time
import logging
from playwright.sync_api import sync_playwright
from src.config import COMPUTRABAJO_RAW, DATA_RAW

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.computrabajo.com.pa/empleos-de-informatica-y-sistemas"
DELAY_SEGUNDOS = 1.5
SELECTOR_ESPERA = "article[data-id], div.js-click-job, article.box_offer, article[class*='offer']"


def _extraer_ofertas_de_pagina(page) -> list:
    """Extrae las ofertas del objeto page de Playwright ya cargado."""
    cards_data = page.evaluate("""() => {
        const selectors = [
            'article[data-id]',
            'div.js-click-job',
            'article.box_offer',
            'article[class*="offer"]'
        ];

        let articles = [];
        for (const sel of selectors) {
            const found = document.querySelectorAll(sel);
            if (found.length > 0) {
                articles = Array.from(found);
                break;
            }
        }

        const results = [];
        articles.forEach(art => {
            try {
                const titleEl = (
                    art.querySelector('h2 a') ||
                    art.querySelector('a.js-o-link') ||
                    art.querySelector('h3 a') ||
                    art.querySelector('a[class*="title"]')
                );
                const titulo = titleEl ? titleEl.textContent.trim() : '';
                if (!titulo) return;

                const empresaEl = (
                    art.querySelector('.tc') ||
                    art.querySelector('[class*="company"]') ||
                    art.querySelector('[class*="empresa"]')
                );
                const empresa = empresaEl ? empresaEl.textContent.trim() : '';

                const ubicacionEl = (
                    art.querySelector('.tl') ||
                    art.querySelector('[class*="location"]') ||
                    art.querySelector('[class*="ciudad"]')
                );
                const ubicacion = ubicacionEl ? ubicacionEl.textContent.trim() : 'Panamá';

                const fechaEl = (
                    art.querySelector('time[datetime]') ||
                    art.querySelector('time') ||
                    art.querySelector('[class*="date"]') ||
                    art.querySelector('[class*="fecha"]')
                );
                const fecha = fechaEl
                    ? (fechaEl.getAttribute('datetime') || fechaEl.textContent.trim())
                    : '';

                const descEl = (
                    art.querySelector('p') ||
                    art.querySelector('[class*="description"]') ||
                    art.querySelector('[class*="resumen"]')
                );
                const descripcion = descEl ? descEl.textContent.trim() : '';

                results.push({ titulo, empresa, ubicacion, fecha, descripcion });
            } catch(e) {
                // Tarjeta malformada — ignorar
            }
        });
        return results;
    }""")

    ofertas = []
    for card in (cards_data or []):
        ofertas.append({
            "titulo":      card.get("titulo", ""),
            "empresa":     card.get("empresa", ""),
            "ubicacion":   card.get("ubicacion", "Panamá"),
            "fecha":       card.get("fecha", ""),
            "descripcion": card.get("descripcion", ""),
            "fuente":      "computrabajo",
        })
    return ofertas


def scrapear_computrabajo(max_paginas: int = 3) -> list:
    """
    Scrapea ofertas IT de Computrabajo Panamá con Playwright.
    Retorna lista de dicts crudos. Si falla, retorna lista vacía.
    """
    logger.info(f"Iniciando scraping Computrabajo (máx. {max_paginas} páginas)...")
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
                url = BASE_URL if pagina == 1 else f"{BASE_URL}?p={pagina}"
                logger.info(f"Scrapeando página {pagina}: {url}")

                try:
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=20000)
                    try:
                        page.wait_for_selector(SELECTOR_ESPERA, timeout=10000)
                    except Exception:
                        logger.warning(f"Página {pagina}: selector de ofertas no apareció.")

                except Exception as e:
                    logger.warning(f"Página {pagina} no cargó: {e}. Deteniendo paginación.")
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
            f"Computrabajo falló: {e}. "
            f"Retornando {len(todas_las_ofertas)} ofertas parciales."
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
    for o in resultado[:5]:
        print(f"  - {o['titulo']} @ {o['empresa']} ({o['ubicacion']})")
```

- [ ] **Step 4: Ejecutar los tests para confirmar que PASAN**

```powershell
pytest tests/test_scraper.py -v
```

Resultado esperado:
```
tests/test_scraper.py::test_scraper_retorna_lista                    PASSED
tests/test_scraper.py::test_scraper_falla_con_gracia                 PASSED
tests/test_scraper.py::test_scraper_pagina_sin_ofertas_detiene_paginacion PASSED
```

- [ ] **Step 5: Verificar que el resto de tests del proyecto sigue en verde**

```powershell
pytest --tb=short -q
```

Resultado esperado: todos los tests pasan.

- [ ] **Step 6: Commit**

```powershell
git add src/ingesta/scraper_computrabajo.py tests/test_scraper.py docs/superpowers/
git commit -m "fix: migrar scraper Computrabajo a Playwright para obtener ofertas reales"
```

---

### Task 3: Verificar con el pipeline real

- [ ] **Step 7: Confirmar que playwright tiene el browser instalado**

```powershell
playwright install chromium
```

Si ya estaba instalado, el comando termina sin descargar nada.

- [ ] **Step 8: Correr el pipeline completo y verificar que Computrabajo ahora devuelve ofertas**

```powershell
python run_pipeline.py
```

Resultado esperado: la línea de Computrabajo muestra un número mayor a 0:
```
[2/3] Scrapeando Computrabajo Panama...
      OK Computrabajo: N ofertas   ← debe ser > 0
```

Si el sitio devuelve 0 de todas formas, significa que Computrabajo cambió su estructura HTML. En ese caso revisar los selectores en `_extraer_ofertas_de_pagina` inspeccionando el DOM en el browser con `headless=False` temporalmente.
