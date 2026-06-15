import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from unittest.mock import patch, MagicMock

from src.ingesta.scraper_computrabajo import scrapear_computrabajo

def test_scraper_retorna_lista():
    """El scraper siempre retorna lista (puede estar vacía)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """
    <html><body>
    <article class="box_offer">
        <h2><a href="/empleo/python-developer">Python Developer</a></h2>
        <span class="tc">TechCorp Panamá</span>
        <span class="tl">Ciudad de Panamá</span>
        <p>Buscamos developer con Python y Django</p>
    </article>
    </body></html>
    """
    with patch("src.ingesta.scraper_computrabajo.requests.get", return_value=mock_response):
        resultado = scrapear_computrabajo(max_paginas=1)
    assert isinstance(resultado, list)

def test_scraper_falla_con_gracia():
    """Si el sitio falla, retorna lista vacía sin lanzar excepción."""
    with patch("src.ingesta.scraper_computrabajo.requests.get", side_effect=Exception("blocked")):
        resultado = scrapear_computrabajo(max_paginas=1)
    assert resultado == []

def test_scraper_bloqueo_http_403():
    """Si recibe 403, retorna lista vacía sin lanzar excepción."""
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = Exception("403 Forbidden")
    with patch("src.ingesta.scraper_computrabajo.requests.get", return_value=mock_response):
        resultado = scrapear_computrabajo(max_paginas=1)
    assert isinstance(resultado, list)
