import json
from pathlib import Path
import sys

import geo_api.geo_decoupage_api as geo
import pytest

# Ajouter dynamiquement la racine du projet au sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def test__get_success_builds_url_and_passes_params(monkeypatch):
    """
    Vérifie que `_get` construit bien l'URL complète à partir de `BASE_URL`
    et qu'il transmet correctement les paramètres à `requests.get`.
    """
    recorded: dict = {}

    def fake_get(url, params=None, timeout=None):
        recorded["url"] = url
        recorded["params"] = params
        recorded["timeout"] = timeout

        class Resp:
            status_code = 200
            text = "ok"

            def raise_for_status(self):
                # Pas d'erreur HTTP
                return None

            def json(self):
                return {"ok": True}

        return Resp()

    # On fixe une base URL contrôlée pour le test
    geo.BASE_URL = "https://example.com"
    monkeypatch.setattr(geo.requests, "get", fake_get)

    result = geo._get("/test", foo="bar")

    assert result == {"ok": True}
    assert recorded["url"] == "https://example.com/test"
    assert recorded["params"] == {"foo": "bar"}
    # On vérifie au passage qu'un timeout est bien fourni
    assert recorded["timeout"] == 15


def test__get_raises_runtime_error_on_http_error(monkeypatch):
    """
    Vérifie que `_get` transforme une `requests.HTTPError` en `RuntimeError`
    avec un message explicite.
    """
    import requests

    def fake_get(url, params=None, timeout=None):
        class Resp:
            status_code = 500
            text = "erreur interne"

            def raise_for_status(self):
                raise requests.HTTPError("boom")

            def json(self):
                return {}

        return Resp()

    monkeypatch.setattr(geo.requests, "get", fake_get)
    geo.BASE_URL = "https://example.com"

    with pytest.raises(RuntimeError) as excinfo:
        geo._get("/test")

    msg = str(excinfo.value)
    assert "Erreur API" in msg
    assert "500" in msg
    assert "/test" in msg


def test_get_regions_uses_correct_path(monkeypatch):
    called = {}

    def fake_get(path: str, **params):
        called["path"] = path
        called["params"] = params
        return [{"code": "84", "nom": "Région test"}]

    monkeypatch.setattr(geo, "_get", fake_get)

    result = geo.get_regions()

    assert result == [{"code": "84", "nom": "Région test"}]
    assert called["path"] == "/regions"
    assert called["params"] == {}


def test_get_departements_uses_correct_path(monkeypatch):
    called = {}

    def fake_get(path: str, **params):
        called["path"] = path
        called["params"] = params
        return [{"code": "69", "nom": "Rhône", "codeRegion": "84"}]

    monkeypatch.setattr(geo, "_get", fake_get)

    result = geo.get_departements()

    assert result == [{"code": "69", "nom": "Rhône", "codeRegion": "84"}]
    assert called["path"] == "/departements"
    assert called["params"] == {}


def test_get_communes_without_fields(monkeypatch):
    called = {}

    def fake_get(path: str, **params):
        called["path"] = path
        called["params"] = params
        return [{"code": "12345", "nom": "Commune test"}]

    monkeypatch.setattr(geo, "_get", fake_get)

    result = geo.get_communes()

    assert result == [{"code": "12345", "nom": "Commune test"}]
    assert called["path"] == "/communes"
    # Sans `fields`, aucun paramètre n'est envoyé
    assert called["params"] == {}


def test_get_communes_with_fields(monkeypatch):
    called = {}

    def fake_get(path: str, **params):
        called["path"] = path
        called["params"] = params
        return [{"code": "12345", "nom": "Commune test", "population": 1000}]

    monkeypatch.setattr(geo, "_get", fake_get)

    fields = "code,nom,population"
    result = geo.get_communes(fields=fields)

    assert result[0]["population"] == 1000
    assert called["path"] == "/communes"
    assert called["params"] == {"fields": fields}


def test_get_epcis_uses_correct_path(monkeypatch):
    called = {}

    def fake_get(path: str, **params):
        called["path"] = path
        called["params"] = params
        return [{"code": "200046977", "nom": "Métropole de Lyon"}]

    monkeypatch.setattr(geo, "_get", fake_get)

    result = geo.get_epcis()

    assert result == [{"code": "200046977", "nom": "Métropole de Lyon"}]
    assert called["path"] == "/epcis"
    assert called["params"] == {}


def test_export_geo_to_json_writes_three_files(tmp_path, monkeypatch):
    """
    Vérifie que `export_geo_to_json` appelle bien les fonctions de récupération
    et écrit les 3 fichiers JSON attendus dans le dossier fourni.
    """

    def fake_get_regions():
        return [{"code": "01", "nom": "Région test"}]

    def fake_get_departements():
        return [{"code": "69", "nom": "Rhône", "codeRegion": "84"}]

    def fake_get_communes(fields=None):
        # On ignore le paramètre `fields` ici, mais on renvoie une structure réaliste
        return [
            {
                "code": "12345",
                "nom": "Commune test",
                "codeRegion": "84",
                "codeDepartement": "69",
                "codesPostaux": ["69001"],
                "population": 1000,
            }
        ]

    monkeypatch.setattr(geo, "get_regions", fake_get_regions)
    monkeypatch.setattr(geo, "get_departements", fake_get_departements)
    monkeypatch.setattr(geo, "get_communes", fake_get_communes)

    output_dir = tmp_path / "data_geo"
    geo.export_geo_to_json(str(output_dir))

    regions_path = output_dir / "regions.json"
    departements_path = output_dir / "departements.json"
    communes_path = output_dir / "communes.json"

    assert regions_path.exists()
    assert departements_path.exists()
    assert communes_path.exists()

    regions_data = json.loads(regions_path.read_text(encoding="utf-8"))
    departements_data = json.loads(departements_path.read_text(encoding="utf-8"))
    communes_data = json.loads(communes_path.read_text(encoding="utf-8"))

    assert regions_data == [{"code": "01", "nom": "Région test"}]
    assert departements_data == [{"code": "69", "nom": "Rhône", "codeRegion": "84"}]
    assert communes_data[0]["code"] == "12345"
    assert communes_data[0]["population"] == 1000
