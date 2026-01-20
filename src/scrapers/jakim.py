"""
JAKIM e-Fatwa scraper.
Source: http://www.e-fatwa.gov.my/

JAKIM (Jabatan Kemajuan Islam Malaysia) publishes:
- State fatwas in Malay and Arabic
- Islamic rulings for Malaysia
"""

from typing import Iterator
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)


class JAKIMScraper(BaseScraper):
    """
    Scraper for JAKIM e-Fatwa portal.
    
    Content includes:
    - Muzakarah decisions
    - State fatwa compilations
    - Islamic rulings (Malay/Arabic)
    """
    
    PAGES = [
        "/fatwa-negeri",
        "/muzakarah-jawatankuasa-fatwa-majlis-kebangsaan-bagi-hal-ehwal-ugama-islam-malaysia",
    ]
    
    def __init__(self):
        super().__init__(
            source_name="JAKIM",
            base_url="http://www.e-fatwa.gov.my"
        )
    
    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """
        Find PDF documents from JAKIM e-Fatwa portal.
        
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
            
            # Find PDF links
            for link in soup.find_all("a", href=True):
                href = link["href"]
                
                if not href.lower().endswith(".pdf"):
                    continue
                
                # Build full URL
                if href.startswith("/"):
                    href = f"{self.base_url}{href}"
                elif not href.startswith("http"):
                    href = f"{self.base_url}/{href}"
                
                title = link.get_text(strip=True) or link.get("title", "")
                
                yield href, title


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = JAKIMScraper()
    docs = scraper.run(limit=5)
    for doc in docs:
        print(f"✓ {doc.title or doc.file_path.name}")
