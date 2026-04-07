import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from scraper import extract_geo

logger = logging.getLogger(__name__)
app = FastAPI(title="Geo Extract API")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract")
def run_geo_extraction() -> JSONResponse:
    """Déclenche l'extraction complète des données GEO."""

    try:
        extract_geo()
    except ValueError as exc:
        logger.exception("Invalid configuration for GEO extraction.")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("GEO extraction failed.")
        raise HTTPException(status_code=500, detail="GEO extraction failed.") from exc

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "job": "geo_extraction",
        },
    )
