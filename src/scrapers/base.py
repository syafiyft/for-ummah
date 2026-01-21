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
import hashlib
import re
import time

import requests
from bs4 import BeautifulSoup

from src.core import settings
from src.core.exceptions import ScraperError

logger = logging.getLogger(__name__)

# Playwright imports (optional - only needed for WAF bypass)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. WAF bypass will not be available.")


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

    def _get_page_with_playwright(self, url: str, wait_time: int = 5000) -> str:
        """
        Fetch a page using Playwright to bypass bot protection (WAF).

        Args:
            url: URL to fetch
            wait_time: Time to wait for page to load (ms)

        Returns:
            Page HTML content
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ScraperError(self.source, "Playwright not installed", url)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                # Navigate and wait for network to be idle
                page.goto(url, wait_until="networkidle", timeout=60000)

                # Additional wait for any JavaScript challenges
                page.wait_for_timeout(wait_time)

                # Get the page content
                content = page.content()

            except PlaywrightTimeout:
                logger.warning(f"Timeout loading {url}")
                content = ""
            finally:
                browser.close()

        return content

    def _get_soup_with_playwright(self, url: str, wait_time: int = 5000) -> BeautifulSoup:
        """Fetch and parse HTML page using Playwright (for WAF-protected sites)."""
        content = self._get_page_with_playwright(url, wait_time)
        return BeautifulSoup(content, "html.parser")

    def _get_document_hash(self, url: str) -> str:
        """Generate a unique hash for a document URL."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename for filesystem compatibility."""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        # Limit length
        return filename[:100]
    
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

    def _download_pdf_with_playwright(self, url: str, title: str = "") -> Path | None:
        """
        Download a PDF using Playwright to bypass WAF protection.

        Args:
            url: URL of the PDF
            title: Document title for filename

        Returns:
            Path to saved file, or None if download failed
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ScraperError(self.source, "Playwright not installed", url)

        doc_hash = self._get_document_hash(url)
        filename = f"{doc_hash}_{self._sanitize_filename(title)}.pdf" if title else f"{doc_hash}.pdf"
        file_path = self.data_dir / filename

        # Skip if already downloaded and not empty
        if file_path.exists() and file_path.stat().st_size > 0:
            logger.debug(f"Skipping existing file: {filename}")
            return file_path

        # Remove empty file if it exists
        if file_path.exists():
            file_path.unlink()

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    accept_downloads=True
                )
                page = context.new_page()

                # Set up download handling
                with page.expect_download(timeout=60000) as download_info:
                    # Navigate to PDF URL - this triggers the download
                    page.goto(url, timeout=60000)

                download = download_info.value
                # Save the download to our filepath
                download.save_as(str(file_path))
                browser.close()

            # Verify file was downloaded and is not empty
            if file_path.exists() and file_path.stat().st_size > 0:
                logger.info(f"Downloaded: {filename[:50]}...")
                return file_path
            else:
                logger.warning(f"Empty download: {url}")
                return None

        except Exception as e:
            logger.warning(f"Playwright download failed for {url}: {e}")
            # Try fallback with requests (some PDFs might work without WAF)
            return self._download_pdf_fallback(url, file_path)

    def _download_pdf_fallback(self, url: str, file_path: Path) -> Path | None:
        """Fallback download using requests for PDFs that don't need WAF bypass."""
        try:
            response = self.session.get(
                url,
                timeout=settings.request_timeout,
                stream=True
            )
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if file_path.stat().st_size > 0:
                logger.info(f"Downloaded (fallback): {file_path.name[:50]}...")
                return file_path
            return None

        except requests.RequestException as e:
            logger.warning(f"Fallback download failed: {e}")
            return None

    def _sanitize_title_from_url(self, url: str) -> str:
        """
        Extract a clean document title from a URL.
        Removes numeric IDs and cleans up the filename.

        Example:
            Input: https://www.bnm.gov.my/documents/20124/938039/pd_credit+risk_dec2024.pdf
            Output: pd_credit_risk_dec2024
        """
        from urllib.parse import urlparse, unquote

        # Parse URL and get the last path segment
        parsed = urlparse(url)
        path = parsed.path

        # Get filename from path
        filename = path.split("/")[-1]

        # URL decode (+ becomes space, %20 becomes space, etc.)
        filename = unquote(filename.replace("+", " "))

        # Remove .pdf extension
        if filename.lower().endswith(".pdf"):
            filename = filename[:-4]

        # Clean up: replace spaces and special chars with underscores
        clean_title = re.sub(r'[^\w\s-]', '', filename)
        clean_title = re.sub(r'[\s]+', '_', clean_title)

        # Remove leading/trailing underscores
        clean_title = clean_title.strip('_')

        return clean_title if clean_title else "document"

    def _download_with_playwright_sync(self, url: str, file_path: Path) -> bool:
        """
        Internal sync method for Playwright download.
        This is called in a separate thread to avoid blocking asyncio.
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    accept_downloads=True
                )
                page = context.new_page()

                # Set up download handling
                with page.expect_download(timeout=60000) as download_info:
                    page.goto(url, timeout=60000)

                download = download_info.value
                download.save_as(str(file_path))
                browser.close()

            return file_path.exists() and file_path.stat().st_size > 0
        except Exception as e:
            logger.warning(f"Playwright download failed: {e}")
            return False

    def scrape_from_url(self, url: str, custom_title: str | None = None) -> ScrapedDocument | None:
        """
        Download and register a PDF from a direct URL.

        This method allows downloading PDFs from direct URLs without
        crawling a website. Useful for adding specific documents.

        Args:
            url: Direct URL to the PDF file
            custom_title: Optional custom title for the document

        Returns:
            ScrapedDocument if successful, None if failed
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        # Extract clean title from URL if not provided
        title = custom_title or self._sanitize_title_from_url(url)

        # Generate clean filename (no hash prefix for direct URL scraping)
        filename = f"{self._sanitize_filename(title)}.pdf"
        file_path = self.data_dir / filename

        logger.info(f"Scraping from URL: {url}")
        logger.info(f"Target filename: {filename}")

        # Skip if already downloaded and not empty
        if file_path.exists() and file_path.stat().st_size > 0:
            logger.info(f"File already exists: {filename}")
            return ScrapedDocument(
                source=self.source,
                url=url,
                file_path=file_path,
                title=title,
            )

        # Try Playwright first (for WAF bypass)
        if PLAYWRIGHT_AVAILABLE:
            # Check if we're in an asyncio loop (FastAPI context)
            try:
                loop = asyncio.get_running_loop()
                is_async_context = True
            except RuntimeError:
                is_async_context = False

            if is_async_context:
                # Run Playwright in a thread pool to avoid blocking asyncio
                logger.info("Running Playwright in thread pool (async context detected)")
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._download_with_playwright_sync, url, file_path)
                    success = future.result(timeout=120)
            else:
                # Direct call for CLI scripts
                success = self._download_with_playwright_sync(url, file_path)

            if success:
                logger.info(f"Downloaded via Playwright: {filename}")
                return ScrapedDocument(
                    source=self.source,
                    url=url,
                    file_path=file_path,
                    title=title,
                )
            else:
                logger.warning("Playwright download failed, trying fallback...")

        # Fallback to requests
        result = self._download_pdf_fallback(url, file_path)
        if result:
            return ScrapedDocument(
                source=self.source,
                url=url,
                file_path=file_path,
                title=title,
            )

        logger.error(f"Failed to download from URL: {url}")
        return None

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
