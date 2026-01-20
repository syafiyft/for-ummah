"""
Script to load and index sample documents.
Run this before using the chatbot if you don't have real documents.
"""

import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processors.chunker import chunk_text, TextChunk
from src.processors.arabic import prepare_for_embedding


def load_sample_documents():
    """Load sample documents from JSON file."""
    sample_path = Path("data/sample/shariah_documents.json")
    
    if not sample_path.exists():
        print(f"❌ Sample file not found: {sample_path}")
        return []
    
    with open(sample_path) as f:
        documents = json.load(f)
    
    print(f"✅ Loaded {len(documents)} sample documents")
    return documents


def prepare_chunks(documents: list[dict]) -> list[TextChunk]:
    """Prepare documents for indexing."""
    all_chunks = []
    
    for doc in documents:
        # Prepare text for embedding
        text = prepare_for_embedding(doc["text"])
        
        # Chunk the document
        chunks = chunk_text(
            text,
            chunk_size=500,
            chunk_overlap=50,
            metadata={
                "source": doc["source"],
                "title": doc["title"],
                "language": doc["language"],
            }
        )
        
        all_chunks.extend(chunks)
    
    print(f"✅ Created {len(all_chunks)} chunks from {len(documents)} documents")
    return all_chunks


def main():
    """Main entry point."""
    print("\n📚 Loading sample Shariah documents...")
    documents = load_sample_documents()
    
    if not documents:
        return
    
    print("\n📝 Preparing chunks for indexing...")
    chunks = prepare_chunks(documents)
    
    print("\n🔍 Sample chunks:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n  [{i+1}] Source: {chunk.metadata['source']}")
        print(f"      Title: {chunk.metadata['title']}")
        print(f"      Text: {chunk.text[:100]}...")
    
    print("\n✅ Data preparation complete!")
    print("\nTo index to Pinecone, set your API keys in .env and run:")
    print("  python scripts/index_documents.py")


if __name__ == "__main__":
    main()
