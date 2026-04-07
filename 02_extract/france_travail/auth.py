import requests

from config import Config


def get_token(config: Config) -> str:
    payload = {
        "grant_type": "client_credentials",
        "client_id": config.ft_client_id,
        "client_secret": config.ft_client_key,
        "scope": config.scope,
    }
    res = requests.post(config.token_url, data=payload, timeout=30)
    res.raise_for_status()
    token = res.json().get("access_token")
    if not token:
        raise ValueError("Réponse token vide - vérifiez vos credentials.")

    return token


def create_authenticated_session(config: Config) -> requests.Session:
    session = requests.Session()
    access_token = get_token(config)
    session.headers.update({"Authorization": f"Bearer {access_token}"})
    return session


def refresh_access_token(session: requests.Session, config: Config) -> None:
    access_token = get_token(config)
    session.headers.update({"Authorization": f"Bearer {access_token}"})
