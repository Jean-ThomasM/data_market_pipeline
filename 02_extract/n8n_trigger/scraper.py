import json
import logging
import re
import time

import requests

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

_MAX_RETRIES = 3
_RETRY_DELAY = 10


def _slugify(name: str) -> str:
    s = name.lower().strip()
    s = s.replace("'", "-").replace("&", "-")
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    return s


def _extract_jsonld(html: str) -> dict | None:
    for match in re.finditer(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    ):
        raw = match.group(1).strip()
        raw = re.sub(r"^\s*//<!\[CDATA\[|\s*//\]\]>\s*$", "", raw).strip()
        raw = raw.replace("\\/", "/")
        if '"legalName"' in raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                logger.warning("JSON-LD parse error: %s", e)
    return None


def _extract_dt_dd(html: str, label: str) -> str | None:
    # Normalize whitespace so "Capital\nsocial" matches "Capital social"
    label_normalized = r"\s*".join(re.escape(part) for part in label.split())
    pattern = re.compile(
        rf'<dt[^>]*class="ui-label"[^>]*>.*?{label_normalized}.*?</dt>'
        r"\s*<dd[^>]*>(.*?)</dd>",
        re.DOTALL | re.IGNORECASE,
    )
    m = pattern.search(html)
    if m:
        value = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        value = " ".join(value.split())
        parts = list(dict.fromkeys(value.split()))
        value = " ".join(parts)
        return value if value else None
    return None


def _extract_adstack(html: str) -> dict:
    result = {}
    for m in re.finditer(r"ADSTACK\.data\.(\w+)\s*=\s*([^;]+);", html):
        key = m.group(1)
        val = m.group(2).strip().strip('"')
        if key in ("chiffre", "effectif", "categorie") and val and val != "0":
            result[key] = val
    return result


def _clean_euro(value: str) -> str | None:
    value = value.replace("&euro;", "€")
    m = re.search(r"([\d\s.,]+)\s*€", value)
    if m:
        return m.group(1).strip().replace(" ", "")
    return value.strip()


def parse_societe_html(html: str, siren: str) -> dict | None:
    ld = _extract_jsonld(html)
    if ld is None:
        logger.warning("No JSON-LD found for %s", siren)
        return None

    result: dict = {}

    for id_ in ld.get("identifier", []):
        pid = id_.get("propertyID", "").upper()
        if pid == "SIREN":
            result["siren"] = id_["value"]
        elif pid == "SIRET":
            result["siret_siege"] = id_["value"]
        elif pid == "TVA":
            result["tva_intra"] = id_["value"]

    result["legal_name"] = ld.get("legalName")
    result["naf_code"] = ld.get("naics")
    result["naf_label"] = ld.get("description")
    result["date_creation"] = ld.get("foundingDate")

    addr = ld.get("address", {})
    if addr:
        result["adresse"] = {
            "rue": addr.get("streetAddress"),
            "complement": addr.get("extendedAddress"),
            "code_postal": addr.get("postalCode"),
            "ville": addr.get("addressLocality"),
        }

    for prop in ld.get("additionalProperty", []):
        pid = prop.get("propertyID", "")
        if pid == "Forme juridique":
            result["forme_juridique_code"] = prop.get("value")
        elif pid == "Statut":
            result["statut"] = prop.get("value")

    dirigeants = []
    seen = set()
    for member in ld.get("member", []):
        d = {"nom": member.get("name")}
        if member.get("@type") == "Person":
            d["prenom"] = member.get("givenName")
            d["nom_famille"] = member.get("familyName")
            if member.get("jobTitle"):
                d["fonction"] = member.get("jobTitle")
        elif member.get("@type") == "Organization":
            d["siren"] = member.get("identifier")
            ap = member.get("additionalProperty", {})
            if isinstance(ap, dict) and ap.get("propertyID") == "Fonction":
                d["fonction"] = ap.get("value")
        key = (d["nom"], d.get("fonction"))
        if key not in seen:
            seen.add(key)
            dirigeants.append(d)
    if dirigeants:
        result["dirigeants"] = dirigeants

    capital_raw = _extract_dt_dd(html, "Capital social")
    if capital_raw:
        result["capital_social"] = _clean_euro(capital_raw)

    cc = _extract_dt_dd(html, "Convention collective")
    if cc:
        result["convention_collective"] = cc

    noms = _extract_dt_dd(html, "Noms commerciaux")
    if noms:
        result["noms_commerciaux"] = noms

    for key, label in [
        ("statut_rcs", "Statut RCS"),
        ("statut_insee", "Statut INSEE"),
        ("statut_rne", "Statut RNE"),
    ]:
        val = _extract_dt_dd(html, label)
        if val:
            result[key] = val

    adstack = _extract_adstack(html)
    if adstack.get("chiffre"):
        result["chiffre_affaires"] = adstack["chiffre"]
    if adstack.get("effectif") and adstack["effectif"] != "0":
        result["effectif"] = adstack["effectif"]

    return result


def scrape_societe(siren: str, company_name: str | None = None) -> dict | None:
    slug = _slugify(company_name) if company_name else siren
    url = f"https://www.societe.com/societe/{slug}-{siren}.html"
    logger.info("Scraping %s", url)

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=30)
            if resp.status_code == 429:
                logger.warning(
                    "Rate limited (attempt %d/%d), waiting %ds...",
                    attempt,
                    _MAX_RETRIES,
                    _RETRY_DELAY,
                )
                time.sleep(_RETRY_DELAY)
                continue
            if resp.status_code == 404:
                logger.warning("Not found: %s", url)
                return None
            resp.raise_for_status()

            result = parse_societe_html(resp.text, siren)
            if result is None:
                logger.warning("No JSON-LD found for %s", url)
                return None

            logger.info(
                "Scraped %s (%s): %s",
                result.get("legal_name", "?"),
                siren,
                json.dumps(
                    {k: v for k, v in result.items() if k != "dirigeants"},
                    ensure_ascii=False,
                ),
            )
            return result

        except requests.RequestException as e:
            logger.error("HTTP error for %s: %s", url, e)
            if attempt < _MAX_RETRIES:
                time.sleep(5)
                continue
            return None
        except Exception as e:
            logger.error("Parse error for %s: %s", url, e)
            return None

    return None
