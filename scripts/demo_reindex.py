import logging
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(".")

from src.services.ingestion import IngestionService
from src.core import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def demo_reindex(source: str):
    """
    Force re-index all PDFs in the specified source directory.
    """
    source = source.lower()
    data_dir = Path(f"data/{source}")
    
    print(f"\n🚀 Starting Demo Re-indexing for: {source.upper()}")
    print("=" * 50)

    if not data_dir.exists():
        logger.error(f"Directory not found: {data_dir}")
        print(f"❌ Error: Data directory 'data/{source}' does not exist.")
        return

    ingestion_service = IngestionService()
    
    # Get all PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {data_dir}")
        print("⚠️  No PDF files found to re-index.")
        return

    print(f"📂 Found {len(pdf_files)} PDF files.")
    print("=" * 50 + "\n")

    success_count = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}...")
            
            # [CHANGEABLE] This URL is simulated for the demo.
            # In a real scenario, this would be the actual source URL (e.g. from the website).
            # For the demo, we just want to show that it's being processed.
            source_url = f"https://demo.reindex/{source}/{pdf_file.name}"

            result = ingestion_service._process_document(
                file_path=pdf_file,
                source_url=source_url,
                source_name=source,
                force_reindex=True
            )
            
            status = result.get("status", "unknown")
            if status == "success":
                print(f"✅ Indexed! ({result.get('chunks')} chunks)\n")
                success_count += 1
            else:
                print(f"⚠️  Status: {status} - {result.get('message', '')}\n")
            
        except Exception as e:
            logger.error(f"Failed to re-index {pdf_file.name}: {e}")
            print(f"❌ Failed: {e}\n")

    print("=" * 50)
    print(f"🎉 Demo Complete! Successfully re-indexed {success_count}/{len(pdf_files)} documents.")
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo Re-indexing Script")
    # [CHANGEABLE] Change 'default' to 'bnm', 'aaoifi', or 'manual' to switch the default source
    parser.add_argument("source", nargs="?", default="sc_malaysia", help="Source to re-index (bnm, sc_malaysia, aaoifi, manual)")
    args = parser.parse_args()
    
    demo_reindex(args.source)
