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
    mock_pw = _make_playwright_mock(ofertas_evaluate=[])

    with patch("src.ingesta.scraper_computrabajo.sync_playwright", return_value=mock_pw):
        from src.ingesta.scraper_computrabajo import scrapear_computrabajo
        resultado = scrapear_computrabajo(max_paginas=3)

    page = mock_pw.__enter__.return_value.chromium.launch.return_value.new_context.return_value.new_page.return_value
    assert page.goto.call_count == 1
    assert resultado == []
