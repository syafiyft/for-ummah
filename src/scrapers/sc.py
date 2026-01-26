"""
Securities Commission Malaysia (SC) Scraper.
Source: https://www.sc.com.my/regulation/acts
"""

from typing import Iterator
from urllib.parse import urljoin
import logging
from .base import BaseScraper, ScrapedDocument, PLAYWRIGHT_AVAILABLE

logger = logging.getLogger(__name__)

class SCScraper(BaseScraper):
    """
    Scraper for Securities Commission Malaysia.
    Focuses on Acts, Guidelines, and Shariah Resolutions.
    """
    
    BASE_URL = "https://www.sc.com.my"
    START_URLS = [
        "/regulation/acts",
        "/regulation/guidelines",
        "/development/islamic-capital-market/syariah/resolutions-of-the-shariah-advisory-council-of-the-sc"
    ]

    def __init__(self):
        super().__init__(
            source_name="SC_Malaysia", 
            base_url=self.BASE_URL
        )
        self._use_playwright = PLAYWRIGHT_AVAILABLE

    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """
        Scan SC pages for PDF links.
        """
        seen_urls = set()
        
        for partial_path in self.START_URLS:
            page_url = urljoin(self.BASE_URL, partial_path)
            logger.info(f"Scanning SC Page: {page_url}")
            
            try:
                # SC usually fine with requests, but let's use Playwright to be safe/consistent with BNM
                if self._use_playwright:
                    soup = self._get_soup_with_playwright(page_url)
                else:
                    soup = self._get_soup(page_url)
                    
                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    # Check for .pdf extension OR SC download handler
                    is_pdf = href.lower().endswith('.pdf')
                    is_download = 'api/documentms/download.ashx' in href.lower()
                    
                    if is_pdf or is_download:
                        full_url = urljoin(self.BASE_URL, href)
                        
                        if full_url in seen_urls: continue
                        seen_urls.add(full_url)
                        
                        title = link.get_text(strip=True)
                        if not title or len(title) < 5:
                            # Try to find parent text
                            title = link.find_parent('div').get_text(strip=True) if link.find_parent('div') else "Unknown SC Document"
                        
                        # Clean title for filename usage later
                        title = title.replace("\n", " ").strip()
                        
                        yield full_url, title
                        
            except Exception as e:
                logger.warning(f"Error scanning {page_url}: {e}")

    def run(self, limit: int | None = None) -> list[ScrapedDocument]:
        """
        Run SC scraper.
        """
        documents = []
        count = 0
        try:
            for url, title in self.get_document_urls():
                if limit and count >= limit: break
                
                try:
                    if self._use_playwright:
                        file_path = self._download_pdf_with_playwright(url, title)
                    else:
                        # Use title for filename to avoid "download.ashx.pdf"
                        clean_filename = f"{self._sanitize_filename(title)}.pdf"
                        file_path = self._download_pdf(url, filename=clean_filename)
                        
                    if file_path:
                        doc = ScrapedDocument(
                            source=self.source,
                            url=url,
                            file_path=file_path,
                            title=title
                        )
                        documents.append(doc)
                        count += 1
                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
                    
        except Exception as e:
            logger.error(f"SC Scraper failed: {e}")
            
        return documents

# Allow running as script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SCScraper()
    docs = scraper.run(limit=3)
    for doc in docs:
        print(f"[OK] {doc.title}")
