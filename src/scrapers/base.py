"""
Base scraper class - DRY principle in action.
All scrapers inherit common functionality from this class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator
import logging
import time

import requests
from bs4 import BeautifulSoup

from src.core import settings
from src.core.exceptions import ScraperError

logger = logging.getLogger(__name__)


@dataclass
class ScrapedDocument:
    """Represents a scraped document with metadata."""
    source: str
    url: str
    file_path: Path
    title: str = ""
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "url": self.url,
            "file_path": str(self.file_path),
            "title": self.title,
            "scraped_at": self.scraped_at.isoformat(),
        }


class BaseScraper(ABC):
    """
    Abstract base class for all document scrapers.
    
    DRY Benefits:
    - Common HTTP request handling with retries
    - Polite crawling (rate limiting)
    - Consistent error handling
    - Unified PDF downloading
    - Shared logging
    
    Each subclass only needs to implement:
    - get_document_urls(): How to find PDF links
    - parse_document_title(): How to extract document titles
    """
    
    def __init__(self, source_name: str, base_url: str):
        """
        Initialize the scraper.
        
        Args:
            source_name: Name of the source (e.g., "BNM", "AAOIFI")
            base_url: Base URL for the website
        """
        self.source = source_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; AgentDeen/1.0; +https://github.com/agent-deen)"
        })
        
        # Setup data directory
        self.data_dir = settings.data_dir / source_name.lower()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized {source_name} scraper. Data dir: {self.data_dir}")
    
    def _request(self, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request with rate limiting and error handling.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests.get
            
        Returns:
            Response object
            
        Raises:
            ScraperError: If request fails
        """
        # Polite crawling - wait between requests
        time.sleep(settings.request_delay)
        
        try:
            response = self.session.get(
                url,
                timeout=settings.request_timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            raise ScraperError(self.source, str(e), url) from e
    
    def _get_soup(self, url: str) -> BeautifulSoup:
        """Fetch and parse HTML page."""
        response = self._request(url)
        return BeautifulSoup(response.text, "html.parser")
    
    def _download_pdf(self, url: str, filename: str | None = None) -> Path:
        """
        Download a PDF file.
        
        Args:
            url: URL of the PDF
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = url.split("/")[-1].split("?")[0]
        
        # Ensure .pdf extension
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        
        # Clean filename
        filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        file_path = self.data_dir / filename
        
        # Skip if already downloaded
        if file_path.exists():
            logger.debug(f"Skipping existing file: {filename}")
            return file_path
        
        logger.info(f"Downloading: {filename}")
        response = self._request(url)
        file_path.write_bytes(response.content)
        
        return file_path
    
    @abstractmethod
    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """
        Discover document URLs from the source.
        
        Yields:
            Tuple of (url, title) for each document
        """
        pass
    
    def run(self, limit: int | None = None) -> list[ScrapedDocument]:
        """
        Run the scraper and download all documents.
        
        Args:
            limit: Maximum number of documents to download (None = all)
            
        Returns:
            List of ScrapedDocument objects
        """
        documents = []
        count = 0
        
        logger.info(f"Starting {self.source} scraper" + (f" (limit: {limit})" if limit else ""))
        
        try:
            for url, title in self.get_document_urls():
                if limit and count >= limit:
                    break
                
                try:
                    file_path = self._download_pdf(url)
                    doc = ScrapedDocument(
                        source=self.source,
                        url=url,
                        file_path=file_path,
                        title=title,
                    )
                    documents.append(doc)
                    count += 1
                    
                except ScraperError as e:
                    logger.warning(f"Failed to download: {e}")
                    continue
                    
        except ScraperError as e:
            logger.error(f"Scraper failed: {e}")
            raise
        
        logger.info(f"Completed {self.source} scraper. Downloaded {len(documents)} documents.")
        return documents
