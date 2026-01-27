"""
AAOIFI (Accounting and Auditing Organization for Islamic Financial Institutions) scraper.
Source: https://aaoifi.com/e-standards/

Updated to handle the guest access form and English filtering.
"""

from typing import Iterator
import logging
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio

from .base import BaseScraper, ScraperError, PLAYWRIGHT_AVAILABLE

if PLAYWRIGHT_AVAILABLE:
    from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class AAOIFIScraper(BaseScraper):
    """
    Scraper for AAOIFI Shariah standards.
    Targets the specific shariah-standards-3 page and downloads the master PDF.
    """
    
    BASE_URL = "https://aaoifi.com/shariah-standards-3/?lang=en"
    
    # Credentials for guest access
    GUEST_NAME = "Syafiy Rahman"
    GUEST_EMAIL = "syafiyft@gmail.com"
    GUEST_COUNTRY = "Malaysia"
    
    def __init__(self):
        super().__init__(
            source_name="AAOIFI",
            base_url="https://aaoifi.com"
        )
    
    def _extract_pdf_links_with_playwright(self) -> list[tuple[str, str]]:
        """
        Use Playwright to navigate, handle form, and click the main download button.
        """
        links = []
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright is required for this scraper.")
            return []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                logger.info(f"Navigating to {self.BASE_URL}")
                page.goto(self.BASE_URL, timeout=60000)
                
                # Check for Guest Form (Guest Access) if redirected or intercepted
                # Usually AAOIFI might show it before viewing the page OR after clicking download
                # Let's check initially
                if page.locator("input[name='your-name']").count() > 0:
                    logger.info("Guest form detected. Filling credentials...")
                    page.fill("input[name='your-name']", self.GUEST_NAME)
                    page.fill("input[name='your-email']", self.GUEST_EMAIL)
                    
                    if page.locator("select[name='your-country']").count() > 0:
                         page.select_option("select[name='your-country']", label=self.GUEST_COUNTRY)
                    elif page.locator("input[name='your-country']").count() > 0:
                         page.fill("input[name='your-country']", self.GUEST_COUNTRY)
                         
                    page.click("input[type='submit']")
                    page.wait_for_load_state("networkidle")
                    logger.info("Form submitted.")

                # Look for the "Download Shariah standards" button
                # Strategy 1: Specific ID provided by user
                logger.info("Looking for download link with ID 24233...")
                download_btn = page.locator("a[href*='download/24233']")
                
                # Strategy 2: Fallback to text if ID changes
                if download_btn.count() == 0:
                     logger.info("ID strategy failed. Trying text strategy...")
                     download_btn = page.get_by_text("Download Shariah standards", exact=False)

                if download_btn.count() > 0:
                    logger.info("Found download button. Extracting link...")
                    # Get the href directly if it's an anchor (use first if multiple)
                    href = download_btn.first.get_attribute("href")
                    
                    if not href:
                        parent = download_btn.first.locator("..")
                        href = parent.get_attribute("href")

                    if href:
                        full_url = href if href.startswith("http") else f"https://aaoifi.com{href}"
                        title = "AAOIFI Shariah Standards (Full)"
                        links.append((full_url, title))
                    else:
                        logger.warning("Could not extract href from download button.")
                else:
                    logger.warning("Download button not found. Dumping page content snippet for debug...")
                    logger.warning(page.content()[:500]) # Log start of content to see if blocked/redirected
                    
            except Exception as e:
                logger.error(f"Playwright extraction failed: {e}")
            finally:
                browser.close()
                
        return links

    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """
        Find all PDF document URLs from AAOIFI e-standards page.
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ScraperError(self.source, "Playwright not installed, cannot scrape AAOIFI")

        # Run Playwright logic
        # Check context to avoid asyncio issues
        is_async = False
        try:
            asyncio.get_running_loop()
            is_async = True
        except RuntimeError:
            pass

        found_links = []
        if is_async:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._extract_pdf_links_with_playwright)
                found_links = future.result()
        else:
            found_links = self._extract_pdf_links_with_playwright()

        for url, title in found_links:
            yield url, title


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = AAOIFIScraper()
    docs = scraper.run(limit=5)
    for doc in docs:
        print(f"✓ {doc.title}")
