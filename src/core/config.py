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
    llm_model: str = "claude-3-5-sonnet-20241022"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2000
    embedding_model: str = "text-embedding-3-large"
    
    # RAG settings
    rag_top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Singleton instance
settings = Settings()
