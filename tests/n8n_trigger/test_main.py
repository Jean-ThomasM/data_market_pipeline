import importlib.util
import json
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "02_extract" / "n8n_trigger" / "main.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("n8n_trigger_main", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["n8n_trigger_main"] = module
    spec.loader.exec_module(module)
    return module


def test_call_n8n_webhook_uses_secret_url_and_query_params(monkeypatch, mocker):
    module = load_module()
    monkeypatch.setenv(
        "N8N_WEBHOOK_URL",
        "https://n8n.carthographie.fr/webhook/e35588dd-bf2c-4183-952a-2694ef4a0b95",
    )
    response = mocker.Mock()
    response.json.return_value = {"siren": "326820065", "legal_name": "SOPRA STERIA"}
    get = mocker.patch("n8n_trigger_main.requests.get", return_value=response)

    result = module.call_n8n_webhook("Sopra Steria", "326820065")

    get.assert_called_once_with(
        "https://n8n.carthographie.fr/webhook/e35588dd-bf2c-4183-952a-2694ef4a0b95",
        params={
            "denomination_unite_legales": "Sopra Steria",
            "siren": "326820065",
        },
        timeout=120,
    )
    response.raise_for_status.assert_called_once_with()
    assert result == {"siren": "326820065", "legal_name": "SOPRA STERIA"}


def test_call_n8n_webhook_accepts_single_item_list(monkeypatch, mocker):
    module = load_module()
    monkeypatch.setenv(
        "N8N_WEBHOOK_URL",
        "https://n8n.carthographie.fr/webhook/e35588dd-bf2c-4183-952a-2694ef4a0b95",
    )
    response = mocker.Mock()
    response.json.return_value = [{"company_name": "SOPRA STERIA GROUP"}]
    mocker.patch("n8n_trigger_main.requests.get", return_value=response)

    result = module.call_n8n_webhook("Sopra Steria", "326820065")

    assert result == {"company_name": "SOPRA STERIA GROUP"}


def test_call_n8n_webhook_rejects_empty_list(monkeypatch, mocker):
    module = load_module()
    monkeypatch.setenv("N8N_WEBHOOK_URL", "https://n8n.carthographie.fr/webhook/test")
    response = mocker.Mock()
    response.json.return_value = []
    mocker.patch("n8n_trigger_main.requests.get", return_value=response)

    try:
        module.call_n8n_webhook("Sopra Steria", "326820065")
    except RuntimeError as exc:
        assert str(exc) == "Unexpected n8n response: empty list"
    else:
        raise AssertionError("Expected RuntimeError for empty list payload")


def test_call_n8n_webhook_rejects_multiple_items(monkeypatch, mocker):
    module = load_module()
    monkeypatch.setenv("N8N_WEBHOOK_URL", "https://n8n.carthographie.fr/webhook/test")
    response = mocker.Mock()
    response.json.return_value = [{"company_name": "A"}, {"company_name": "B"}]
    mocker.patch("n8n_trigger_main.requests.get", return_value=response)

    try:
        module.call_n8n_webhook("Sopra Steria", "326820065")
    except RuntimeError as exc:
        assert str(exc) == "Unexpected n8n response: multiple records returned"
    else:
        raise AssertionError("Expected RuntimeError for multi-item payload")


def test_build_flat_record_keeps_n8n_schema_fields():
    module = load_module()
    scraped = {
        "company_name": "SOPRA STERIA GROUP",
        "url": "https://www.societe.com/societe/sopra-steria-group-326820065.html",
        "legal_form": None,
        "capital": "19689538,00",
        "stated_primary_business_activity": None,
        "type_of_business": None,
        "collective_bargaining_agreement": None,
        "revenue": "1984700000,00",
        "net_results": 176640000,
        "carbon_footprint": "70204 tCO2e",
        "other_reports": [
            {"label": "Gouvernance du secteur", "score": "50/100"},
            {"Année score": "2024", "Score territorial": "B"},
        ],
        "scrapped_at": "2026-06-04T04:26:41.392-04:00",
    }
    offer = {
        "employer_name": "Sopra Steria",
        "nom_commune": "Paris",
        "siren": "326820065",
    }

    record = module.build_flat_record(scraped, offer, "2026-06-04T12:00:00+00:00")

    assert record == {
        "employer_name": "Sopra Steria",
        "nom_commune": "Paris",
        "siren": "326820065",
        "scraped_at": "2026-06-04T04:26:41.392-04:00",
        "company_name": "SOPRA STERIA GROUP",
        "url": "https://www.societe.com/societe/sopra-steria-group-326820065.html",
        "legal_form": None,
        "capital": "19689538,00",
        "stated_primary_business_activity": None,
        "type_of_business": None,
        "collective_bargaining_agreement": None,
        "revenue": "1984700000,00",
        "net_results": 176640000,
        "carbon_footprint": "70204 tCO2e",
        "other_reports_json": json.dumps(
            [
                {"label": "Gouvernance du secteur", "score": "50/100"},
                {"Année score": "2024", "Score territorial": "B"},
            ],
            ensure_ascii=False,
        ),
    }


def test_build_flat_record_uses_runtime_timestamp_when_scrapped_at_missing():
    module = load_module()
    offer = {
        "employer_name": "Sopra Steria",
        "nom_commune": "Paris",
        "siren": "326820065",
    }

    record = module.build_flat_record(
        {"company_name": "SOPRA STERIA GROUP"},
        offer,
        "2026-06-04T12:00:00+00:00",
    )

    assert record["scraped_at"] == "2026-06-04T12:00:00+00:00"
    assert record["other_reports_json"] is None
