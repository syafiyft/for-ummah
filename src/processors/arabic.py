"""
Arabic text processing and normalization.

Essential for improving RAG quality with Arabic documents:
- Removes diacritics (harakat) for consistent matching
- Normalizes letter variants (alef, yeh)
- Cleans OCR artifacts
"""

import re


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for better search matching.
    
    Transformations:
    1. Remove diacritics (tashkeel/harakat)
    2. Normalize alef variants → ا
    3. Normalize yeh variants → ي
    4. Remove tatweel (kashida/elongation)
    5. Normalize numbers to Western Arabic
    
    Args:
        text: Input text (may contain Arabic and other scripts)
        
    Returns:
        Normalized text
    """
    if not text:
        return text
    
    # 1. Remove Arabic diacritics (tashkeel)
    # Range: \u064B-\u0652 covers fatha, damma, kasra, sukun, etc.
    # \u0670 is superscript alef
    text = re.sub(r'[\u064B-\u0652\u0670]', '', text)
    
    # 2. Normalize alef variants
    # أ إ ٱ آ → ا
    text = re.sub(r'[إأٱآ]', 'ا', text)
    
    # 3. Normalize alef maqsura and yeh
    # ى → ي
    text = re.sub(r'ى', 'ي', text)
    
    # 4. Remove tatweel (used for text justification)
    # ـ (U+0640)
    text = re.sub(r'ـ', '', text)
    
    # 5. Normalize Eastern Arabic numerals to Western
    # ٠١٢٣٤٥٦٧٨٩ → 0123456789
    eastern_to_western = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    text = text.translate(eastern_to_western)
    
    return text


def clean_ocr_artifacts(text: str) -> str:
    """
    Remove common OCR artifacts from text.
    
    Args:
        text: Text potentially containing OCR errors
        
    Returns:
        Cleaned text
    """
    if not text:
        return text
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove standalone page numbers (common pattern)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    
    # Remove isolated single characters (often OCR errors)
    text = re.sub(r'\s[a-zA-Z]\s', ' ', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def extract_islamic_citations(text: str) -> list[str]:
    """
    Extract Quranic verses and Hadith references from Arabic text.
    
    Args:
        text: Arabic text containing citations
        
    Returns:
        List of extracted citations
    """
    citations = []
    
    # Pattern for Quranic references: سورة X آية Y
    quran_pattern = r'سورة\s+(\S+)\s+آية\s+(\d+)'
    for match in re.finditer(quran_pattern, text):
        surah, ayah = match.groups()
        citations.append(f"القرآن: سورة {surah}، آية {ayah}")
    
    # Pattern for Hadith collections
    hadith_sources = [
        'صحيح البخاري',
        'صحيح مسلم',
        'سنن أبي داود',
        'سنن الترمذي',
        'سنن النسائي',
        'سنن ابن ماجه',
    ]
    
    for source in hadith_sources:
        if source in text:
            citations.append(source)
    
    return list(set(citations))  # Remove duplicates


def prepare_for_embedding(text: str) -> str:
    """
    Prepare text for embedding/indexing.
    
    Combines normalization and cleaning.
    
    Args:
        text: Raw text from PDF extraction
        
    Returns:
        Clean, normalized text ready for embedding
    """
    text = clean_ocr_artifacts(text)
    text = normalize_arabic(text)
    return text
