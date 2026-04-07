"""
Configuration centralisée du pipeline.

Lit les variables d'environnement et retourne des objets de config simples.
Priorité : GCP Secret Manager > .env local
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Charge le .env une seule fois au niveau du projet
load_dotenv()


# ── Dataclasses de configuration ──────────────────────────────────────────


@dataclass(frozen=True)
class GCPCredentials:
    """Identifiants et configuration GCP."""

    project_id: str | None
    use_gcs: bool


@dataclass(frozen=True)
class FranceTravailCredentials:
    """Credentials France Travail."""

    client_id: str
    client_secret: str


@dataclass(frozen=True)
class Paths:
    """Chemins par défaut du pipeline."""

    db_path: str = "data/geo.sqlite"
    geo_json_dir: str = "data/data_geo"
    offres_dir: str = "data/france_travail_offres"
    referentiels_dir: str = "data/france_travail_referentiels"
    sql_geo: str = "sql/geo_views.sql"
    sql_offres: str = "sql/france_travail_offres_views.sql"


# ── Fonctions de chargement ──────────────────────────────────────────────


def load_gcp_config() -> GCPCredentials:
    """
    Charge la config GCP depuis les variables d'environnement.

    Retourne:
        GCPCredentials avec project_id et use_gcs
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or None
    use_gcs = bool(
        os.getenv("GCS_BUCKET_OFFRES")
        or os.getenv("GCS_BUCKET_GEO")
        or os.getenv("GCS_BUCKET_REFERENTIELS")
    )
    return GCPCredentials(project_id=project_id, use_gcs=use_gcs)


def get_gcs_bucket(bucket_type: str) -> str | None:
    """
    Récupère le nom d'un bucket GCS depuis les variables d'environnement.

    Args:
        bucket_type: 'offres', 'geo', 'referentiels', ou 'config'

    Returns:
        Nom du bucket ou None si non configuré
    """
    env_mapping = {
        "offres": "GCS_BUCKET_OFFRES",
        "geo": "GCS_BUCKET_GEO",
        "referentiels": "GCS_BUCKET_REFERENTIELS",
        "config": "GCS_BUCKET_CONFIG",
    }
    env_var = env_mapping.get(bucket_type)
    return os.getenv(env_var) if env_var else None


def load_ft_credentials(project_id: str | None = None) -> FranceTravailCredentials:
    """
    Charge les credentials France Travail.

    Priorité :
    1. GCP Secret Manager (si project_id fourni)
    2. Variables d'environnement .env

    Args:
        project_id: ID du projet GCP (optionnel)

    Returns:
        FranceTravailCredentials

    Raises:
        ValueError: Si les credentials ne sont trouvés nulle part
    """
    # Essayer GCP Secret Manager en premier
    if project_id:
        try:
            from google.cloud import secretmanager

            client = secretmanager.SecretManagerServiceClient()

            def _get_secret(secret_id: str) -> str:
                name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode("UTF-8")

            client_id = _get_secret("ft-client-id")
            client_secret = _get_secret("ft-client-secret")
            return FranceTravailCredentials(
                client_id=client_id, client_secret=client_secret
            )

        except Exception as e:
            # GCP indisponible ou erreur — fallback .env
            print(f"⚠️  GCP Secret Manager indisponible : {e}")

    # Fallback .env
    client_id = os.getenv("FT_CLIENT_ID")
    client_secret = os.getenv("FT_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError(
            "Credentials France Travail manquants.\n"
            "Définissez FT_CLIENT_ID et FT_CLIENT_SECRET dans .env\n"
            "ou configurez GOOGLE_CLOUD_PROJECT pour GCP Secret Manager."
        )

    return FranceTravailCredentials(client_id=client_id, client_secret=client_secret)


def load_paths() -> Paths:
    """Retourne les chemins par défaut du pipeline."""
    return Paths()
