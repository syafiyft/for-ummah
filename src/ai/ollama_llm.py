"""
Ollama LLM client for Agent Deen.
100% FREE local inference using llama3.2.
"""

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # "system", "user", "assistant"
    content: str


class OllamaLLM:
    """
    Local LLM using Ollama (FREE).
    Uses llama3.2 for chat completions.
    """
    
    def __init__(
        self, 
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url
        logger.info(f"OllamaLLM initialized with model: {model}")
    
    def chat(
        self,
        messages: list[ChatMessage] | list[dict],
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate a chat completion.
        
        Args:
            messages: List of ChatMessage or dicts with role/content
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Assistant's response text
        """
        # Convert to dict format if needed
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                formatted_messages.append(msg)
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
                timeout=120,  # Longer timeout for LLM inference
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Ollama error: {response.text}")
            
            data = response.json()
            return data["message"]["content"]
            
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to Ollama. Make sure it's running:\n"
                "  ollama serve"
            )
        except Exception as e:
            logger.error(f"Ollama LLM error: {e}")
            raise
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Simple generation from a single prompt.
        
        Args:
            prompt: The prompt text
            **kwargs: Additional args passed to chat()
            
        Returns:
            Generated text
        """
        return self.chat([{"role": "user", "content": prompt}], **kwargs)
