"""
Bank Negara Malaysia (BNM) Shariah document scraper.
Source: https://www.bnm.gov.my/shariah

Uses Playwright to bypass AWS WAF bot protection.
"""

from typing import Iterator
from urllib.parse import urljoin, urlparse
import os
import logging

from .base import BaseScraper, ScrapedDocument, PLAYWRIGHT_AVAILABLE

logger = logging.getLogger(__name__)


class BNMScraper(BaseScraper):
    """
    Scraper for Bank Negara Malaysia Shariah documents.

    BNM publishes:
    - Shariah policies
    - Guidelines
    - Circulars
    - Shariah Advisory Council resolutions

    Note: BNM website is protected by AWS WAF, so we use Playwright
    to bypass bot detection.
    """

    # Pages to scrape for PDF documents
    PAGES = [
        "/banking-islamic-banking",  # Main Islamic banking policy documents
        "/insurance-takaful",  # Takaful insurance
        "/development-financial-institutions",  # Development financial institutions
        "/money-services-business",  # Money services business
        "/intermediaries",  # Financial intermediaries
        "/payment-systems",  # Payment systems
        "/dnfbp",  # Designated Non-Financial Businesses and Professions
        "/regulations/currency",  # Currency regulations
        "/shariah",
        "/islamic-finance/shariah",
        "/regulation/policy-documents/islamic-banking",
        "/regulation/policy-documents/takaful-insurance",
    ]

    def __init__(self):
        super().__init__(
            source_name="BNM",
            base_url="https://www.bnm.gov.my"
        )
        self._use_playwright = PLAYWRIGHT_AVAILABLE

    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """
        Find all PDF document URLs from BNM website.
        Uses Playwright to bypass WAF protection.

        Yields:
            Tuple of (pdf_url, document_title)
        """
        seen_urls = set()

        for page in self.PAGES:
            page_url = f"{self.base_url}{page}"
            logger.info(f"Scanning page: {page_url}")

            try:
                if self._use_playwright:
                    soup = self._get_soup_with_playwright(page_url)
                else:
                    soup = self._get_soup(page_url)
            except Exception as e:
                logger.warning(f"Failed to fetch {page_url}: {e}")
                continue

            # Strategy 1: Find direct PDF links
            for link in soup.find_all("a", href=True):
                href = link["href"]

                # Check if it's a PDF or policy document link
                is_pdf = href.lower().endswith(".pdf")
                is_policy = '/policy-document/' in href.lower() or '/pd/' in href.lower()

                if not (is_pdf or is_policy):
                    continue

                # Build full URL
                full_url = urljoin(page_url, href)

                # Skip duplicates
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Extract title from link text or filename
                title = link.get_text(strip=True)
                if not title or len(title) < 3:
                    title = os.path.basename(urlparse(href).path)
                    title = title.replace('.pdf', '').replace('-', ' ').replace('_', ' ')

                # For policy pages, we need to resolve to actual PDF
                if is_policy and not is_pdf:
                    pdf_info = self._resolve_policy_page(full_url)
                    if pdf_info:
                        yield pdf_info
                else:
                    yield full_url, title

            # Strategy 2: Look for document tables (common in BNM)
            for table in soup.find_all('table'):
                for row in table.find_all('tr'):
                    links = row.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        if not href.lower().endswith('.pdf'):
                            continue

                        full_url = urljoin(page_url, href)

                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)

                        # Try to get title from row text
                        title = row.get_text(strip=True)[:100]
                        if not title:
                            title = link.get_text(strip=True)

                        yield full_url, title

        logger.info(f"Found {len(seen_urls)} unique documents")

    def _resolve_policy_page(self, url: str) -> tuple[str, str] | None:
        """
        For non-PDF policy pages, find the actual PDF download link.
        """
        try:
            if self._use_playwright:
                soup = self._get_soup_with_playwright(url)
            else:
                soup = self._get_soup(url)
        except Exception as e:
            logger.warning(f"Failed to resolve policy page {url}: {e}")
            return None

        # Look for PDF download button/link
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()

            if href.lower().endswith('.pdf') or 'download' in link_text:
                pdf_url = urljoin(url, href)
                title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'Unknown'
                return pdf_url, title

        return None

    def run(self, limit: int | None = None) -> list[ScrapedDocument]:
        """
        Run the scraper and download all documents.
        Overridden to use Playwright for PDF downloads.

        Args:
            limit: Maximum number of documents to download (None = all)

        Returns:
            List of ScrapedDocument objects
        """
        documents = []
        count = 0

        logger.info(f"Starting {self.source} scraper" + (f" (limit: {limit})" if limit else ""))
        logger.info(f"Using Playwright: {self._use_playwright}")

        try:
            for url, title in self.get_document_urls():
                if limit and count >= limit:
                    break

                try:
                    # Use Playwright for downloading if available (WAF bypass)
                    if self._use_playwright:
                        file_path = self._download_pdf_with_playwright(url, title)
                    else:
                        file_path = self._download_pdf(url)

                    if file_path:
                        doc = ScrapedDocument(
                            source=self.source,
                            url=url,
                            file_path=file_path,
                            title=title,
                        )
                        documents.append(doc)
                        count += 1

                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Scraper failed: {e}")
            raise

        logger.info(f"Completed {self.source} scraper. Downloaded {len(documents)} documents.")
        return documents


# Allow running as script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = BNMScraper()
    docs = scraper.run()  # Full scrape - no limit
    for doc in docs:
        print(f"[OK] {doc.title or doc.file_path.name}")
