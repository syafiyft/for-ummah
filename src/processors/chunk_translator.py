"""
Chunk translator for trilingual indexing.
Translates text chunks to multiple languages for cross-language retrieval.
"""

import logging
import time
from dataclasses import replace
from deep_translator import GoogleTranslator
from deep_translator.exceptions import RequestError

from src.processors.chunker import TextChunk

logger = logging.getLogger(__name__)

# Language configurations
LANGUAGES = {
    "en": "english",
    "ms": "malay", 
    "ar": "arabic",
}

# Rate limiting to avoid Google Translate blocks
DELAY_BETWEEN_REQUESTS = 0.1  # 100ms between requests


class ChunkTranslator:
    """Translate chunks to multiple languages."""
    
    def __init__(self):
        self.translators = {}
        self._init_translators()
    
    def _init_translators(self):
        """Initialize translators for each language pair."""
        # We'll translate FROM English TO other languages
        for target_code in ["ms", "ar"]:
            self.translators[f"en->{target_code}"] = GoogleTranslator(
                source="en", 
                target=target_code
            )
    
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code (en, ms, ar)
            target_lang: Target language code (en, ms, ar)
            
        Returns:
            Translated text
        """
        if source_lang == target_lang:
            return text
        
        if not text or len(text.strip()) < 5:
            return text
        
        try:
            # Create translator on-the-fly for flexibility
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            
            # Handle long texts by splitting
            max_chars = 4500
            if len(text) <= max_chars:
                result = translator.translate(text)
                time.sleep(DELAY_BETWEEN_REQUESTS)
                return result
            
            # Split by paragraphs for long texts
            paragraphs = text.split("\n\n")
            translated_parts = []
            
            for para in paragraphs:
                if para.strip():
                    if len(para) <= max_chars:
                        translated = translator.translate(para)
                        translated_parts.append(translated)
                        time.sleep(DELAY_BETWEEN_REQUESTS)
                    else:
                        # For very long paragraphs, split by sentences
                        sentences = para.split(". ")
                        batch = ""
                        for sentence in sentences:
                            if len(batch) + len(sentence) < max_chars:
                                batch += sentence + ". "
                            else:
                                if batch:
                                    translated_parts.append(translator.translate(batch))
                                    time.sleep(DELAY_BETWEEN_REQUESTS)
                                batch = sentence + ". "
                        if batch:
                            translated_parts.append(translator.translate(batch))
                            time.sleep(DELAY_BETWEEN_REQUESTS)
                else:
                    translated_parts.append("")
            
            return "\n\n".join(translated_parts)
            
        except RequestError as e:
            logger.warning(f"Translation request error: {e}")
            return text
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
    
    def translate_chunk(self, chunk: TextChunk, target_lang: str, original_text: str = None) -> TextChunk:
        """
        Create a translated copy of a chunk.
        
        Args:
            chunk: Original TextChunk
            target_lang: Target language code
            original_text: Original text to preserve for display (optional)
            
        Returns:
            New TextChunk with translated text and updated language
        """
        if chunk.language == target_lang:
            return chunk
        
        translated_text = self.translate_text(
            chunk.text, 
            chunk.language, 
            target_lang
        )
        
        # Create new chunk with translated text, preserving original for display
        return TextChunk(
            text=translated_text,
            chunk_index=chunk.chunk_index,
            start_char=chunk.start_char,
            end_char=chunk.end_char,
            metadata=chunk.metadata.copy(),
            page_number=chunk.page_number,
            total_pages=chunk.total_pages,
            language=target_lang,
            original_text=original_text or chunk.text,  # Preserve original for source display
        )
    
    def create_trilingual_chunks(
        self, 
        chunks: list[TextChunk],
        source_lang: str = "en",
        progress_callback=None,
    ) -> list[TextChunk]:
        """
        Create trilingual versions of all chunks.
        Preserves original text for display in source snippets.
        
        Args:
            chunks: List of original chunks
            source_lang: Language of original chunks
            progress_callback: Optional callback(current, total) for progress
            
        Returns:
            List of all chunks (original + translations)
        """
        all_chunks = []
        total = len(chunks)
        target_langs = [lang for lang in ["en", "ms", "ar"] if lang != source_lang]
        
        for i, chunk in enumerate(chunks):
            # Set source language on original (original_text is same as text)
            chunk.language = source_lang
            chunk.original_text = chunk.text  # Store original for display
            all_chunks.append(chunk)
            
            # Translate to other languages, preserving original text
            for target_lang in target_langs:
                translated = self.translate_chunk(chunk, target_lang, original_text=chunk.text)
                all_chunks.append(translated)
            
            if progress_callback and (i + 1) % 10 == 0:
                progress_callback(i + 1, total)
        
        return all_chunks


def translate_chunks_to_trilingual(
    chunks: list[TextChunk],
    source_lang: str = "en",
) -> list[TextChunk]:
    """
    Convenience function to translate chunks to all three languages.
    
    Args:
        chunks: Original chunks (assumed to be in source_lang)
        source_lang: Source language code
        
    Returns:
        List of trilingual chunks (3x the original count)
    """
    translator = ChunkTranslator()
    return translator.create_trilingual_chunks(chunks, source_lang)
