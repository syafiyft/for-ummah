"""
Translate and re-index all chunks as trilingual.
Creates EN, MS, AR versions of each chunk for cross-language retrieval.
"""

import json
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.chunker import TextChunk
from src.processors.chunk_translator import ChunkTranslator
from src.vector_db.pinecone_store import PineconeStore


def load_existing_chunks(json_path: Path) -> list[dict]:
    """Load chunks from JSON backup."""
    if not json_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {json_path}")
    
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def dict_to_chunk(chunk_dict: dict) -> TextChunk:
    """Convert a dictionary to a TextChunk object."""
    return TextChunk(
        text=chunk_dict["text"],
        chunk_index=chunk_dict.get("chunk_index", 0),
        start_char=chunk_dict.get("start_char", 0),
        end_char=chunk_dict.get("end_char", 0),
        metadata={
            "source": chunk_dict.get("source", "Unknown"),
            "title": chunk_dict.get("title", ""),
            "filename": chunk_dict.get("filename", ""),
        },
        page_number=chunk_dict.get("page_number"),
        total_pages=chunk_dict.get("total_pages"),
        language=chunk_dict.get("language", "en"),
    )


def progress_callback(current: int, total: int):
    """Print progress."""
    percent = (current / total) * 100
    print(f"   Translating: {current}/{total} ({percent:.1f}%)")


def main():
    """Main entry point."""
    print("=" * 60)
    print("TRILINGUAL CHUNK TRANSLATION & RE-INDEXING")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load existing chunks
    chunks_path = Path("data/processed/all_chunks_with_pages.json")
    print(f"\n[LOAD] Loading chunks from {chunks_path}")
    
    try:
        chunk_dicts = load_existing_chunks(chunks_path)
        print(f"   [OK] Loaded {len(chunk_dicts)} chunks")
    except FileNotFoundError as e:
        print(f"   [ERROR] {e}")
        print("\n   Please run reindex_with_pages.py first to create the chunks file.")
        return
    
    # Convert to TextChunk objects
    chunks = [dict_to_chunk(d) for d in chunk_dicts]
    
    # Translate to trilingual
    print("\n[TRANSLATE] Creating trilingual versions...")
    print("   This may take 15-30 minutes for 7000+ chunks...")
    print("   (Translating to Malay and Arabic)")
    
    translator = ChunkTranslator()
    trilingual_chunks = translator.create_trilingual_chunks(
        chunks, 
        source_lang="en",
        progress_callback=progress_callback,
    )
    
    print(f"\n   [OK] Created {len(trilingual_chunks)} trilingual chunks")
    print(f"   - English: {sum(1 for c in trilingual_chunks if c.language == 'en')}")
    print(f"   - Malay: {sum(1 for c in trilingual_chunks if c.language == 'ms')}")
    print(f"   - Arabic: {sum(1 for c in trilingual_chunks if c.language == 'ar')}")
    
    # Save trilingual chunks backup
    trilingual_path = Path("data/processed/all_chunks_trilingual.json")
    trilingual_path.parent.mkdir(parents=True, exist_ok=True)
    
    trilingual_dicts = [c.to_dict() for c in trilingual_chunks]
    with open(trilingual_path, "w", encoding="utf-8") as f:
        json.dump(trilingual_dicts, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVE] Saved trilingual chunks to {trilingual_path}")
    
    # Index to Pinecone
    print("\n[INDEX] Indexing to Pinecone...")
    
    store = PineconeStore()
    
    # Clear existing index
    try:
        print("   [CLEAR] Clearing existing index...")
        store.index.delete(delete_all=True)
        print("   [OK] Index cleared")
    except Exception as e:
        print(f"   [WARN] Could not clear index: {e}")
    
    # Index trilingual chunks
    count = store.add_chunks(iter(trilingual_chunks))
    
    print(f"\n   [OK] Indexed {count} trilingual chunks to Pinecone!")
    
    print("\n" + "=" * 60)
    print("TRILINGUAL INDEXING COMPLETE!")
    print("=" * 60)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nCross-language retrieval is now enabled:")
    print("  - Malay queries will match Malay chunks")
    print("  - Arabic queries will match Arabic chunks")
    print("  - English queries will match English chunks")
    print("\nRestart the API server to see the changes.")


if __name__ == "__main__":
    main()
