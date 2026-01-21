"""
Claude LLM client for Agent Deen.
Uses Claude Haiku 3.5 for fast, affordable AI responses.
"""

import logging
import os
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Model IDs - Claude Haiku 3.5 is the fastest and cheapest
CLAUDE_HAIKU = "claude-3-5-haiku-20241022"
CLAUDE_SONNET = "claude-3-5-sonnet-20241022"


class ClaudeLLM:
    """
    Claude LLM client using Anthropic API.
    Default: Claude Haiku 3.5 (fastest, cheapest).
    """
    
    def __init__(self, model: str = CLAUDE_HAIKU, api_key: str | None = None):
        """
        Initialize Claude client.
        
        Args:
            model: Model ID (default: claude-3-5-haiku-20241022)
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env)
        """
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Claude LLM initialized with model: {self.model}")
    
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a response from Claude.
        
        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        
        if system:
            kwargs["system"] = system
        
        response = self.client.messages.create(**kwargs)
        
        # Log model used for verification
        logger.info(f"Claude response from model: {response.model}")
        
        # Extract text from response
        return response.content[0].text
    
    def translate(
        self,
        texts: list[str],
        target_language: str,
        source_language: str = "auto",
    ) -> list[str]:
        """
        Translate multiple texts efficiently in a single request.
        
        Args:
            texts: List of texts to translate
            target_language: Target language (e.g., "Malay", "Arabic")
            source_language: Source language (default: auto-detect)
            
        Returns:
            List of translated texts
        """
        if not texts:
            return []
        
        # Build translation prompt
        prompt = f"""Translate the following {len(texts)} texts to {target_language}.

IMPORTANT:
- Return ONLY the translations, one per line
- Keep the same order as input
- Preserve any formatting (newlines, bullets, etc.)
- Do not add explanations or notes

Texts to translate:
"""
        for i, text in enumerate(texts):
            prompt += f"\n---TEXT {i+1}---\n{text}"
        
        prompt += f"\n\n---END---\n\nNow provide {len(texts)} translations to {target_language}, one per line, separated by '---NEXT---':"
        
        response = self.generate(
            prompt,
            system="You are a professional translator. Translate accurately and naturally.",
            temperature=0.2,
            max_tokens=4096,
        )
        
        # Parse response - split by separator
        translations = response.split("---NEXT---")
        translations = [t.strip() for t in translations if t.strip()]
        
        # Ensure we have the right number of translations
        if len(translations) != len(texts):
            logger.warning(f"Translation count mismatch: expected {len(texts)}, got {len(translations)}")
            # Pad or truncate as needed
            while len(translations) < len(texts):
                translations.append(texts[len(translations)])  # Keep original if missing
        
        return translations[:len(texts)]
    
    def get_model_info(self) -> dict:
        """Get information about the current model for verification."""
        return {
            "model": self.model,
            "is_haiku": "haiku" in self.model.lower(),
            "provider": "Anthropic",
        }


# Convenience function to verify model
def verify_claude_model():
    """
    Verify Claude is working and show which model is being used.
    Run this to confirm Haiku is active.
    """
    try:
        llm = ClaudeLLM()
        info = llm.get_model_info()
        
        print("=" * 50)
        print("CLAUDE MODEL VERIFICATION")
        print("=" * 50)
        print(f"Model ID: {info['model']}")
        print(f"Is Haiku: {'✅ YES' if info['is_haiku'] else '❌ NO'}")
        print(f"Provider: {info['provider']}")
        
        # Quick test
        response = llm.generate("Say 'Hello from Claude Haiku!' in exactly those words.")
        print(f"\nTest Response: {response}")
        print("=" * 50)
        
        return info
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    verify_claude_model()
