# syntax=docker/dockerfile:1.7

FROM n8nio/n8n:latest

WORKDIR /app

ENV N8N_PORT=5678 \
    N8N_PROTOCOL=https \
    N8N_SECURE_COOKIE=true \
    N8N_ENDPOINT_HEALTH=health \
    N8N_RUNNERS_ENABLED=false \
    N8N_RESTRICT_FILE_ACCESS_TO=/tmp \
    GENERIC_TIMEZONE=Europe/Paris

COPY societe.com-scraper.json /app/workflows/societe.com-scraper.json
COPY --chmod=0755 entrypoint.sh /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
