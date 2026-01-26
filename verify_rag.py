import asyncio
import logging
from src.core import settings
from src.ai.rag import RAGPipeline

# Setup basic logging
logging.basicConfig(level=logging.INFO)

async def test_rag():
    print(f"--- RAG Verification (Reranker: {settings.rerank_model}) ---")
    
    # Initialize pipeline
    rag = RAGPipeline(llm_type="ollama")
    
    queries = [
        "What is the definition of credit risk?",
        # "Is there any arabic term used in operational resilience?"
    ]
    
    for q in queries:
        print(f"\nScanning query: {q}")
        response = rag.query(q, top_k=50) # Ensure we get enough candidates
        
        print(f"Model Used: {response.model_used}")
        print(f"Reranked: {response.reranked}")
        print(f"Confidence: {response.confidence}")
        print(f"Answer: {response.answer}")
        
        found_takaful = False
        print("\nChecking for 'Takaful' in sources:")
        for i, src in enumerate(response.sources):
            has_term = "takaful" in src['snippet'].lower()
            if has_term:
                found_takaful = True
                print(f"[MATCH] Source {i+1} (Score: {src['score']:.4f}): {src['snippet'][:100]}...")
            elif i < 5:
                # Print top 5 non-matches just to see what IT IS picking
                print(f"Source {i+1} (Score: {src['score']:.4f}): {src['snippet'][:100]}...")
        
        if not found_takaful:
            print("\n[WARNING] 'Takaful' NOT found in top chunks!")

if __name__ == "__main__":
    asyncio.run(test_rag())
