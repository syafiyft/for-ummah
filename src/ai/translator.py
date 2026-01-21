"""
Language enforcement with fallback translation.
Ensures LLM responses are in the correct language.
"""

import logging
from langdetect import detect as langdetect_detect
from langdetect.lang_detect_exception import LangDetectException
from deep_translator import GoogleTranslator

from src.core.language import Language

logger = logging.getLogger(__name__)

# Language code mapping for translators
LANGUAGE_TO_CODE = {
    Language.ARABIC: "ar",
    Language.ENGLISH: "en",
    Language.MALAY: "ms",
    Language.MIXED: "en",  # Default to English for mixed
}


def detect_output_language(text: str) -> str | None:
    """
    Detect the language of the LLM output.
    
    Args:
        text: The text to detect language from
        
    Returns:
        ISO 639-1 language code (e.g., 'en', 'ar', 'ms') or None if detection fails
    """
    if not text or len(text.strip()) < 10:
        return None
    
    try:
        # langdetect returns ISO 639-1 codes
        detected = langdetect_detect(text)
        logger.debug(f"Detected output language: {detected}")
        return detected
    except LangDetectException as e:
        logger.warning(f"Language detection failed: {e}")
        return None


def ensure_response_language(
    response: str,
    target_language: Language,
    force_translate: bool = False,
) -> str:
    """
    Ensure the response is in the target language.
    If the LLM responded in a different language, translate it.
    
    Args:
        response: The LLM's response text
        target_language: The language the response should be in
        force_translate: If True, always translate regardless of detected language
        
    Returns:
        Response text in the target language
    """
    if not response or not response.strip():
        return response
    
    target_code = LANGUAGE_TO_CODE.get(target_language, "en")
    
    # Check if translation is needed
    if not force_translate:
        detected_code = detect_output_language(response)
        
        if detected_code is None:
            logger.debug("Could not detect language, skipping translation")
            return response
        
        # Handle language code variations
        # langdetect can return 'id' for Indonesian which is very close to Malay
        if target_code == "ms" and detected_code in ("ms", "id"):
            logger.debug("Response already in Malay/Indonesian, skipping translation")
            return response
        
        if detected_code == target_code:
            logger.debug(f"Response already in target language ({target_code})")
            return response
        
        logger.info(f"Language mismatch: detected={detected_code}, target={target_code}. Translating...")
    
    # Perform translation
    try:
        translator = GoogleTranslator(source="auto", target=target_code)
        
        # deep-translator has a character limit, so split long texts
        max_chars = 4500  # Google Translate limit is ~5000
        if len(response) <= max_chars:
            translated = translator.translate(response)
        else:
            # Split by paragraphs and translate each
            paragraphs = response.split("\n\n")
            translated_parts = []
            for para in paragraphs:
                if para.strip():
                    translated_para = translator.translate(para)
                    translated_parts.append(translated_para)
                else:
                    translated_parts.append(para)
            translated = "\n\n".join(translated_parts)
        
        logger.info(f"Successfully translated response to {target_code}")
        return translated
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        # Return original response if translation fails
        return response


def get_language_code(language: Language) -> str:
    """Get ISO 639-1 code for a Language enum."""
    return LANGUAGE_TO_CODE.get(language, "en")
