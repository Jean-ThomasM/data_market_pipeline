import logging
import os

from scraper import extract_offers, extract_referentials

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

VALID_TARGETS = {"offers", "referentials", "all"}


def _get_extract_target() -> str:
    target = os.getenv("FT_EXTRACT_TARGET", "offers").strip().lower()
    if target not in VALID_TARGETS:
        valid_targets = ", ".join(sorted(VALID_TARGETS))
        raise ValueError(
            f"FT_EXTRACT_TARGET invalide: '{target}'. Valeurs attendues: {valid_targets}."
        )
    return target


def main() -> None:
    target = _get_extract_target()
    logger.info("Starting France Travail batch extraction with target: %s", target)

    if target in {"referentials", "all"}:
        extract_referentials()

    if target in {"offers", "all"}:
        extract_offers(mode="prod")

    logger.info("France Travail batch extraction completed for target: %s", target)


if __name__ == "__main__":
    main()
