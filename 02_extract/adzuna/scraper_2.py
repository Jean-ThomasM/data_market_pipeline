"""Compatibility module.

The Adzuna extractor now lives in scraper.py because main.py imports scraper.
"""

from scraper import OffersExtractor, extract_offers, main, request_with_retry

__all__ = ["OffersExtractor", "extract_offers", "main", "request_with_retry"]
