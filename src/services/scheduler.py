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
        sources = ["BNM", "SC", "AAOIFI"]

    try:
        total_docs = 0
        
        # --- 1. BNM SCRAPER ---
        if "BNM" in sources:
            history_service.update_job_status("running", "Scraping Bank Negara Malaysia...", 0.2)
            try:
                scraper = BNMScraper()
                logger.info(f"[{job_id}] Running BNM Scraper...")
                documents = scraper.run()
                
                # Ingest
                _ingest_documents(documents, history_service, job_id, 0.3, 0.5)
                total_docs += len(documents)
            except Exception as e:
                logger.error(f"BNM Scraper failed: {e}")

        # --- 2. SC MALAYSIA SCRAPER ---
        if "SC" in sources:
            from src.scrapers.sc import SCScraper
            history_service.update_job_status("running", "Scraping SC Malaysia...", 0.4)
            try:
                scraper = SCScraper()
                logger.info(f"[{job_id}] Running SC Scraper...")
                documents = scraper.run()
                
                # Ingest
                _ingest_documents(documents, history_service, job_id, 0.4, 0.6)
                total_docs += len(documents)
            except Exception as e:
                logger.error(f"SC Scraper failed: {e}")

        # --- 3. AAOIFI SCRAPER ---
        if "AAOIFI" in sources:
            from src.scrapers.aaoifi import AAOIFIScraper
            history_service.update_job_status("running", "Scraping AAOIFI...", 0.6)
            try:
                scraper = AAOIFIScraper()
                logger.info(f"[{job_id}] Running AAOIFI Scraper...")
                documents = scraper.run()
                
                # Ingest
                _ingest_documents(documents, history_service, job_id, 0.6, 0.8)
                total_docs += len(documents)
            except Exception as e:
                logger.error(f"AAOIFI Scraper failed: {e}")

        # --- 4. JAKIM SCRAPER ---
        if "JAKIM" in sources:
            from src.scrapers.jakim import JAKIMScraper
            history_service.update_job_status("running", "Scraping JAKIM...", 0.8)
            try:
                scraper = JAKIMScraper()
                logger.info(f"[{job_id}] Running JAKIM Scraper...")
                documents = scraper.run(limit=5)
                
                # Ingest
                _ingest_documents(documents, history_service, job_id, 0.8, 1.0)
                total_docs += len(documents)
            except Exception as e:
                logger.error(f"JAKIM Scraper failed: {e}")

        
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

    for idx, doc in enumerate(documents):
        # Calculate granular progress
        current_prog = start_prog + ((idx / total) * (end_prog - start_prog))
        history_service.update_job_status("running", f"Processing: {doc.title[:50]}...", current_prog)
        
        try:
            # IngestionService now handles history logging centrally
            logger.info(f"[{job_id}] Processing: {doc.title}")
            
            result = ingestion_service._process_document(
                file_path=doc.file_path, 
                source_url=doc.url,
                source_name=doc.source
            )
            
            if result.get("status") == "skipped":
                logger.info(f"[{job_id}] Skipped: {doc.title}")
            
        except Exception as e:
            logger.error(f"[{job_id}] Failed to ingest {doc.title}: {e}")
            # IngestionService should catch its own errors, but if it crashes, we log here too just in case
            # to keep the loop going.
            history_service.log_ingestion(
                type="auto_update",
                source=doc.source,
                filename=doc.file_path.name,
                status="failed",
                error=f"Scheduler Error: {str(e)}"
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
