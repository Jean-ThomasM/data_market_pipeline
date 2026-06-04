import logging
import time
import unicodedata
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://recherche-entreprises.api.gouv.fr"
MIN_DELAY = 0.15
_last_call: float = 0.0


def _rate_limit() -> None:
    global _last_call
    elapsed = time.monotonic() - _last_call
    if elapsed < MIN_DELAY:
        time.sleep(MIN_DELAY - elapsed)
    _last_call = time.monotonic()


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _normalize(s: str | None) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


def _best_match(results: list[dict], city: str | None) -> dict[str, Any] | None:
    if not results:
        return None
    if not city:
        return _flatten_result(results[0])
    city_norm = _normalize(city)
    for r in results:
        siege = r.get("siege", {}) or {}
        rc = _normalize(siege.get("libelle_commune", ""))
        if rc == city_norm:
            return _flatten_result(r)
    for r in results:
        siege = r.get("siege", {}) or {}
        rc = _normalize(siege.get("libelle_commune", ""))
        if city_norm in rc or rc in city_norm:
            return _flatten_result(r)
    return _flatten_result(results[0])


def _flatten_result(item: dict[str, Any]) -> dict[str, Any]:
    siege = item.get("siege", {}) or {}
    dirigeants = item.get("dirigeants", [])
    finances = item.get("finances", {}) or {}
    complements = item.get("complements", {}) or {}
    result = {
        "siren": item.get("siren"),
        "siret_siege": siege.get("siret"),
        "nom_complet": item.get("nom_complet"),
        "nom_raison_sociale": item.get("nom_raison_sociale"),
        "sigle": item.get("sigle"),
        "nature_juridique": item.get("nature_juridique"),
        "categorie_entreprise": item.get("categorie_entreprise"),
        "activite_principale": item.get("activite_principale"),
        "section_activite_principale": item.get("section_activite_principale"),
        "tranche_effectif_salarie": item.get("tranche_effectif_salarie"),
        "annee_tranche_effectif_salarie": item.get("annee_tranche_effectif_salarie"),
        "caractere_employeur": item.get("caractere_employeur"),
        "etat_administratif": item.get("etat_administratif"),
        "statut_diffusion": item.get("statut_diffusion"),
        "date_creation": item.get("date_creation"),
        "date_fermeture": item.get("date_fermeture"),
        "date_mise_a_jour": item.get("date_mise_a_jour"),
        "date_mise_a_jour_insee": item.get("date_mise_a_jour_insee"),
        "date_mise_a_jour_rne": item.get("date_mise_a_jour_rne"),
        "nombre_etablissements": item.get("nombre_etablissements"),
        "nombre_etablissements_ouverts": item.get("nombre_etablissements_ouverts"),
        "adresse": {
            "numero_voie": siege.get("numero_voie"),
            "type_voie": siege.get("type_voie"),
            "libelle_voie": siege.get("libelle_voie"),
            "complement_adresse": siege.get("complement_adresse"),
            "code_postal": siege.get("code_postal"),
            "libelle_commune": siege.get("libelle_commune"),
            "code_commune": siege.get("commune"),
        },
        "coordonnees": siege.get("coordonnees"),
        "latitude": _safe_float(siege.get("latitude")),
        "longitude": _safe_float(siege.get("longitude")),
        "region": siege.get("region"),
        "departement": siege.get("departement"),
        "epci": siege.get("epci"),
        "liste_idcc": siege.get("liste_idcc"),
        "dirigeants": [
            {
                "nom": d.get("nom"),
                "prenoms": d.get("prenoms"),
                "annee_de_naissance": d.get("annee_de_naissance"),
                "qualite": d.get("qualite"),
                "type_dirigeant": d.get("type_dirigeant"),
                "denomination": d.get("denomination"),
                "siren": d.get("siren"),
            }
            for d in dirigeants
        ],
        "finances": {
            year: {"ca": info.get("ca"), "resultat_net": info.get("resultat_net")}
            for year, info in finances.items()
        },
        "egapro_renseignee": complements.get("egapro_renseignee"),
        "est_ess": complements.get("est_ess"),
        "est_association": complements.get("est_association"),
        "est_societe_mission": complements.get("est_societe_mission"),
        "est_administration": complements.get("est_administration"),
    }
    return {k: v for k, v in result.items() if v is not None}


def _call_api(params: dict) -> dict[str, Any] | None:
    headers = {
        "User-Agent": "DataMarketPipeline/1.0",
        "Accept": "application/json",
    }
    for attempt in range(3):
        try:
            _rate_limit()
            resp = requests.get(
                f"{BASE_URL}/search",
                params=params,
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "5"))
                logger.warning("Rate limited, waiting %ds", retry_after)
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error("API error for params %s: %s", params, e)
            if attempt < 2:
                time.sleep(2**attempt)
                continue
            return None
    return None


def search_by_siren(siren: str) -> dict[str, Any] | None:
    data = _call_api({"q": siren, "per_page": 1})
    if data is None:
        return None
    results = data.get("results", [])
    if not results:
        return None
    return _flatten_result(results[0])


def search_by_name_city(name: str, city: str | None = None) -> dict[str, Any] | None:
    if not name or not name.strip():
        return None
    q = f"{name} {city}".strip() if city else name.strip()
    data = _call_api({"q": q, "per_page": 10})
    if data is None:
        return None
    return _best_match(data.get("results", []), city)
