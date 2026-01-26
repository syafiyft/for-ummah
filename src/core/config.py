"""
Centralized configuration for Agent Deen.
All settings in one place - no hardcoded values scattered around.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    pinecone_api_key: str = ""
    
    # Pinecone
    pinecone_index: str = "shariah-kb"
    pinecone_region: str = "us-east-1"
    
    # Paths
    data_dir: Path = Path("data")
    
    # Scraper settings
    request_delay: float = 1.0  # Seconds between requests (polite crawling)
    request_timeout: int = 30
    
    # AI settings
    llm_model: str = "claude-3-5-haiku-20241022"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2000
    embedding_model: str = "text-embedding-3-large"
    
    # Ollama settings (FREE local inference)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    use_ollama: bool = True  # Set to False to use Anthropic instead
    
    # RAG settings
    rag_top_k: int = 60  # Increased for reranking (retrieve ample candidates)
    rag_rerank_top_k: int = 25  # Increased to 25 to capture subtle details (like "Takaful")
    rag_relevance_threshold: float = 0.60  # Lowered slightly as reranker handles precision
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Dynamic Prompt Settings
    knowledge_sources: list[str] = [
        "Bank Negara Malaysia (BNM) Shariah Policy Documents",
        "AAOIFI Shariah Standards",
        "Securities Commission Malaysia (SC) Resolutions",
        "JAKIM Fatwas",
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton instance
settings = Settings()
