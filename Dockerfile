FROM python:3.12-slim-trixie

# Installer uv depuis l'image officielle distroless
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Travailler dans /app
WORKDIR /app

# Copier les fichiers de configuration du projet uv
COPY pyproject.toml uv.lock ./

# Synchroniser les dépendances (production uniquement, pas dev)
RUN uv sync --frozen --no-dev

# Copier le reste du projet
COPY . .

# Commande par défaut : exécuter avec uv run pour utiliser le bon environnement
CMD ["uv", "run", "main.py"]
