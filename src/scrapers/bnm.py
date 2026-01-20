"""
Bank Negara Malaysia (BNM) Shariah document scraper.
Source: https://www.bnm.gov.my/shariah
"""

from typing import Iterator
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)


class BNMScraper(BaseScraper):
    """
    Scraper for Bank Negara Malaysia Shariah documents.
    
    BNM publishes:
    - Shariah policies
    - Guidelines
    - Circulars
    - Shariah Advisory Council resolutions
    """
    
    # Pages to scrape for PDF documents
    PAGES = [
        "/shariah",
        "/shariah-standards",
        "/islamic-finance/shariah",
    ]
    
    def __init__(self):
        super().__init__(
            source_name="BNM",
            base_url="https://www.bnm.gov.my"
        )
    
    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """
        Find all PDF document URLs from BNM website.
        
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
                
                # Build full URL if relative
                if href.startswith("/"):
                    href = f"{self.base_url}{href}"
                elif not href.startswith("http"):
                    href = f"{self.base_url}/{href}"
                
                # Extract title from link text or parent
                title = link.get_text(strip=True)
                if not title:
                    title = link.get("title", "")
                if not title:
                    parent = link.find_parent(["td", "li", "p"])
                    if parent:
                        title = parent.get_text(strip=True)[:100]
                
                yield href, title


# Allow running as script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = BNMScraper()
    docs = scraper.run(limit=5)  # Test with 5 docs
    for doc in docs:
        print(f"✓ {doc.title or doc.file_path.name}")
