import logging
import time

import requests

from config import Config

logger = logging.getLogger(__name__)


def get_token(config: Config) -> str:
    payload = {
        "grant_type": "client_credentials",
        "client_id": config.ft_client_id,
        "client_secret": config.ft_client_key,
        "scope": config.scope,
    }
    logger.info("Requesting France Travail access token.")
    start_time = time.monotonic()
    res = requests.post(config.token_url, data=payload, timeout=30)
    res.raise_for_status()
    token = res.json().get("access_token")
    if not token:
        raise ValueError("Réponse token vide - vérifiez vos credentials.")

    logger.info(
        "France Travail access token retrieved in %.2f seconds.",
        time.monotonic() - start_time,
    )
    return token


def create_authenticated_session(config: Config) -> requests.Session:
    session = requests.Session()
    access_token = get_token(config)
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    logger.info("Authenticated France Travail session initialized.")
    return session


def refresh_access_token(session: requests.Session, config: Config) -> None:
    logger.info("Refreshing France Travail access token.")
    access_token = get_token(config)
    session.headers.update({"Authorization": f"Bearer {access_token}"})
