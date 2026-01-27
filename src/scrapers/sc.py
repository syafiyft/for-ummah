"""
Securities Commission Malaysia (SC) Scraper.
Source: https://www.sc.com.my/regulation/acts
"""

from typing import Iterator
from urllib.parse import urljoin
import logging
import json
import re
from bs4 import BeautifulSoup
from .base import BaseScraper, ScrapedDocument, PLAYWRIGHT_AVAILABLE

logger = logging.getLogger(__name__)

class SCScraper(BaseScraper):
    """
    Scraper for Securities Commission Malaysia.
    Focuses on Acts, Guidelines, and Shariah Resolutions.
    """
    
    BASE_URL = "https://www.sc.com.my"
    START_URLS = [
        "/regulation/acts",  # Shariah Standards and Acts
        "/regulation/guidelines", # Guidelines
    ]

    def __init__(self):
        super().__init__(
            source_name="SC_Malaysia", 
            base_url=self.BASE_URL
        )
        self._use_playwright = PLAYWRIGHT_AVAILABLE

    def get_document_urls(self) -> Iterator[tuple[str, str]]:
        """
        Scan SC pages for PDF links, including sub-category pages.
        Uses both DOM scanning and embedded JSON data extraction.
        """
        seen_urls = set()
        category_urls = set()
        
        # Phase 1: Scan main pages for categories and direct files
        for partial_path in self.START_URLS:
            page_url = urljoin(self.BASE_URL, partial_path)
            logger.info(f"Scanning SC Main Page: {page_url}")
            
            try:
                # Get page content
                if self._use_playwright:
                    response = self._get_page_with_playwright(page_url)
                    soup = BeautifulSoup(response, "html.parser")
                    text_content = response
                else:
                    resp = self._request(page_url)
                    text_content = resp.text
                    soup = BeautifulSoup(text_content, "html.parser")
                
                # Strategy A: Extract from embedded JSON (most reliable for SC)
                # Look for $X.PPG = { ... }
                try:
                    import json
                    import re
                    
                    # Robust extraction: Find start and count brackets
                    marker = "$X.PPG"
                    marker_idx = text_content.find(marker)
                    
                    if marker_idx != -1:
                        logger.info(f"Found JSON marker at {marker_idx}")
                        # Find the first opening brace after the marker
                        json_start = text_content.find("{", marker_idx)
                        if json_start != -1:
                            # Count brackets to find the end
                            brace_count = 0
                            json_end = -1
                            
                            for i, char in enumerate(text_content[json_start:], start=json_start):
                                if char == "{":
                                    brace_count += 1
                                elif char == "}":
                                    brace_count -= 1
                                    
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                            
                            if json_end != -1:
                                json_str = text_content[json_start:json_end]
                                try:
                                    top_data = json.loads(json_str)
                                    logger.info(f"Extracted JSON with keys: {list(top_data.keys())}")
                                    
                                    # Search for 'pages' in any of the values
                                    found_pages = False
                                    for key, val in top_data.items():
                                        if isinstance(val, dict) and "pages" in val:
                                            logger.info(f"Found 'pages' inside key: {key}")
                                            data_with_pages = val
                                            
                                            if "0" in data_with_pages["pages"]:
                                                items = data_with_pages["pages"]["0"]
                                                logger.info(f"Found {len(items)} categories in {key}")
                                                
                                                for item in items:
                                                    if "Page Address" in item:
                                                        cat_link = item["Page Address"]
                                                        full_cat_url = urljoin(self.BASE_URL, cat_link)
                                                        if full_cat_url != page_url:
                                                            category_urls.add(full_cat_url)
                                                            logger.info(f"Found Category (JSON): {item.get('Page Name')} -> {full_cat_url}")
                                                found_pages = True
                                    
                                    if not found_pages:
                                        logger.debug("Could not find 'pages' key in any nested object.")
                                            
                                except json.JSONDecodeError as e:
                                    logger.warning(f"JSON decode error: {e}")
                except Exception as e:
                    logger.warning(f"JSON extraction failed for {page_url}: {e}")

                # Strategy B: DOM Scan (Fallback/Supplementary)
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(self.BASE_URL, href)
                    
                    # 1. Check for PDF/Download
                    if self._is_document_link(href):
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            yield full_url, self._extract_title(link)
                            
                    # 2. Check for Sub-Categories (DOM based)
                    elif "/regulation/" in full_url and full_url != page_url:
                        if partial_path in full_url and full_url not in category_urls:
                            category_urls.add(full_url)

            except Exception as e:
                logger.warning(f"Error scanning main page {page_url}: {e}")

        # Ensure critical categories are present if missed
        hardcoded_cats = [
            "https://www.sc.com.my/regulation/guidelines",
            "https://www.sc.com.my/regulation/guidelines/bonds-and-sukuk",
            "https://www.sc.com.my/regulation/guidelines/shariah",
            "https://www.sc.com.my/regulation/guidelines/sustainable-and-responsible-investment",
            "https://www.sc.com.my/regulation/guidelines/digital-assets",
            "https://www.sc.com.my/regulation/guidelines/advertising-and-promotion",
            "https://www.sc.com.my/regulation/guidelines/asset-valuation",
            "https://www.sc.com.my/regulation/guidelines/audit-oversight",
            "https://www.sc.com.my/regulation/guidelines/amla"
        ]
        for hc in hardcoded_cats:
            if hc not in category_urls and hc not in seen_urls:
                category_urls.add(hc)

        # Phase 2: Visit discovered categories
        logger.info(f"Found {len(category_urls)} sub-categories. Deep scanning...")
        
        for cat_url in category_urls:
            logger.info(f"Scanning Category: {cat_url}")
            try:
                # Use Playwright for categories too, as they might be dynamic
                if self._use_playwright:
                    soup = self._get_soup_with_playwright(cat_url)
                else:
                    soup = self._get_soup(cat_url)
                
                # Extract documents from category page
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    # Direct PDF
                    if self._is_document_link(href):
                        full_url = urljoin(self.BASE_URL, href)
                        if full_url not in seen_urls:
                            seen_urls.add(full_url)
                            yield full_url, self._extract_title(link)
                    
                    # Level 2 recursion (e.g. Guidelines -> Bonds -> Specific Bond Type)
                    # Use simple heuristic: if it looks like a sub-page of the current category
                    elif cat_url in urljoin(self.BASE_URL, href):
                         sub_url = urljoin(self.BASE_URL, href)
                         if sub_url != cat_url and sub_url not in seen_urls and sub_url not in category_urls:
                             # We won't go infinitely deep, just one more level for safety
                             logger.info(f"Deep diving into sub-topic: {sub_url}")
                             try: 
                                 sub_soup = self._get_soup(sub_url)
                                 for sub_link in sub_soup.find_all('a', href=True):
                                     if self._is_document_link(sub_link['href']):
                                         full_sub_url = urljoin(self.BASE_URL, sub_link['href'])
                                         if full_sub_url not in seen_urls:
                                             seen_urls.add(full_sub_url)
                                             yield full_sub_url, self._extract_title(sub_link)
                             except Exception: pass

            except Exception as e:
                logger.warning(f"Error scanning category {cat_url}: {e}")

    def _is_document_link(self, href: str) -> bool:
        """Check if href points to a document."""
        href = href.lower()
        return href.endswith('.pdf') or 'api/documentms/download.ashx' in href

    def _extract_title(self, link) -> str:
        """Extract and clean title from link element."""
        title = link.get_text(strip=True)
        if not title or len(title) < 5:
            # Try parent div
            parent = link.find_parent('div')
            title = parent.get_text(strip=True) if parent else ""
        
        return title.replace("\n", " ").strip() or "SC Document"

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
