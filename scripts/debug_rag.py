import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.vector_db import PineconeStore
from src.core import settings
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_rag")

def debug_search(query: str):
    print(f"\n🔍 Debugging Search for: '{query}'")
    print(f"⚙️  Settings: Top-K={settings.rag_top_k}, Threshold={settings.rag_relevance_threshold}")
    
    store = PineconeStore()
    
    # Run search with higher Limit to see where the doc is buried
    results = store.search(query, top_k=20)
    
    print(f"\nFound {len(results)} raw matches (Top 20).")
    print("-" * 80)
    print(f"{'SCORE':<8} | {'SOURCE':<15} | {'TITLE/FILENAME'}")
    print("-" * 80)
    
    found_target = False
    
    for i, res in enumerate(results):
        score = res.get('score', 0)
        metadata = res.get('metadata', {})
        source = metadata.get('source', 'Unknown')
        title = metadata.get('title', 'No Title')
        filename = metadata.get('filename', 'No Filename')
        
        # Check if this is the target doc
        is_target = "operational" in title.lower() or "resilience" in filename.lower()
        marker = "✅ TARGET" if is_target else ""
        if is_target: found_target = True
        
        display_name = title if title != "Unknown" else filename
        
        print(f"{score:.4f}   | {source:<15} | {display_name[:50]}... {marker}")
        
    print("-" * 80)
    if not found_target:
        print("❌ Target document (Operational Resilience) NOT FOUND in Top 20.")
    else:
        print("✅ Target document FOUND in results.")

if __name__ == "__main__":
    query = "what is The BCM policy"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    debug_search(query)
