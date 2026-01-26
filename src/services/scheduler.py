from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
import threading

from src.scrapers.bnm import BNMScraper
from src.services.ingestion import IngestionService
from src.services.history import HistoryService

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def run_daily_update(sources: list[str] = None):
    """
    Job to run the daily update process.
    Scrapes BNM and other sources, then ingests new documents.
    """
    job_id = f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"[{job_id}] Starting automated update job...")
    
    history_service = HistoryService()
    history_service.update_job_status("running", "Starting update job...", 0.1)
    
    # Default sources if None
    if not sources:
        sources = ["BNM"]

    try:
        total_docs = 0
        
        # --- 1. BNM SCRAPER ---
        if "BNM" in sources:
            history_service.update_job_status("running", "Scraping Bank Negara Malaysia...", 0.2)
            try:
                scraper = BNMScraper()
                logger.info(f"[{job_id}] Running BNM Scraper...")
                documents = scraper.run(limit=5)
                
                # Ingest
                _ingest_documents(documents, history_service, job_id, 0.3, 0.5)
                total_docs += len(documents)
            except Exception as e:
                logger.error(f"BNM Scraper failed: {e}")

        # --- 2. SC MALAYSIA SCRAPER ---
        if "SC" in sources:
            from src.scrapers.sc import SCScraper
            history_service.update_job_status("running", "Scraping SC Malaysia...", 0.6)
            try:
                scraper = SCScraper()
                logger.info(f"[{job_id}] Running SC Scraper...")
                documents = scraper.run(limit=5)
                
                # Ingest
                _ingest_documents(documents, history_service, job_id, 0.7, 0.9)
                total_docs += len(documents)
            except Exception as e:
                logger.error(f"SC Scraper failed: {e}")

        
        history_service.update_job_status("completed", f"Job finished. Processed {total_docs} documents.", 1.0)
        logger.info(f"[{job_id}] Update job completed successfully.")
        
    except Exception as e:
        logger.error(f"[{job_id}] Update job failed: {e}")
        history_service.update_job_status("failed", f"Job failed: {str(e)}", 0.0)

def _ingest_documents(documents, history_service, job_id, start_prog, end_prog):
    """Helper to ingest a list of documents with progress tracking."""
    ingestion_service = IngestionService()
    total = len(documents)
    if total == 0: return

    # Load existing history to check for duplicates
    # This is a simple memory-based check. For production, use DB.
    existing_history = history_service.get_ingestion_history()
    processed_files = {h["filename"] for h in existing_history if h.get("status") == "success"}

    for idx, doc in enumerate(documents):
        # Calculate granular progress
        current_prog = start_prog + ((idx / total) * (end_prog - start_prog))
        history_service.update_job_status("running", f"Checking: {doc.title[:50]}...", current_prog)
        
        # Check if already processed
        if doc.file_path.name in processed_files:
            history_service.log_ingestion(
                type="auto_update",
                source=doc.source,
                filename=doc.file_path.name,
                status="skipped",
                error="Already processed"
            )
            logger.info(f"[{job_id}] Skipped existing: {doc.title}")
            continue

        try:
            logger.info(f"[{job_id}] Ingesting: {doc.title}")
            history_service.update_job_status("running", f"Ingesting: {doc.title[:50]}...", current_prog)
            
            # Pass source explicitly
            result = ingestion_service._process_document(
                file_path=doc.file_path, 
                source_url=doc.url,
                source_name=doc.source
            )
            
            # Log to history
            history_service.log_ingestion(
                type="auto_update",
                source=doc.source,
                filename=doc.file_path.name,
                status=result.get("status", "unknown"),
                error=result.get("message")
            )
            
            # Add to local cache for this run
            processed_files.add(doc.file_path.name)
            
        except Exception as e:
            logger.error(f"[{job_id}] Failed to ingest {doc.title}: {e}")
            history_service.log_ingestion(
                type="auto_update",
                source=doc.source,
                filename=doc.file_path.name,
                status="failed",
                error=str(e)
            )
def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        # Run every 24 hours
        trigger = IntervalTrigger(hours=24)
        
        # Add job
        scheduler.add_job(
            run_daily_update,
            trigger=trigger,
            id="daily_update",
            name="Daily Content Update",
            replace_existing=True,
            next_run_time=datetime.now() # Run immediately on startup for DEMO purposes or remove this line for real prod
        )
        
        scheduler.start()
        logger.info("Scheduler started.")

def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
