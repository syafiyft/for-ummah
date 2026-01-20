"""
AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) scraper.
Source: https://aaoifi.com/

Note: AAOIFI standards are primarily in Arabic with English translations.
This scraper focuses on publicly available documents.
"""

from typing import Iterator
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)


class AAOIFIScraper(BaseScraper):
    """
    Scraper for AAOIFI Shariah standards.
    
    AAOIFI publishes:
    - Shariah Standards (Arabic primary)
    - Accounting Standards
    - Governance Standards
    - Ethics Standards
    """
    
    PAGES = [
        "/shariah-standards/",
        "/standards/",
    ]
    
    def __init__(self):
        super().__init__(
            source_name="AAOIFI",
            base_url="https://aaoifi.com"
        )
    
    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """
        Find all PDF document URLs from AAOIFI website.
        
        Note: AAOIFI may have some documents behind login.
        This scrapes publicly available documents only.
        
        Yields:
            Tuple of (pdf_url, document_title)
        """
        for page in self.PAGES:
            page_url = f"{self.base_url}{page}"
            logger.info(f"Scanning page: {page_url}")
            
            try:
                soup = self._get_soup(page_url)
            except Exception as e:
                logger.warning(f"Failed to fetch {page_url}: {e}")
                continue
            
            # Find all PDF links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                
                if not href.lower().endswith(".pdf"):
                    continue
                
                # Build full URL
                if href.startswith("/"):
                    href = f"{self.base_url}{href}"
                elif not href.startswith("http"):
                    href = f"{self.base_url}/{href}"
                
                # Get title
                title = link.get_text(strip=True) or link.get("title", "")
                
                yield href, title


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = AAOIFIScraper()
    docs = scraper.run(limit=5)
    for doc in docs:
        print(f"✓ {doc.title or doc.file_path.name}")
