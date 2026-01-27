import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(".")

from src.services.ingestion import IngestionService
from src.core import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_reindex_aaoifi():
    """
    Force re-index all PDFs in the data/aaoifi directory.
    """
    data_dir = Path("data/aaoifi")
    if not data_dir.exists():
        logger.error(f"Directory not found: {data_dir}")
        return

    ingestion_service = IngestionService()
    
    # Get all PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in data/aaoifi")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to re-index.")

    for pdf_file in pdf_files:
        try:
            logger.info(f"Re-indexing: {pdf_file.name}")
            
            # Construct a dummy or original URL. 
            # Ideally we'd map this back to the real URL, but for re-indexing 
            # validation, the source URL in the DB is sufficient. 
            # If we don't pass one, ingestion might complain or use a default.
            # We'll use a placeholder or try to infer.
            # For this verification specific to the user's request, 
            # we know it comes from the scraping we just did.
            
            # Since we just verified the download with the scraper,
            # we can roughly simulate the scraper's metadata if we want,
            # OR we can just pass a generic Source URL since the file content is what matters for RAG.
            # However, `process_document` updates the record.
            
            # Let's use a generic URL to indicate it's a re-index/manual run
            source_url = f"https://aaoifi.com/e-standards/{pdf_file.name}"

            ingestion_service._process_document(
                file_path=pdf_file,
                source_url=source_url,
                source_name="aaoifi",
                force_reindex=True
            )
            logger.info("Successfully re-indexed.")
            
        except Exception as e:
            logger.error(f"Failed to re-index {pdf_file.name}: {e}")

if __name__ == "__main__":
    force_reindex_aaoifi()
