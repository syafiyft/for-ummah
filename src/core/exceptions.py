"""
Custom exceptions for Agent Deen.
Provides clear error types for better debugging.
"""


class AgentDeenError(Exception):
    """Base exception for all Agent Deen errors."""
    pass


class ScraperError(AgentDeenError):
    """Error during web scraping."""
    
    def __init__(self, source: str, message: str, url: str | None = None):
        self.source = source
        self.url = url
        super().__init__(f"[{source}] {message}" + (f" URL: {url}" if url else ""))


class ProcessorError(AgentDeenError):
    """Error during document processing."""
    
    def __init__(self, processor: str, message: str, file_path: str | None = None):
        self.processor = processor
        self.file_path = file_path
        super().__init__(f"[{processor}] {message}" + (f" File: {file_path}" if file_path else ""))


class VectorDBError(AgentDeenError):
    """Error with vector database operations."""
    pass


class AIError(AgentDeenError):
    """Error with AI/LLM operations."""
    pass
