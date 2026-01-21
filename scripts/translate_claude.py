"""
Fast trilingual translation using Claude Haiku.
Translates chunks in batches for significantly faster processing.
"""

import json
from pathlib import Path
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.chunker import TextChunk
from src.ai.claude_llm import ClaudeLLM
from src.vector_db.pinecone_store import PineconeStore


# Batch size - how many chunks to translate per API call
BATCH_SIZE = 20  # Balance between speed and reliability


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
        language="en",  # Assume source is English
        original_text=chunk_dict["text"],  # Preserve original
    )


def translate_batch_claude(
    llm: ClaudeLLM,
    texts: list[str],
    target_language: str,
) -> list[str]:
    """
    Translate a batch of texts using Claude.
    
    Args:
        llm: Claude LLM instance
        texts: List of texts to translate
        target_language: Target language name (e.g., "Malay", "Arabic")
        
    Returns:
        List of translated texts
    """
    if not texts:
        return []
    
    # Build prompt for batch translation
    prompt = f"""You are a professional translator. Translate these {len(texts)} texts to {target_language}.

RULES:
1. Return ONLY the translations
2. Separate each translation with the exact marker: <<<NEXT>>>
3. Keep the same order as input
4. Preserve formatting (newlines, bullets, etc.)
5. Do not add explanations

TEXTS:
"""
    for i, text in enumerate(texts):
        prompt += f"\n[{i+1}]\n{text}\n"
    
    prompt += f"\nNow translate all {len(texts)} texts to {target_language}. Separate with <<<NEXT>>>:"
    
    try:
        response = llm.generate(
            prompt,
            temperature=0.2,
            max_tokens=8192,
        )
        
        # Parse response
        translations = response.split("<<<NEXT>>>")
        translations = [t.strip() for t in translations if t.strip()]
        
        # Handle count mismatch
        if len(translations) != len(texts):
            print(f"   [WARN] Expected {len(texts)} translations, got {len(translations)}")
            while len(translations) < len(texts):
                translations.append(texts[len(translations)])
        
        return translations[:len(texts)]
        
    except Exception as e:
        print(f"   [ERROR] Translation failed: {e}")
        return texts  # Return originals on failure


def create_trilingual_chunks_claude(
    chunks: list[TextChunk],
    llm: ClaudeLLM,
) -> list[TextChunk]:
    """
    Create trilingual chunks using Claude for fast translation.
    
    Args:
        chunks: Original English chunks
        llm: Claude LLM instance
        
    Returns:
        List of trilingual chunks (EN + MS + AR)
    """
    all_chunks = []
    total = len(chunks)
    
    print(f"\n[TRANSLATE] Processing {total} chunks with Claude Haiku...")
    print(f"   Batch size: {BATCH_SIZE} chunks per request")
    print(f"   Estimated API calls: {(total // BATCH_SIZE + 1) * 2}")
    
    # Process in batches
    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch_chunks = chunks[batch_start:batch_end]
        batch_texts = [c.text for c in batch_chunks]
        
        progress = (batch_start / total) * 100
        print(f"   [{progress:.1f}%] Translating chunks {batch_start+1}-{batch_end}...")
        
        # Translate to Malay
        malay_texts = translate_batch_claude(llm, batch_texts, "Malay")
        
        # Translate to Arabic
        arabic_texts = translate_batch_claude(llm, batch_texts, "Arabic")
        
        # Create chunk objects
        for i, chunk in enumerate(batch_chunks):
            # Original English chunk
            chunk.language = "en"
            chunk.original_text = chunk.text
            all_chunks.append(chunk)
            
            # Malay translation
            ms_chunk = TextChunk(
                text=malay_texts[i],
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata=chunk.metadata.copy(),
                page_number=chunk.page_number,
                total_pages=chunk.total_pages,
                language="ms",
                original_text=chunk.text,
            )
            all_chunks.append(ms_chunk)
            
            # Arabic translation
            ar_chunk = TextChunk(
                text=arabic_texts[i],
                chunk_index=chunk.chunk_index,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                metadata=chunk.metadata.copy(),
                page_number=chunk.page_number,
                total_pages=chunk.total_pages,
                language="ar",
                original_text=chunk.text,
            )
            all_chunks.append(ar_chunk)
    
    return all_chunks


def main():
    """Main entry point."""
    print("=" * 60)
    print("FAST TRILINGUAL TRANSLATION WITH CLAUDE HAIKU")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize Claude
    print("\n[INIT] Initializing Claude Haiku...")
    try:
        llm = ClaudeLLM()
        info = llm.get_model_info()
        print(f"   Model: {info['model']}")
        print(f"   Is Haiku: {'✅ YES' if info['is_haiku'] else '❌ NO'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n   Make sure ANTHROPIC_API_KEY is set in .env")
        return
    
    # Load existing chunks
    chunks_path = Path("data/processed/all_chunks_with_pages.json")
    print(f"\n[LOAD] Loading chunks from {chunks_path}")
    
    try:
        chunk_dicts = load_existing_chunks(chunks_path)
        print(f"   [OK] Loaded {len(chunk_dicts)} chunks")
    except FileNotFoundError as e:
        print(f"   [ERROR] {e}")
        return
    
    # Convert to TextChunk objects
    chunks = [dict_to_chunk(d) for d in chunk_dicts]
    
    # Translate with Claude
    trilingual_chunks = create_trilingual_chunks_claude(chunks, llm)
    
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
    print("  - Source snippets show original text")
    print("\nRestart the API server to see the changes.")


if __name__ == "__main__":
    main()
