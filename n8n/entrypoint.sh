#!/bin/sh

if [ -f /app/workflows/societe.com-scraper.json ]; then
    echo "Importing societe.com-scraper workflow..."
    n8n import:workflow --input=/app/workflows/societe.com-scraper.json 2>&1 || echo "Warning: workflow import failed."
fi

echo "Starting n8n..."
exec n8n start
