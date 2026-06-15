import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingesta.api_remotive import ingerir_remotive

def test_ingerir_remotive_devuelve_lista():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "jobs": [
            {
                "id": 1,
                "title": "Python Developer",
                "company_name": "TechCorp",
                "candidate_required_location": "Remote",
                "salary": "USD 3000-4000",
                "publication_date": "2024-01-15T00:00:00",
                "description": "<p>We need Python and Django skills</p>",
                "url": "https://remotive.com/job/1"
            }
        ]
    }
    with patch("src.ingesta.api_remotive.requests.get", return_value=mock_response):
        resultado = ingerir_remotive()
    assert isinstance(resultado, list)
    assert len(resultado) == 1
    assert resultado[0]["title"] == "Python Developer"

def test_ingerir_remotive_falla_con_gracia():
    with patch("src.ingesta.api_remotive.requests.get", side_effect=Exception("timeout")):
        resultado = ingerir_remotive()
    assert resultado == []
