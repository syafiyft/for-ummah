#!/usr/bin/env python3
"""
Scrape a PDF from a direct URL and index it to the vector database.

Usage:
    python scripts/scrape_url.py "https://www.bnm.gov.my/documents/20124/938039/pd_credit+risk_dec2024.pdf"
    python scripts/scrape_url.py "URL" --title "Custom Document Title"
    python scripts/scrape_url.py "URL" --source SC  # Default is BNM
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scrapers.base import BaseScraper, ScrapedDocument, PLAYWRIGHT_AVAILABLE
from src.processors.pdf_extractor import PDFExtractor
from src.processors.chunker import chunk_with_pages
from src.vector_db.pinecone_store import PineconeStore

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class URLScraper(BaseScraper):
    """
    Simple scraper for downloading PDFs from direct URLs.
    Does not implement get_document_urls as it's not needed for direct URL scraping.
    """

    def __init__(self, source_name: str = "BNM"):
        super().__init__(
            source_name=source_name,
            base_url=""  # Not used for direct URL scraping
        )

    def get_document_urls(self):
        """Not implemented - this scraper uses direct URLs."""
        raise NotImplementedError("Use scrape_from_url() instead")


def scrape_and_index(url: str, source: str = "BNM", title: str | None = None) -> bool:
    """
    Download a PDF from URL, extract text, and index to Pinecone.

    Args:
        url: Direct URL to the PDF
        source: Source name (e.g., BNM, SC, AAOIFI)
        title: Optional custom title

    Returns:
        True if successful, False otherwise
    """
    print("=" * 60)
    print("URL SCRAPER - Download & Index")
    print("=" * 60)
    print(f"URL: {url}")
    print(f"Source: {source}")
    print(f"Playwright available: {PLAYWRIGHT_AVAILABLE}")
    print()

    # Step 1: Download PDF
    print("[1/4] Downloading PDF...")
    scraper = URLScraper(source_name=source)
    doc = scraper.scrape_from_url(url, custom_title=title)

    if not doc:
        print("[ERROR] Failed to download PDF!")
        return False

    print(f"      Downloaded: {doc.file_path.name}")
    print(f"      Title: {doc.title}")

    # Step 2: Extract text with page tracking
    print("\n[2/4] Extracting text...")
    extractor = PDFExtractor()
    result = extractor.extract(doc.file_path)

    if not result.page_texts:
        print(f"      [WARN] No page texts extracted (quality: {result.quality_score:.2f})")
        return False

    print(f"      Extracted {result.pages} pages (quality: {result.quality_score:.2f})")
    print(f"      Language: {result.language.value}")

    # Step 3: Chunk text
    print("\n[3/4] Chunking text...")
    metadata = {
        "source": source,
        "title": doc.title,
        "filename": doc.file_path.name,
        "language": result.language.value,
        "url": url,
    }

    chunks = chunk_with_pages(
        result.page_texts,
        chunk_size=800,
        chunk_overlap=100,
        metadata=metadata,
        total_pages=result.pages,  # For Page X/Total display
    )

    print(f"      Created {len(chunks)} chunks with page numbers (total: {result.pages} pages)")

    # Step 4: Save to JSON backup
    print("\n[4/5] Saving to JSON backup...")
    import json
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save individual document chunks
    doc_json_path = processed_dir / f"{doc.file_path.stem}_chunks.json"
    chunk_dicts = [chunk.to_dict() for chunk in chunks]
    with open(doc_json_path, "w", encoding="utf-8") as f:
        json.dump(chunk_dicts, f, ensure_ascii=False, indent=2)
    print(f"      Saved to: {doc_json_path}")

    # Step 5: Index to Pinecone
    print("\n[5/5] Indexing to Pinecone...")
    store = PineconeStore()
    count = store.add_chunks(iter(chunks))
    print(f"      Indexed {count} chunks!")

    print()
    print("=" * 60)
    print("SUCCESS!")
    print("=" * 60)
    print(f"Document: {doc.title}")
    print(f"File: {doc.file_path}")
    print(f"Chunks indexed: {count}")
    print()
    print("Restart your API server to query the new document:")
    print("  uvicorn src.api.main:app --reload --port 8000")
    print()

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Download a PDF from URL and index it for the AI chatbot"
    )
    parser.add_argument(
        "url",
        help="Direct URL to the PDF file"
    )
    parser.add_argument(
        "--source", "-s",
        default="BNM",
        help="Source name (default: BNM)"
    )
    parser.add_argument(
        "--title", "-t",
        default=None,
        help="Custom document title (default: extracted from URL)"
    )

    args = parser.parse_args()

    success = scrape_and_index(
        url=args.url,
        source=args.source,
        title=args.title,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
