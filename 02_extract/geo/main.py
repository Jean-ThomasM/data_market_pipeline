import logging

from scraper import extract_geo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting GEO batch extraction.")
    extract_geo()
    logger.info("GEO batch extraction completed.")


if __name__ == "__main__":
    main()
