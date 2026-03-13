"""
Scraper France Travail — Offres Data Engineer + Référentiels
Extraction multi-recherches avec dédoublonnage, retry et double stockage (local / GCS).
"""

import os
import re
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field

import requests
from dotenv import load_dotenv

# =============================================================================
# Configuration
# =============================================================================
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("ft_scraper")

# Constantes API
MAX_RESULTS = 3_150
PAGE_SIZE = 150
REQUEST_DELAY = 0.15
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


@dataclass
class Config:
    """Paramètres centralisés, résolus à l'instanciation."""

    client_id: str = field(default_factory=lambda: os.getenv("FT_CLIENT_ID", ""))
    client_secret: str = field(default_factory=lambda: os.getenv("FT_CLIENT_SECRET", ""))
    scope: str = field(
        default_factory=lambda: os.getenv("SCOPE_API_FT_EMPLOI", "api_offresdemploiv2 o2dsoffre")
    )
    gcs_bucket_name: str = field(default_factory=lambda: os.getenv("GCS_BUCKET_NAME", ""))

    token_url: str = (
        "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
        "?realm=%2Fpartenaire"
    )
    offres_base_url: str = (
        "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    )
    referentiels_base_url: str = (
        "https://api.francetravail.io/partenaire/offresdemploi/v2/referentiel"
    )

    local_save_dir_offres: str = field(
        default_factory=lambda: str(
            Path(__file__).resolve().parent.parent / "data" / "france_travail_offres"
        )
    )
    local_save_dir_refs: str = field(
        default_factory=lambda: str(
            Path(__file__).resolve().parent.parent / "data" / "france_travail_referentiels"
        )
    )

    searches: list = field(default_factory=lambda: [
        {"codeROME": os.getenv("FT_ROME_CODE", "M1811")},
        {"motsCles": "data engineer"},
        {"motsCles": "architecte data"},
        {"motsCles": "data ingénieur"},
        {"motsCles": "ingénieur data"},
        {"motsCles": "data architect"},
    ])

    # Référentiels à extraire : endpoint API -> nom du fichier local
    referentiels: dict = field(default_factory=lambda: {
        "metiers": "ref_metiers_rome.json",
        "domaines": "ref_domaines_rome.json",
        "secteursActivites": "ref_secteurs_activites.json",
        "typesContrats": "ref_types_contrats.json",
        "niveauxFormations": "ref_niveaux_formations.json",
        "permis": "ref_permis.json",
        "langues": "ref_langues.json",
    })

    def validate(self) -> None:
        if not self.client_id or not self.client_secret:
            raise ValueError(
                "Les variables FT_CLIENT_ID et FT_CLIENT_SECRET doivent être définies."
            )


# =============================================================================
# Classe de base — Authentification + Stockage partagés
# =============================================================================
class BaseFranceTravailClient:
    """Logique commune : authentification, session, stockage GCS/local."""

    def __init__(self, config: Config, local_dir: str):
        self.config = config
        self.config.validate()
        self.session = requests.Session()
        self.local_dir = local_dir

        self.bucket = self._init_gcs_bucket()
        if not self.bucket:
            os.makedirs(self.local_dir, exist_ok=True)

    # ── GCS (lazy import) ────────────────────────────────────────────────
    def _init_gcs_bucket(self):
        if not self.config.gcs_bucket_name:
            logger.info("💻 Stockage : local (%s)", self.local_dir)
            return None
        try:
            from google.cloud import storage  # noqa: import tardif volontaire

            client = storage.Client()
            bucket = client.bucket(self.config.gcs_bucket_name)
            logger.info("🚀 Stockage : GCS (%s)", self.config.gcs_bucket_name)
            return bucket
        except ImportError:
            logger.warning(
                "⚠️  google-cloud-storage non installé → fallback stockage local."
            )
            os.makedirs(self.local_dir, exist_ok=True)
            return None

    # ── Authentification ─────────────────────────────────────────────────
    def authenticate(self) -> None:
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": self.config.scope,
        }
        try:
            res = requests.post(
                self.config.token_url, data=payload, timeout=REQUEST_TIMEOUT
            )
            res.raise_for_status()
        except requests.RequestException as exc:
            logger.error("❌ Échec d'authentification : %s", exc)
            raise

        token = res.json().get("access_token")
        if not token:
            raise ValueError("Réponse token vide — vérifiez vos credentials.")

        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("✅ Authentification réussie.")

    # ── Sauvegarde générique ─────────────────────────────────────────────
    def _save_json(self, json_str: str, filename: str, gcs_prefix: str) -> None:
        if self.bucket:
            blob = self.bucket.blob(f"{gcs_prefix}/{filename}")
            blob.upload_from_string(json_str, content_type="application/json")
            logger.info("☁️  Sauvegardé sur GCS : %s/%s", gcs_prefix, filename)
        else:
            path = os.path.join(self.local_dir, filename)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(json_str)
            logger.info("💾 Sauvegardé en local : %s", path)

    # ── Nettoyage JSON (caractères invisibles) ───────────────────────────
    @staticmethod
    def sanitize_json(text: str) -> str:
        text = text.replace("\u00a0", " ")
        text = re.sub(r"[\u200B-\u200F\u2028\u2029\uFEFF\u00AD]", "", text)
        return text


# =============================================================================
# 1. Extracteur de Référentiels
# =============================================================================
class ReferentielsExtractor(BaseFranceTravailClient):
    """Télécharge les dictionnaires de données France Travail (1×/mois)."""

    def __init__(self, config: Config):
        super().__init__(config, local_dir=config.local_save_dir_refs)

    # ── Téléchargement d'un référentiel ──────────────────────────────────
    def _fetch_one(self, endpoint: str, filename: str) -> None:
        url = f"{self.config.referentiels_base_url}/{endpoint}"
        logger.info("📥 Téléchargement du référentiel : %s …", endpoint)

        for attempt in range(MAX_RETRIES):
            try:
                res = self.session.get(url, timeout=REQUEST_TIMEOUT)

                if res.status_code in (401, 403):
                    logger.warning("🔑 Token expiré, ré-authentification…")
                    self.authenticate()
                    continue

                if res.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning("⏳ Rate-limited, attente %ss…", wait)
                    time.sleep(wait)
                    continue

                res.raise_for_status()
                data = res.json()

                json_str = self.sanitize_json(
                    json.dumps(data, ensure_ascii=False, indent=2)
                )
                self._save_json(json_str, filename, gcs_prefix="raw_referentiels")
                logger.info(
                    "✅ Référentiel '%s' OK — %s entrées.", endpoint, len(data)
                )
                return

            except requests.RequestException as exc:
                logger.error(
                    "❌ Erreur référentiel '%s' (tentative %s/%s) : %s",
                    endpoint,
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )
                time.sleep(2 ** attempt)

        logger.error("🚨 Abandon du référentiel '%s' après %s tentatives.", endpoint, MAX_RETRIES)

    # ── Point d'entrée ───────────────────────────────────────────────────
    def extract_all(self) -> None:
        self.authenticate()
        for endpoint, filename in self.config.referentiels.items():
            self._fetch_one(endpoint, filename)
            time.sleep(REQUEST_DELAY)
        logger.info("🎉 Extraction des référentiels terminée.")


# =============================================================================
# 2. Scraper des Offres (Multi-Passes + Dédoublonnage)
# =============================================================================
class DataEngineerScraper(BaseFranceTravailClient):
    """Extraction des offres Data Engineer avec dédoublonnage par ID."""

    def __init__(self, config: Config):
        super().__init__(config, local_dir=config.local_save_dir_offres)
        self.unique_offers: dict[str, dict] = {}
        self.total_fetched: int = 0
        self.stats_per_search: dict[str, int] = {}

    # ── Parsing du header Content-Range ──────────────────────────────────
    @staticmethod
    def _parse_total(response: requests.Response) -> int:
        header = response.headers.get("Content-Range", "")
        try:
            return int(header.split("/")[1])
        except (IndexError, ValueError):
            results = response.json().get("resultats", [])
            return len(results)

    # ── Récupération d'une page ──────────────────────────────────────────
    def _fetch_page(self, params: dict, start: int, end: int) -> list[dict]:
        page_params = {**params, "range": f"{start}-{end}"}
        headers = {"Range": f"offres {start}-{end}"}

        for attempt in range(MAX_RETRIES):
            try:
                res = self.session.get(
                    self.config.offres_base_url,
                    params=page_params,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                )

                if res.status_code in (200, 206):
                    return res.json().get("resultats", [])

                if res.status_code in (401, 403):
                    logger.warning("🔑 Token expiré, ré-authentification…")
                    self.authenticate()
                    time.sleep(1)
                    continue

                if res.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning("⏳ Rate-limited, attente %ss…", wait)
                    time.sleep(wait)
                    continue

                logger.warning(
                    "⚠️  HTTP %s pour la plage %s-%s (tentative %s/%s)",
                    res.status_code,
                    start,
                    end,
                    attempt + 1,
                    MAX_RETRIES,
                )
                time.sleep(2 ** attempt)

            except requests.RequestException as exc:
                logger.error(
                    "❌ Erreur réseau plage %s-%s (tentative %s/%s) : %s",
                    start,
                    end,
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )
                time.sleep(2 ** attempt)

        logger.error("🚨 Abandon de la plage %s-%s après %s tentatives.", start, end, MAX_RETRIES)
        return []

    # ── Exécution d'une recherche ────────────────────────────────────────
    def _run_search(self, search_params: dict) -> None:
        label = search_params.get("codeROME") or search_params.get("motsCles", "?")
        logger.info("🚀 --- Recherche : '%s' ---", label)

        params = {**search_params, "sort": 2}

        # Premier appel pour connaître le total
        try:
            first = self.session.get(
                self.config.offres_base_url, params=params, timeout=REQUEST_TIMEOUT
            )
        except requests.RequestException as exc:
            logger.error("❌ Impossible de lancer la recherche '%s' : %s", label, exc)
            return

        if first.status_code == 204:
            logger.info("Aucune offre pour '%s'.", label)
            return

        total = self._parse_total(first)
        logger.info("🔍 %s offres trouvées pour '%s'", total, label)

        limit = min(total, MAX_RESULTS)
        added_this_search = 0

        for start in range(0, limit, PAGE_SIZE):
            end = min(start + PAGE_SIZE - 1, limit - 1)
            offres = self._fetch_page(params, start, end)
            self.total_fetched += len(offres)

            for offre in offres:
                oid = offre.get("id")
                if oid and oid not in self.unique_offers:
                    self.unique_offers[oid] = offre
                    added_this_search += 1

            logger.info(
                "  📄 [%s-%s] +%s offres (unique total : %s)",
                start,
                end,
                len(offres),
                len(self.unique_offers),
            )
            time.sleep(REQUEST_DELAY)

        self.stats_per_search[label] = added_this_search

    # ── Sauvegarde finale ────────────────────────────────────────────────
    def _save(self) -> None:
        if not self.unique_offers:
            logger.warning("Aucune offre à sauvegarder.")
            return

        offres_finales = list(self.unique_offers.values())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"offres_data_market_{timestamp}.json"

        payload = {
            "metadata": {
                "searches_performed": self.config.searches,
                "offers_added_per_search": self.stats_per_search,
                "total_fetched_before_dedup": self.total_fetched,
                "duplicates_removed": self.total_fetched - len(offres_finales),
                "total_unique_offers": len(offres_finales),
                "extracted_at": datetime.now().isoformat(),
            },
            "resultats": offres_finales,
        }

        json_str = self.sanitize_json(
            json.dumps(payload, ensure_ascii=False, indent=2)
        )
        self._save_json(json_str, filename, gcs_prefix="raw_offres")
        logger.info(
            "🧹 Terminé — %s récupérées, %s uniques, %s doublons éliminés.",
            self.total_fetched,
            len(offres_finales),
            self.total_fetched - len(offres_finales),
        )

    # ── Point d'entrée ───────────────────────────────────────────────────
    def run(self) -> None:
        self.authenticate()
        for search in self.config.searches:
            self._run_search(search)
        self._save()


# =============================================================================
# Points d'entrée pour l'orchestrateur
# =============================================================================
def extract_francetravail_offres(output_dir: str | None = None) -> None:
    """Extrait les offres (quotidien)."""
    config = Config()
    if output_dir:
        config.local_save_dir_offres = output_dir
    scraper = DataEngineerScraper(config)
    scraper.run()


def extract_francetravail_referentiels(output_dir: str | None = None) -> None:
    """Extrait les référentiels (mensuel)."""
    config = Config()
    if output_dir:
        config.local_save_dir_refs = output_dir
    extractor = ReferentielsExtractor(config)
    extractor.extract_all()


if __name__ == "__main__":
    extract_francetravail_referentiels()
    print("\n" + "=" * 50 + "\n")
    extract_francetravail_offres()
