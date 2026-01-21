"""
Manual scraper for user-submitted documents.
"""

from typing import Iterator

from .base import BaseScraper


class ManualScraper(BaseScraper):
    """
    Generic scraper for manual ingestion of documents.
    Used when a user provides a direct URL or uploads a file.
    """
    
    def __init__(self):
        super().__init__(
            source_name="Manual",
            base_url="https://manual-upload",
        )
    
    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """Not used for manual scraper."""
        yield from []
