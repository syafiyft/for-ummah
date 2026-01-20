# Scrapers module
from .base import BaseScraper
from .bnm import BNMScraper
from .aaoifi import AAOIFIScraper
from .jakim import JAKIMScraper

__all__ = [
    "BaseScraper",
    "BNMScraper",
    "AAOIFIScraper",
    "JAKIMScraper",
]
