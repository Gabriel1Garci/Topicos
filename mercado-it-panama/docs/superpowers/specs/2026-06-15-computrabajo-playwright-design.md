# Diseño: Scraper Computrabajo con Playwright

**Fecha:** 2026-06-15  
**Archivo afectado:** `src/ingesta/scraper_computrabajo.py`

## Problema

El scraper actual usa `requests` + BeautifulSoup. Computrabajo renderiza sus ofertas con JavaScript, por lo que siempre devuelve 0 resultados.

## Solución

Migrar a Playwright (Opción B) siguiendo el patrón exacto de `scraper_konzerta.py`:

- `sync_playwright` + `chromium.launch(headless=True)`
- `page.wait_for_load_state("networkidle")` para esperar el JS
- `page.wait_for_selector(selector)` para confirmar que las tarjetas cargaron
- `page.evaluate(JS)` para extraer campos en un solo round-trip

## Cambios

- Eliminar `_extraer_ofertas_de_pagina(html: str)` basado en BeautifulSoup
- Reemplazar por `_extraer_ofertas_de_pagina(page)` que recibe objeto Playwright
- Reemplazar `requests.get()` con `page.goto()` en `scrapear_computrabajo()`
- Eliminar import de `requests` y `BeautifulSoup`

## Selectores Computrabajo

| Campo | Selectores (en orden de prioridad) |
|-------|-----------------------------------|
| Contenedor | `article[data-id]`, `div.js-click-job` |
| Título | `h2 a`, `a.js-o-link` |
| Empresa | `.tc` |
| Ubicación | `.tl` |
| Fecha | `time[datetime]` |
| Descripción | `p` dentro del contenedor |

## Output

Sin cambios en el schema de salida: lista de dicts con `titulo`, `empresa`, `ubicacion`, `fecha`, `descripcion`, `fuente: "computrabajo"`. Compatible con el pipeline existente.
