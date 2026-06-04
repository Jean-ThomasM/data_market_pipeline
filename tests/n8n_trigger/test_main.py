import importlib.util
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


def test_build_flat_record_keeps_staging_schema_fields():
    module = load_module()
    scraped = {
        "siren": "326820065",
        "siret_siege": "32682006500082",
        "tva_intra": "FR12326820065",
        "legal_name": "SOPRA STERIA GROUP",
        "naf_code": "6202A",
        "naf_label": "Conseil en systemes et logiciels informatiques",
        "date_creation": "1985-01-01",
        "adresse": {
            "rue": "6 avenue Kleber",
            "complement": None,
            "code_postal": "75116",
            "ville": "Paris",
        },
        "forme_juridique_code": "5599",
        "statut": "Active",
        "dirigeants": [{"nom": "Dupont", "fonction": "President"}],
        "capital_social": "1000000",
        "convention_collective": "Syntec",
        "noms_commerciaux": "Sopra Steria",
        "statut_rcs": "Inscrite",
        "statut_insee": "Active",
        "statut_rne": "Inscrite",
        "chiffre_affaires": "100000000",
        "effectif": "10000",
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
        "scraped_at": "2026-06-04T12:00:00+00:00",
        "siret_siege": "32682006500082",
        "tva_intra": "FR12326820065",
        "legal_name": "SOPRA STERIA GROUP",
        "naf_code": "6202A",
        "naf_label": "Conseil en systemes et logiciels informatiques",
        "date_creation": "1985-01-01",
        "adresse_rue": "6 avenue Kleber",
        "adresse_complement": None,
        "adresse_code_postal": "75116",
        "adresse_ville": "Paris",
        "forme_juridique_code": "5599",
        "statut": "Active",
        "dirigeants": [{"nom": "Dupont", "fonction": "President"}],
        "capital_social": "1000000",
        "convention_collective": "Syntec",
        "noms_commerciaux": "Sopra Steria",
        "statut_rcs": "Inscrite",
        "statut_insee": "Active",
        "statut_rne": "Inscrite",
        "chiffre_affaires": "100000000",
        "effectif": "10000",
    }
