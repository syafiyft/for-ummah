import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vector_db.pinecone_store import PineconeStore

def test_search():
    print("Initializing Pinecone Store...")
    store = PineconeStore()
    
    query = "Debit Card"
    print(f"\nSearching for: {query}")
    
    # Check if specific file exists using filter
    print("\n--- Diagnostic: Checking for specific BNM file ---")
    target_file = "d5583ab01d86_Debit_Card_and_Debit_Card-i.pdf"
    
    dummy_vec = [0.1] * 768
    filter_res = store.index.query(
        vector=dummy_vec,
        top_k=5,
        include_metadata=True,
        filter={"filename": target_file}
    )
    
    if filter_res.matches:
        print(f"✅ Found {len(filter_res.matches)} chunks for file: {target_file}")
        print(f"Sample text: {filter_res.matches[0].metadata.get('text')[:100]}...")
    else:
        print(f"❌ No chunks found for file: {target_file}")
        
    # Regular search
    results = store.search(query, top_k=10)
    
    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} results:")
    for i, res in enumerate(results):
        meta = res['metadata']
        print(f"\nResult {i+1} (Score: {res['score']:.4f})")
        print(f"File: {meta.get('filename')}")
        print(f"Page: {meta.get('page_number', 'N/A')}")
        print(f"Text: {res['text'][:100]}...")

if __name__ == "__main__":
    test_search()
