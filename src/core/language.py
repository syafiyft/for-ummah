"""
Language detection and utilities for trilingual support.
Supports: Arabic (ar), English (en), Malay (ms)
"""

import re
from enum import Enum


class Language(Enum):
    """Supported languages in Agent Deen."""
    ARABIC = "ar"
    ENGLISH = "en"
    MALAY = "ms"
    MIXED = "mixed"
    
    @property
    def display_name(self) -> str:
        """Human-readable name for the language."""
        names = {
            "ar": "العربية (Arabic)",
            "en": "English",
            "ms": "Bahasa Melayu",
            "mixed": "Mixed"
        }
        return names.get(self.value, self.value)


def detect_language(text: str) -> Language:
    """
    Detect the primary language of a text.
    
    Uses character-based heuristics:
    - Arabic Unicode range: \\u0600-\\u06FF
    - Malay detection: common Malay words
    - Default: English
    
    Args:
        text: Input text to analyze
        
    Returns:
        Language enum value
    """
    if not text or not text.strip():
        return Language.ENGLISH
    
    # Count Arabic characters
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    total = arabic_chars + latin_chars
    
    if total == 0:
        return Language.ENGLISH
    
    arabic_ratio = arabic_chars / total
    
    # Primarily Arabic
    if arabic_ratio > 0.6:
        return Language.ARABIC
    
    # Mixed content
    if arabic_ratio > 0.1:
        return Language.MIXED
    
    # Check for Malay - common words
    malay_markers = [
        # Common words
        'adalah', 'dengan', 'untuk', 'yang', 'ini', 'itu',
        'boleh', 'tidak', 'ada', 'saya', 'kita', 'dalam',
        'kepada', 'daripada', 'seperti', 'oleh', 'tetapi',
        'atau', 'jika', 'apabila', 'kerana', 'supaya',
        # Question words
        'apakah', 'bagaimana', 'mengapa', 'siapa', 'bila',
        'adakah', 'berapa', 'mana', 'kenapa', 'macam',
        # Islamic finance terms in Malay context
        'perbankan', 'kewangan', 'patuh', 'syariah', 'halal',
        'haram', 'faedah', 'riba', 'pinjaman', 'pelaburan',
        # Common verbs
        'mahu', 'hendak', 'perlu', 'ingin', 'akan',
        'telah', 'sudah', 'sedang', 'dapat', 'bolehkah',
    ]
    
    text_lower = text.lower()
    malay_matches = sum(1 for word in malay_markers if word in text_lower)
    
    # Lower threshold for short queries (e.g., "Apakah itu Takaful?")
    word_count = len(text.split())
    if word_count <= 5 and malay_matches >= 1:
        return Language.MALAY
    
    # If contains multiple Malay markers, likely Malay
    if malay_matches >= 2:
        return Language.MALAY
    
    return Language.ENGLISH


def get_response_language(query_lang: Language, preference: Language | None = None) -> Language:
    """
    Determine which language to respond in.
    
    Args:
        query_lang: Language of the user's query
        preference: User's preferred response language (optional)
        
    Returns:
        Language to use for response
    """
    if preference:
        return preference
    
    # Respond in same language as query (unless mixed)
    if query_lang == Language.MIXED:
        return Language.ENGLISH
    
    return query_lang
