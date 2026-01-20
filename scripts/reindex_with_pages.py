"""
Re-index all PDFs with page number tracking.
This script replaces the current Pinecone index with page-aware chunks.
"""

import json
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.pdf_extractor import PDFExtractor
from src.processors.chunker import chunk_with_pages
from src.processors.arabic import prepare_for_embedding
from src.vector_db.pinecone_store import PineconeStore


def find_pdfs(data_dir: Path) -> list[tuple[str, Path]]:
    """Find all PDFs in the data directory."""
    pdfs = []
    
    # Known source directories
    sources = {
        "bnm": "BNM",
        "aaoifi": "AAOIFI",
        "sc": "SC Malaysia",
        "jakim": "JAKIM",
    }
    
    for folder, source_name in sources.items():
        folder_path = data_dir / folder
        if folder_path.exists():
            for pdf in folder_path.glob("*.pdf"):
                pdfs.append((source_name, pdf))
    
    return pdfs


def process_pdf(source: str, pdf_path: Path) -> list[dict]:
    """Extract and chunk a PDF with page numbers."""
    print(f"\n[PDF] Processing: {pdf_path.name}")

    # Extract with page tracking
    extractor = PDFExtractor()
    result = extractor.extract(pdf_path)

    if not result.page_texts:
        print(f"   [WARN] No page texts extracted (quality: {result.quality_score:.2f})")
        return []

    print(f"   [OK] Extracted {result.pages} pages (quality: {result.quality_score:.2f})")
    
    # Chunk with page numbers
    metadata = {
        "source": source,
        "title": pdf_path.stem.replace("-", " ").replace("_", " "),
        "filename": pdf_path.name,
        "language": result.language.value,
    }
    
    chunks = chunk_with_pages(
        result.page_texts,
        chunk_size=800,  # Slightly smaller for better retrieval
        chunk_overlap=100,
        metadata=metadata,
    )
    
    print(f"   [OK] Created {len(chunks)} chunks with page numbers")
    
    # Convert to dicts for indexing
    return [chunk.to_dict() for chunk in chunks]


def save_chunks_json(all_chunks: list[dict], output_path: Path):
    """Save chunks to JSON for backup."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVE] Saved {len(all_chunks)} chunks to {output_path}")


def index_to_pinecone(chunks: list[dict]):
    """Index chunks to Pinecone with page numbers."""
    print("\n[INDEX] Indexing to Pinecone...")

    store = PineconeStore()

    # Delete existing vectors (full re-index)
    try:
        print("   [CLEAR] Clearing existing index...")
        store.index.delete(delete_all=True)
        print("   [OK] Index cleared")
    except Exception as e:
        print(f"   [WARN] Could not clear index: {e}")
    
    # Create TextChunk-like objects for indexing
    from src.processors.chunker import TextChunk
    
    chunk_objects = []
    for chunk_dict in chunks:
        chunk = TextChunk(
            text=chunk_dict["text"],
            chunk_index=chunk_dict.get("chunk_index", 0),
            start_char=chunk_dict.get("start_char", 0),
            end_char=chunk_dict.get("end_char", 0),
            metadata={
                "source": chunk_dict.get("source", "Unknown"),
                "title": chunk_dict.get("title", ""),
                "filename": chunk_dict.get("filename", ""),
                "language": chunk_dict.get("language", "en"),
                "page_number": chunk_dict.get("page_number"),
            },
            page_number=chunk_dict.get("page_number"),
        )
        chunk_objects.append(chunk)
    
    # Index in batches
    count = store.add_chunks(iter(chunk_objects))
    print(f"\n[OK] Indexed {count} chunks to Pinecone with page numbers!")


def main():
    """Main entry point."""
    print("=" * 60)
    print("RE-INDEXING PDFs WITH PAGE NUMBERS")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    data_dir = Path("data")

    # Find all PDFs
    pdfs = find_pdfs(data_dir)
    print(f"\n[FOUND] {len(pdfs)} PDFs to process:")
    for source, pdf in pdfs:
        print(f"   - [{source}] {pdf.name}")

    if not pdfs:
        print("\n[ERROR] No PDFs found in data directory!")
        return

    # Process all PDFs
    all_chunks = []
    for source, pdf_path in pdfs:
        chunks = process_pdf(source, pdf_path)
        all_chunks.extend(chunks)

    print(f"\n[TOTAL] {len(all_chunks)} chunks from {len(pdfs)} PDFs")

    # Save to JSON backup
    output_path = data_dir / "processed" / "all_chunks_with_pages.json"
    save_chunks_json(all_chunks, output_path)

    # Index to Pinecone
    index_to_pinecone(all_chunks)

    print("\n" + "=" * 60)
    print("RE-INDEXING COMPLETE!")
    print("=" * 60)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nPage numbers are now available in source metadata.")
    print("Restart the API server to see the changes.")


if __name__ == "__main__":
    main()
