import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from scraper import extract_offers, extract_referentials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)
app = FastAPI(title="France Travail Extract API")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/referentials")
def run_referentials_extraction() -> JSONResponse:
    """
    Déclenche l'extraction complète des référentiels France Travail.
    """

    try:
        extract_referentials()
    except ValueError as exc:
        logger.exception("Invalid configuration for referentials extraction.")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Referentials extraction failed.")
        raise HTTPException(
            status_code=500,
            detail="Referentials extraction failed.",
        ) from exc

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "job": "referentials_extraction",
        },
    )


@app.post("/offers")
def run_offers_extraction(mode: str = "prod") -> JSONResponse:
    """
    Déclenche l'extraction complète des offres France Travail.
    """

    try:
        extract_offers(mode=mode)
    except ValueError as exc:
        logger.exception("Invalid configuration for offers extraction.")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Offers extraction failed.")
        raise HTTPException(
            status_code=500,
            detail="Offers extraction failed.",
        ) from exc

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "job": "offers_extraction",
        },
    )
