"""
Script to reset the Agent Deen system.
- Clears Pinecone Vector DB
- Deletes local PDF files
- Resets ingestion history
- Resets job status
"""

import sys
import shutil
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.vector_db.pinecone_store import PineconeStore
from src.core import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("⚠️  Starting System Reset... ⚠️")
    
    # 1. Clear Vector DB
    try:
        logger.info("Clearing Pinecone Index...")
        store = PineconeStore()
        store.clear_index()
        logger.info("✅ Pinecone Index cleared.")
    except Exception as e:
        logger.error(f"❌ Failed to clear Pinecone: {e}")
    
    # 2. Delete Local Data
    data_dir = settings.data_dir
    if data_dir.exists():
        logger.info(f"Cleaning data directory: {data_dir}")
        for item in data_dir.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                    logger.info(f"  Deleted dir: {item.name}")
                elif item.is_file() and item.name != ".gitkeep":
                    item.unlink()
                    logger.info(f"  Deleted file: {item.name}")
            except Exception as e:
                logger.error(f"  Failed to delete {item.name}: {e}")
    
    # 3. Re-create empty status files
    from src.services.history import HistoryService
    h_service = HistoryService() # This will re-init the files empty
    h_service.update_job_status("idle", "System Reset Complete", 0.0)
    
    logger.info("✅ System Reset Complete.")
    logger.info("You can now trigger the scraper from the Admin Dashboard.")

if __name__ == "__main__":
    main()
