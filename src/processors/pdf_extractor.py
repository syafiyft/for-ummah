"""
Smart PDF text extraction with cascade fallback.

Extraction Strategy (cheapest first):
1. PyMuPDF - For digital PDFs (fast, free, excellent Arabic support)
2. Tesseract OCR - For scanned PDFs (free, good Arabic support)

This cascade approach minimizes cost while maximizing quality.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging

import fitz  # PyMuPDF

from src.core.language import Language, detect_language
from src.core.exceptions import ProcessorError

logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    """How the text was extracted."""
    DIGITAL = "digital"     # PyMuPDF - native text
    OCR = "ocr"            # Tesseract OCR
    FAILED = "failed"


@dataclass
class ExtractionResult:
    """Result of PDF text extraction."""
    text: str
    method: ExtractionMethod
    language: Language
    pages: int
    quality_score: float  # 0.0 to 1.0
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "method": self.method.value,
            "language": self.language.value,
            "pages": self.pages,
            "quality_score": self.quality_score,
        }


class PDFExtractor:
    """
    Smart PDF extractor with cascade fallback.
    
    Tries PyMuPDF first (digital text), falls back to OCR if needed.
    """
    
    def __init__(self, min_quality: float = 0.3):
        """
        Args:
            min_quality: Minimum quality score to accept extraction
        """
        self.min_quality = min_quality
    
    def extract(self, file_path: str | Path) -> ExtractionResult:
        """
        Extract text from PDF using best available method.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            ExtractionResult with text and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ProcessorError("PDFExtractor", f"File not found: {file_path}")
        
        # Try digital extraction first (PyMuPDF)
        result = self._extract_pymupdf(file_path)
        
        if result.quality_score >= self.min_quality:
            return result
        
        logger.info(f"Low quality ({result.quality_score:.2f}), trying OCR...")
        
        # Fallback to OCR
        ocr_result = self._extract_tesseract(file_path)
        
        # Return whichever has better quality
        if ocr_result.quality_score > result.quality_score:
            return ocr_result
        
        return result
    
    def _extract_pymupdf(self, file_path: Path) -> ExtractionResult:
        """Extract text using PyMuPDF (for digital PDFs)."""
        try:
            doc = fitz.open(file_path)
            
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            
            text = "\n\n".join(text_parts)
            pages = len(doc)
            doc.close()
            
            quality = self._assess_quality(text)
            language = detect_language(text)
            
            return ExtractionResult(
                text=text,
                method=ExtractionMethod.DIGITAL,
                language=language,
                pages=pages,
                quality_score=quality,
            )
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return ExtractionResult(
                text="",
                method=ExtractionMethod.FAILED,
                language=Language.ENGLISH,
                pages=0,
                quality_score=0.0,
            )
    
    def _extract_tesseract(self, file_path: Path) -> ExtractionResult:
        """Extract text using Tesseract OCR (for scanned PDFs)."""
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Convert PDF pages to images
            images = convert_from_path(file_path, dpi=200)
            
            text_parts = []
            for i, image in enumerate(images):
                # OCR with Arabic + English support
                text = pytesseract.image_to_string(
                    image,
                    lang='ara+eng',
                    config='--psm 6'  # Assume uniform block of text
                )
                text_parts.append(text)
            
            text = "\n\n".join(text_parts)
            quality = self._assess_quality(text)
            language = detect_language(text)
            
            return ExtractionResult(
                text=text,
                method=ExtractionMethod.OCR,
                language=language,
                pages=len(images),
                quality_score=quality,
            )
            
        except ImportError:
            logger.warning("Tesseract/pdf2image not available, skipping OCR")
            return ExtractionResult(
                text="",
                method=ExtractionMethod.FAILED,
                language=Language.ENGLISH,
                pages=0,
                quality_score=0.0,
            )
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            return ExtractionResult(
                text="",
                method=ExtractionMethod.FAILED,
                language=Language.ENGLISH,
                pages=0,
                quality_score=0.0,
            )
    
    def _assess_quality(self, text: str) -> float:
        """
        Assess quality of extracted text (0.0 to 1.0).
        
        Checks for:
        - Minimum text length
        - Garbled characters
        - Word count
        """
        if not text or len(text.strip()) < 50:
            return 0.0
        
        import re
        
        # Count garbled/unusual characters
        total_chars = len(text)
        
        # Characters that shouldn't appear frequently in normal text
        # (excluding Arabic range which we want to keep)
        garbled = len(re.findall(r'[^\w\s\u0600-\u06FF.,;:!?()[\]{}\'\"؛،\-–—]', text))
        
        # Calculate garbled ratio
        garbled_ratio = garbled / total_chars if total_chars > 0 else 1.0
        
        # Base quality
        quality = 1.0 - (garbled_ratio * 3)  # Penalize garbled heavily
        
        # Bonus for having reasonable word count
        words = len(text.split())
        if words > 100:
            quality += 0.1
        if words > 500:
            quality += 0.1
        
        return max(0.0, min(1.0, quality))


# Convenience function
def extract_pdf(file_path: str | Path) -> ExtractionResult:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        ExtractionResult with text and metadata
    """
    extractor = PDFExtractor()
    return extractor.extract(file_path)
