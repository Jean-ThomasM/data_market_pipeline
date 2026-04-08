FROM python:3.12-slim-trixie

# Installer uv depuis l'image officielle distroless
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Travailler dans /app
WORKDIR /app

# Copier les fichiers de configuration du projet uv
COPY pyproject.toml .

# Synchroniser les dépendances dans un environnement virtuel local (.venv)
RUN uv sync

# Activer l'environnement virtuel par défaut
ENV PATH="/app/.venv/bin:$PATH"

# Copier le reste du projet
COPY . .

# Commande par défaut : exécuter le point d'entrée principal via l'env .venv
CMD ["python", "main.py"]

