# AI Fiqh Hackathon 2026 - Technical Implementation Plan
## 🚀 BarakahVault: Trilingual AI Shariah Compliance Assistant

## 📋 Project Overview

**Competition:** AI Fiqh Hackathon in Islamic Finance 2026  
**Deadline:** January 22, 2026 (3 days for POC submission)  
**Team:** BarakahVault  
**Venue:** Menara Kembar Bank Rakyat  

### Contest Requirements

**Evaluation Criteria:**
- **Shariah Standards & Regulations (70%)**
  - Shariah Compliance & Accuracy
  - Use of Authentic Sources
  - Consistency of Legal Reasoning
  - Business Model
  
- **Innovation (30%)**
  - Innovation & Originality
  - AI & Technology Application
  - Business Model & Value Proposition
  - User Experience & Clarity

### Required Deliverables

1. Proof of Concept (POC) - Working Prototype
2. Business Model Slide
3. AI Architecture Diagram
4. Innovation Strategies Documentation
5. Source Code
6. Supporting Documentation

---

## 🎯 Solution: BarakahVault - Trilingual AI Shariah Compliance Assistant

### 🌟 Unique Selling Proposition (USP)

**The ONLY trilingual Islamic finance AI assistant that:**
- Understands queries in **Arabic, English, and Malay**
- Searches across **multilingual Shariah documents**
- Provides answers with **original Arabic citations + translations**
- Handles **both digital and scanned Arabic PDFs**
- Offers **authentic Shariah scholarship** from authoritative sources

### Core Features
- 🌍 **Trilingual Support**: Arabic (العربية), English, Bahasa Melayu
- 📚 **Multi-source Knowledge Base**: BNM, AAOIFI, SC, State Fatwas (Arabic + English)
- 🔍 **Smart OCR**: Handles scanned Arabic documents automatically
- 📖 **Citation with Translation**: Original Arabic text + English translation
- 🎯 **Context-Aware**: Understands mixed-language documents
- ⚡ **Real-time Queries**: Shariah compliance checks in seconds
- 🔐 **Source Authentication**: Every answer traceable to original fatwa/ruling

---

## 🌍 Part 0: Multilingual & Arabic Document Handling

### The Challenge: Arabic Language in Islamic Finance

**Reality Check:**
- 60-80% of authentic Shariah sources are in Arabic
- AAOIFI standards: Primarily Arabic with English translations
- State fatwas: Often Arabic-only or Arabic-first
- BNM documents: Mix of English and Malay, some Arabic terms
- Scanned PDFs: Common in government archives

### Our Multilingual Strategy

#### Language Support Matrix

| Language | Input Queries | Document Sources | Output Responses | Priority |
|----------|---------------|------------------|------------------|----------|
| **Arabic (العربية)** | ✅ Yes | ✅ Primary | ✅ Yes | **HIGH** |
| **English** | ✅ Yes | ✅ Primary | ✅ Yes | **HIGH** |
| **Bahasa Melayu** | ✅ Yes | ✅ Secondary | ✅ Yes | **MEDIUM** |

#### Innovation Advantage: Turn Arabic into a Competitive Edge

```yaml
Why This Wins the Hackathon:
  1. Authenticity: Direct access to original Arabic fatwas
  2. Accuracy: No translation loss in Shariah rulings
  3. Market Differentiation: Most AI tools can't handle Arabic properly
  4. Regional Appeal: Malaysian Islamic finance professionals need Arabic access
  5. Scalability: Opens doors to GCC markets (UAE, Saudi Arabia, Qatar)
```

---

## 🛠️ Arabic Document Processing Pipeline

### Strategy: Mixed-Model Approach (Best of All Worlds)

We'll use a **smart cascade system** that optimizes for speed, cost, and accuracy:

```
Digital PDF → PyMuPDF (Fast & Free) → Success? ✅
    ↓ Failed
Scanned PDF → Tesseract OCR (Free) → Good Quality? ✅
    ↓ Low Quality
Complex/Important → Azure Document Intelligence → ✅ Guaranteed Success
```

### Tool Selection & Rationale

#### Tier 1: PyMuPDF (Primary - Digital PDFs)
```python
Cost: FREE
Speed: Very Fast (< 1 second per page)
Accuracy: 99%+ for digital PDFs
Arabic Support: Excellent
Use For: 
  - Modern AAOIFI standards (digital PDFs)
  - Recent BNM policies (digital)
  - SC Malaysia documents (digital)
Best For: 70% of your documents
```

#### Tier 2: Tesseract OCR (Secondary - Scanned Documents)
```python
Cost: FREE
Speed: Fast (2-3 seconds per page)
Accuracy: 75-85% for Arabic
Arabic Support: Good (with ara language pack)
Use For:
  - Older scanned fatwas
  - Government archives
  - Historical documents
Best For: 20% of your documents (when Tier 1 fails)
```

#### Tier 3: Azure Document Intelligence (Fallback - Critical Documents)
```python
Cost: $1.50 per 1,000 pages (Free tier: 500 pages/month)
Speed: Medium (5-8 seconds per page)
Accuracy: 95-98% for Arabic
Arabic Support: Excellent (Microsoft's best OCR)
Use For:
  - Failed Tesseract extractions
  - Critical AAOIFI standards
  - Complex multi-column layouts
  - Tables and forms in Arabic
Best For: 10% of your documents (highest quality needed)
```

### Implementation: Smart PDF Processor

```python
# File: processors/multilingual_pdf_processor.py

import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import re
from typing import Dict, List
from enum import Enum

class ExtractionMethod(Enum):
    PYMUPDF = "digital"
    TESSERACT = "ocr_free"
    AZURE = "ocr_premium"
    FAILED = "failed"

class Language(Enum):
    ARABIC = "ar"
    ENGLISH = "en"
    MALAY = "ms"
    MIXED = "mixed"

def detect_language(text: str) -> Language:
    """Detect primary language in text"""
    
    # Count character sets
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    
    total = arabic_chars + english_chars
    if total == 0:
        return Language.ENGLISH
    
    arabic_ratio = arabic_chars / total
    
    if arabic_ratio > 0.6:
        return Language.ARABIC
    elif arabic_ratio > 0.1:
        return Language.MIXED
    else:
        return Language.ENGLISH

def assess_text_quality(text: str) -> float:
    """
    Assess quality of extracted text (0-1 score)
    Returns confidence that extraction was successful
    """
    
    if not text or len(text.strip()) < 50:
        return 0.0
    
    # Check for garbled text indicators
    garbled_chars = len(re.findall(r'[^\w\s\u0600-\u06FF.,;:!?؛،]', text))
    total_chars = len(text)
    
    if total_chars == 0:
        return 0.0
    
    garbled_ratio = garbled_chars / total_chars
    
    # Calculate quality score
    quality = 1.0 - (garbled_ratio * 2)  # Penalize garbled text heavily
    
    # Bonus for having actual words
    words = len(text.split())
    if words > 20:
        quality += 0.2
    
    return min(max(quality, 0.0), 1.0)

class SmartPDFExtractor:
    """
    Intelligent PDF extractor with cascade fallback
    Optimizes for speed, cost, and accuracy
    """
    
    def __init__(self, azure_endpoint=None, azure_key=None):
        self.azure_endpoint = azure_endpoint
        self.azure_key = azure_key
        self.stats = {
            'pymupdf': 0,
            'tesseract': 0,
            'azure': 0,
            'failed': 0
        }
    
    def extract(self, pdf_path: str, force_method: ExtractionMethod = None) -> Dict:
        """
        Extract text from PDF using smart cascade
        
        Returns:
            {
                'text': str,
                'method': ExtractionMethod,
                'language': Language,
                'quality': float,
                'page_count': int,
                'cost': float,
                'processing_time': float
            }
        """
        
        import time
        start_time = time.time()
        
        if force_method:
            result = self._extract_with_method(pdf_path, force_method)
        else:
            result = self._cascade_extraction(pdf_path)
        
        result['processing_time'] = time.time() - start_time
        
        # Update stats
        self.stats[result['method'].value.replace('ocr_', '')] += 1
        
        return result
    
    def _cascade_extraction(self, pdf_path: str) -> Dict:
        """Try methods in order: PyMuPDF → Tesseract → Azure"""
        
        # Tier 1: Try PyMuPDF (fast digital extraction)
        result = self._extract_pymupdf(pdf_path)
        
        if result['quality'] > 0.7:  # Good quality
            return result
        
        print(f"PyMuPDF quality low ({result['quality']:.2f}), trying Tesseract OCR...")
        
        # Tier 2: Try Tesseract OCR (free OCR)
        result = self._extract_tesseract(pdf_path)
        
        if result['quality'] > 0.6:  # Acceptable quality
            return result
        
        print(f"Tesseract quality low ({result['quality']:.2f}), trying Azure...")
        
        # Tier 3: Azure Document Intelligence (premium OCR)
        if self.azure_endpoint and self.azure_key:
            result = self._extract_azure(pdf_path)
            return result
        else:
            print("Warning: Azure credentials not configured. Using Tesseract result.")
            result['method'] = ExtractionMethod.FAILED
            return result
    
    def _extract_pymupdf(self, pdf_path: str) -> Dict:
        """Extract using PyMuPDF (for digital PDFs)"""
        
        try:
            doc = fitz.open(pdf_path)
            
            full_text = []
            page_count = len(doc)
            
            for page in doc:
                text = page.get_text()
                full_text.append(text)
            
            doc.close()
            
            combined_text = "\n\n".join(full_text)
            
            return {
                'text': combined_text,
                'method': ExtractionMethod.PYMUPDF,
                'language': detect_language(combined_text),
                'quality': assess_text_quality(combined_text),
                'page_count': page_count,
                'cost': 0.0,
                'notes': 'Digital PDF extraction'
            }
        
        except Exception as e:
            return {
                'text': '',
                'method': ExtractionMethod.FAILED,
                'language': Language.ENGLISH,
                'quality': 0.0,
                'page_count': 0,
                'cost': 0.0,
                'error': str(e)
            }
    
    def _extract_tesseract(self, pdf_path: str) -> Dict:
        """Extract using Tesseract OCR (for scanned PDFs)"""
        
        try:
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=300)
            
            full_text = []
            
            for page_num, page_image in enumerate(pages, 1):
                # OCR with Arabic + English support
                text = pytesseract.image_to_string(
                    page_image,
                    lang='ara+eng',  # Multi-language support
                    config='--psm 6'  # Assume uniform block of text
                )
                full_text.append(text)
            
            combined_text = "\n\n".join(full_text)
            
            return {
                'text': combined_text,
                'method': ExtractionMethod.TESSERACT,
                'language': detect_language(combined_text),
                'quality': assess_text_quality(combined_text),
                'page_count': len(pages),
                'cost': 0.0,
                'notes': 'Free OCR extraction'
            }
        
        except Exception as e:
            return {
                'text': '',
                'method': ExtractionMethod.FAILED,
                'language': Language.ENGLISH,
                'quality': 0.0,
                'page_count': 0,
                'cost': 0.0,
                'error': str(e)
            }
    
    def _extract_azure(self, pdf_path: str) -> Dict:
        """Extract using Azure Document Intelligence (premium)"""
        
        try:
            client = DocumentAnalysisClient(
                endpoint=self.azure_endpoint,
                credential=AzureKeyCredential(self.azure_key)
            )
            
            with open(pdf_path, "rb") as f:
                poller = client.begin_analyze_document(
                    "prebuilt-read",
                    document=f
                )
            
            result = poller.result()
            
            # Extract text while preserving structure
            full_text = []
            page_count = len(result.pages)
            
            for page in result.pages:
                page_text = []
                for line in page.lines:
                    page_text.append(line.content)
                full_text.append("\n".join(page_text))
            
            combined_text = "\n\n".join(full_text)
            
            # Calculate cost: $1.50 per 1000 pages
            cost = (page_count / 1000) * 1.50
            
            return {
                'text': combined_text,
                'method': ExtractionMethod.AZURE,
                'language': detect_language(combined_text),
                'quality': assess_text_quality(combined_text),
                'page_count': page_count,
                'cost': cost,
                'notes': 'Premium Azure OCR'
            }
        
        except Exception as e:
            return {
                'text': '',
                'method': ExtractionMethod.FAILED,
                'language': Language.ENGLISH,
                'quality': 0.0,
                'page_count': 0,
                'cost': 0.0,
                'error': str(e)
            }
    
    def get_stats(self):
        """Get extraction statistics"""
        total = sum(self.stats.values())
        if total == 0:
            return self.stats
        
        return {
            method: f"{count} ({count/total*100:.1f}%)"
            for method, count in self.stats.items()
        }

# Usage Example
def process_all_pdfs(pdf_directory: str, azure_config: Dict = None):
    """Process all PDFs in a directory with smart extraction"""
    
    from pathlib import Path
    
    # Initialize extractor
    extractor = SmartPDFExtractor(
        azure_endpoint=azure_config.get('endpoint') if azure_config else None,
        azure_key=azure_config.get('key') if azure_config else None
    )
    
    pdf_dir = Path(pdf_directory)
    results = []
    total_cost = 0.0
    
    for pdf_file in pdf_dir.glob('*.pdf'):
        print(f"\n📄 Processing: {pdf_file.name}")
        
        result = extractor.extract(str(pdf_file))
        
        print(f"   Method: {result['method'].value}")
        print(f"   Language: {result['language'].value}")
        print(f"   Quality: {result['quality']:.2f}")
        print(f"   Pages: {result['page_count']}")
        print(f"   Cost: ${result['cost']:.4f}")
        print(f"   Time: {result['processing_time']:.2f}s")
        
        total_cost += result['cost']
        results.append({
            'filename': pdf_file.name,
            'result': result
        })
    
    print(f"\n{'='*60}")
    print(f"📊 EXTRACTION STATISTICS")
    print(f"{'='*60}")
    print(f"Total documents: {len(results)}")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"\nMethod breakdown:")
    for method, stat in extractor.get_stats().items():
        print(f"  {method}: {stat}")
    
    return results
```

### Arabic Text Cleaning & Normalization

```python
# File: processors/arabic_cleaner.py

import re
from typing import str

class ArabicTextCleaner:
    """Clean and normalize Arabic text for better RAG performance"""
    
    @staticmethod
    def normalize_arabic(text: str) -> str:
        """
        Normalize Arabic text:
        - Remove diacritics (harakat)
        - Normalize hamza variants
        - Normalize alef variants
        - Remove tatweel
        """
        
        if not text:
            return text
        
        # Remove Arabic diacritics (tashkeel)
        arabic_diacritics = re.compile(r'[\u064B-\u0652\u0670]')
        text = arabic_diacritics.sub('', text)
        
        # Normalize hamza
        text = re.sub(r'[إأٱآا]', 'ا', text)  # Normalize alef variants
        text = re.sub(r'[ىئ]', 'ي', text)     # Normalize yeh
        
        # Remove tatweel (elongation character)
        text = re.sub(r'ـ', '', text)
        
        # Normalize numbers to Western Arabic (0-9)
        eastern_to_western = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        text = text.translate(eastern_to_western)
        
        return text
    
    @staticmethod
    def clean_ocr_artifacts(text: str) -> str:
        """Remove common OCR artifacts"""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers pattern
        text = re.sub(r'\n\d+\n', '\n', text)
        
        # Remove isolated single characters (often OCR errors)
        text = re.sub(r'\s[a-zA-Z]\s', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_citations(text: str) -> List[str]:
        """Extract Quranic verses and Hadith references from Arabic text"""
        
        citations = []
        
        # Pattern for Quranic references: سورة ... آية ...
        quran_pattern = r'سورة\s+(\w+)\s+آية\s+(\d+)'
        quran_matches = re.findall(quran_pattern, text)
        
        for surah, ayah in quran_matches:
            citations.append(f"القرآن: سورة {surah}، آية {ayah}")
        
        # Pattern for Hadith references
        hadith_pattern = r'(صحيح البخاري|صحيح مسلم|سنن أبي داود)'
        hadith_matches = re.findall(hadith_pattern, text)
        
        citations.extend(set(hadith_matches))
        
        return citations

# Usage
cleaner = ArabicTextCleaner()

# Example
arabic_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
cleaned = cleaner.normalize_arabic(arabic_text)  # Removes diacritics
print(cleaned)  # Output: بسم الله الرحمن الرحيم
```

### Language Detection & Router

```python
# File: processors/language_detector.py

from typing import Dict, List
import re

class LanguageDetector:
    """Detect and route multilingual queries"""
    
    @staticmethod
    def detect(text: str) -> Dict:
        """
        Detect language and provide confidence scores
        
        Returns:
            {
                'primary': 'ar|en|ms',
                'secondary': 'ar|en|ms' or None,
                'is_mixed': bool,
                'scores': {'ar': 0.7, 'en': 0.3, 'ms': 0.0}
            }
        """
        
        if not text:
            return {
                'primary': 'en',
                'secondary': None,
                'is_mixed': False,
                'scores': {'ar': 0, 'en': 0, 'ms': 0}
            }
        
        # Count character types
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # Malay-specific words (simple heuristic)
        malay_words = ['adalah', 'dengan', 'untuk', 'yang', 'ini', 'itu', 
                       'boleh', 'tidak', 'ada', 'saya', 'kita']
        malay_count = sum(1 for word in malay_words if word in text.lower())
        
        total = arabic_chars + english_chars + (malay_count * 10)
        
        if total == 0:
            return {
                'primary': 'en',
                'secondary': None,
                'is_mixed': False,
                'scores': {'ar': 0, 'en': 1.0, 'ms': 0}
            }
        
        # Calculate scores
        ar_score = arabic_chars / total
        en_score = english_chars / total
        ms_score = (malay_count * 10) / total
        
        # Determine primary language
        scores = {'ar': ar_score, 'en': en_score, 'ms': ms_score}
        primary = max(scores, key=scores.get)
        
        # Determine if mixed
        is_mixed = sum(1 for score in scores.values() if score > 0.2) > 1
        
        # Determine secondary language
        sorted_langs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        secondary = sorted_langs[1][0] if sorted_langs[1][1] > 0.2 else None
        
        return {
            'primary': primary,
            'secondary': secondary,
            'is_mixed': is_mixed,
            'scores': scores
        }
    
    @staticmethod
    def get_response_language(query_language: str, user_preference: str = None) -> str:
        """Determine which language to respond in"""
        
        if user_preference:
            return user_preference
        
        # Default: respond in same language as query
        return query_language

# Usage
detector = LanguageDetector()

# Test cases
test_queries = [
    "What is Murabaha?",
    "ما هو المرابحة؟",
    "Adakah Takaful halal?",
    "Is التورق المنظم allowed in Islamic finance?",
]

for query in test_queries:
    result = detector.detect(query)
    print(f"Query: {query}")
    print(f"Primary: {result['primary']}, Mixed: {result['is_mixed']}")
    print(f"Scores: {result['scores']}\n")
```

---

## 🔍 Part 1: Web Crawling Strategy

### 1.1 Priority Data Sources

Based on contest requirements (Slide 11), these are **mandatory sources**:

| Source | URL | Content Type | Priority |
|--------|-----|--------------|----------|
| Bank Negara Malaysia (BNM) | https://www.bnm.gov.my/shariah | Policy Documents | **HIGH** |
| AAOIFI Standards | https://aaoifi.com/ | Shariah Standards | **HIGH** |
| Securities Commission Malaysia | https://www.sc.com.my/resources/shariah | Shariah Resolutions | **HIGH** |
| JAKIM E-Fatwa | http://www.e-fatwa.gov.my/ | State Fatwas | **HIGH** |
| IIFM | https://www.iifm.net/ | Islamic Finance Standards | MEDIUM |
| Dallah Al Baraka | - | Resolutions | MEDIUM |
| State Fatwa Authorities | Various | Regional Fatwas | MEDIUM |

### 1.2 Recommended Crawling Tools

#### **Option 1: Python-Based Stack (Recommended)**

**For Structured Websites:**
```python
# Primary: Scrapy Framework
- Best for: Large-scale, structured crawling
- Pros: Fast, async, built-in middleware, robust
- Use for: BNM, SC Malaysia, IIFM websites

# Alternative: Beautiful Soup + Requests
- Best for: Simple, targeted scraping
- Pros: Easy to learn, flexible
- Use for: Small sites, quick prototypes
```

**For JavaScript-Heavy Sites:**
```python
# Playwright or Selenium
- Best for: Dynamic content, SPAs
- Pros: Full browser automation, handles JS rendering
- Use for: Modern Islamic finance portals
```

**For PDF Documents:**
```python
# PyPDF2 / pdfplumber
- Best for: Text extraction from PDFs
- Critical for: AAOIFI standards, BNM policies

# Apache Tika
- Best for: Universal document parsing
- Supports: PDF, DOCX, HTML, etc.

# Azure Document Intelligence (AI)
- Best for: OCR on scanned documents
- Pros: High accuracy, handles Arabic text
```

#### **Option 2: No-Code/Low-Code Solutions**

```yaml
Firecrawl:
  - API-based web scraping
  - Returns markdown/structured data
  - Good for: Quick POC development
  
Apify:
  - Pre-built scrapers
  - Cloud-based
  - Good for: Standard websites

Docugami:
  - Document understanding
  - Good for: PDF processing
```

### 1.3 Crawling Implementation Plan

#### **Day 1: Setup & Initial Crawling**

**Step 1: Environment Setup**
```bash
# Install dependencies
pip install scrapy beautifulsoup4 requests
pip install pdfplumber PyPDF2 python-docx
pip install playwright
pip install langchain langchain-anthropic
pip install pinecone-client chromadb

# Initialize project
scrapy startproject shariah_crawler
```

**Step 2: Build Scrapers**

```python
# Example: BNM Shariah Scraper
# File: scrapers/bnm_scraper.py

import scrapy
from scrapy.crawler import CrawlerProcess

class BNMShariah(scrapy.Spider):
    name = 'bnm_shariah'
    start_urls = [
        'https://www.bnm.gov.my/shariah',
        'https://www.bnm.gov.my/documents',
    ]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # Be polite
        'CONCURRENT_REQUESTS': 1,
    }
    
    def parse(self, response):
        # Extract PDF links
        pdf_links = response.css('a[href$=".pdf"]::attr(href)').getall()
        
        for pdf_url in pdf_links:
            yield scrapy.Request(
                url=response.urljoin(pdf_url),
                callback=self.save_pdf,
                meta={'source': 'BNM', 'url': pdf_url}
            )
    
    def save_pdf(self, response):
        filename = response.url.split('/')[-1]
        with open(f'data/pdfs/bnm_{filename}', 'wb') as f:
            f.write(response.body)
        
        yield {
            'source': 'BNM',
            'filename': filename,
            'url': response.url,
            'date_crawled': datetime.now().isoformat()
        }
```

**Step 3: PDF Processing**

```python
# File: processors/pdf_processor.py

import pdfplumber
import re
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF with metadata"""
    
    text_content = []
    metadata = {
        'source_file': pdf_path.name,
        'pages': 0,
        'has_arabic': False
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        metadata['pages'] = len(pdf.pages)
        
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            
            if text:
                # Check for Arabic content
                if re.search(r'[\u0600-\u06FF]', text):
                    metadata['has_arabic'] = True
                
                text_content.append({
                    'page': page_num,
                    'content': text,
                    'tables': page.extract_tables()
                })
    
    return {
        'text': text_content,
        'metadata': metadata
    }

def process_all_pdfs(pdf_directory):
    """Process all PDFs in directory"""
    
    pdf_dir = Path(pdf_directory)
    processed_docs = []
    
    for pdf_file in pdf_dir.glob('*.pdf'):
        print(f"Processing: {pdf_file.name}")
        
        try:
            doc_data = extract_text_from_pdf(pdf_file)
            doc_data['metadata']['source_category'] = categorize_document(pdf_file.name)
            processed_docs.append(doc_data)
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")
    
    return processed_docs

def categorize_document(filename):
    """Categorize document based on filename/content"""
    
    categories = {
        'policy': ['policy', 'guideline', 'circular'],
        'standard': ['standard', 'aaoifi', 'accounting'],
        'fatwa': ['fatwa', 'resolution', 'ruling'],
        'regulation': ['regulation', 'requirement', 'framework']
    }
    
    filename_lower = filename.lower()
    
    for category, keywords in categories.items():
        if any(kw in filename_lower for kw in keywords):
            return category
    
    return 'general'
```

#### **Day 2: Data Processing & Storage**

**Step 4: Text Chunking Strategy**

```python
# File: processors/text_chunker.py

from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_shariah_documents(documents, chunk_size=1000, overlap=200):
    """
    Intelligent chunking for Shariah documents
    Preserves context and citations
    """
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=[
            "\n\n",  # Paragraphs
            "\n",    # Lines
            ". ",    # Sentences
            ", ",    # Clauses
            " ",     # Words
        ],
        length_function=len,
    )
    
    chunked_docs = []
    
    for doc in documents:
        # Add metadata to each chunk
        chunks = text_splitter.create_documents(
            texts=[doc['content']],
            metadatas=[{
                'source': doc['source'],
                'filename': doc['filename'],
                'category': doc['category'],
                'page': doc.get('page', 'N/A'),
                'date_crawled': doc.get('date_crawled'),
            }]
        )
        
        chunked_docs.extend(chunks)
    
    return chunked_docs
```

### 1.4 Data Storage Schema

```python
# Document metadata structure
document_schema = {
    "id": "unique_doc_id",
    "source": "BNM|AAOIFI|SC|JAKIM|IIFM",
    "document_type": "policy|standard|fatwa|regulation",
    "title": "Document title",
    "content": "Full text content",
    "chunks": [
        {
            "chunk_id": "chunk_unique_id",
            "text": "Chunk content",
            "page_number": 5,
            "section": "Section name"
        }
    ],
    "metadata": {
        "author": "Issuing authority",
        "date_published": "ISO date",
        "language": "en|ms|ar",
        "url": "Source URL",
        "pdf_path": "Local file path",
        "has_arabic": True,
        "category": "muamalat|takaful|banking"
    },
    "embedding_id": "Vector DB ID",
    "date_indexed": "ISO date"
}
```

---

## 🤖 Part 2: Multilingual AI Chatbot Architecture

### 2.1 Enhanced Tech Stack (with Multilingual Support)

#### **Full Stack Architecture**

```yaml
Frontend:
  Option 1 (Web): 
    - Next.js 14 + React
    - Tailwind CSS + RTL support for Arabic
    - Shadcn/ui components
    - i18next for translations
  
  Option 2 (Mobile-First):
    - Flutter Web/Mobile
    - Material Design 3
    - Built-in RTL support

Backend:
  Framework: FastAPI (Python 3.11+)
  Async: asyncio + uvicorn
  API Gateway: Optional (NGINX)
  Language Detection: langdetect + custom detector

AI/ML Layer:
  LLM Provider: Claude 3.5 Sonnet (Anthropic API)
  - Excellent Arabic understanding
  - Supports 100+ languages natively
  - Context window: 200K tokens
  
  Orchestration: LangChain
  Alternative: LlamaIndex
  
Vector Database:
  Option 1 (Managed): Pinecone (Recommended for POC)
  Option 2 (Open Source): Qdrant or Weaviate
  Option 3 (Embedded): ChromaDB (for demo)
  
  Note: All support multilingual embeddings!

Embeddings:
  Primary: text-embedding-3-large (OpenAI)
  - Dimension: 3072
  - Supports 100+ languages including Arabic
  - Best performance for mixed-language docs
  
  Alternative: multilingual-e5-large (Open source)
  - Free but requires local hosting

OCR Services:
  Primary: PyMuPDF (Digital PDFs)
  Secondary: Tesseract (Free OCR)
  Fallback: Azure Document Intelligence (Premium)

Caching:
  Redis (Optional, for performance)
  - Cache common queries in all languages

Deployment:
  POC: Railway, Render, or Vercel
  Production: AWS/Azure (your existing cloud)
```

### 2.2 Multilingual RAG Pipeline

#### **Enhanced Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY (Trilingual)                  │
│   EN: "Is this investment halal?"                           │
│   AR: "هل هذا الاستثمار حلال؟"                              │
│   MS: "Adakah pelaburan ini halal?"                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              LANGUAGE DETECTION & ROUTING                   │
│  • Detect primary language (AR/EN/MS)                       │
│  • Identify mixed-language queries                          │
│  • Set response language preference                         │
│  • Normalize Arabic text (remove diacritics)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  QUERY PROCESSING                           │
│  • Intent Classification                                    │
│  • Query Expansion (multilingual synonyms)                  │
│  • Translation if needed (for better search)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          MULTILINGUAL EMBEDDING GENERATION                  │
│  Convert query to vector using multilingual model           │
│  (Works seamlessly across AR/EN/MS)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         CROSS-LINGUAL VECTOR SEARCH                         │
│  Search Pinecone for relevant chunks in ANY language        │
│  • Top K = 8-10 chunks (mixed languages OK)                 │
│  • Metadata filtering (source, category, language)          │
│  • Semantic search works across languages!                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              CONTEXT RETRIEVAL                              │
│  Retrieved Documents (may be in different languages):       │
│  1. BNM Policy (EN) - 95% match                             │
│  2. AAOIFI Standard (AR) - 93% match                        │
│  3. SC Resolution (EN+MS) - 90% match                       │
│  4. JAKIM Fatwa (AR+MS) - 88% match                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              RE-RANKING (Optional)                          │
│  • Cross-encoder reranking                                  │
│  • Relevance scoring                                        │
│  • Language diversity balancing                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           MULTILINGUAL PROMPT CONSTRUCTION                  │
│  • System: Expert trilingual Shariah advisor               │
│  • Context: Mixed AR/EN/MS documents                        │
│  • Instruction: Respond in user's language                  │
│  • Special: Handle Arabic citations with translation        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              CLAUDE 3.5 SONNET GENERATION                   │
│  Claude generates response with:                            │
│  • Shariah ruling in requested language                     │
│  • Legal reasoning (ta'lil)                                 │
│  • Citations from sources (original + translation)          │
│  • Arabic text preserved when citing Arabic sources         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           RESPONSE POST-PROCESSING                          │
│  • Format citations with dual language                      │
│  • Add confidence scoring                                   │
│  • Verify source authenticity                               │
│  • Apply RTL formatting for Arabic text                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 TRILINGUAL RESPONSE                         │
│  Answer in user's language                                  │
│  + Original Arabic citations                                │
│  + English translations                                     │
│  + Source attribution                                       │
│  + Confidence level                                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Implementation Code

#### **Step 1: Enhanced Vector Database Setup**

```python
# File: vector_db/multilingual_pinecone_setup.py

import os
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document
from processors.arabic_cleaner import ArabicTextCleaner
from processors.language_detector import LanguageDetector

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index with higher dimension for multilingual embeddings
index_name = "shariah-multilingual-kb"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=3072,  # text-embedding-3-large dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Initialize multilingual embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=os.getenv("OPENAI_API_KEY")
    # Automatically handles Arabic, English, Malay!
)

# Create vector store
vector_store = PineconeVectorStore(
    index_name=index_name,
    embedding=embeddings
)

# Initialize utilities
cleaner = ArabicTextCleaner()
detector = LanguageDetector()

def prepare_document_for_indexing(text: str, metadata: dict) -> str:
    """
    Prepare document text for indexing
    - Normalize Arabic text
    - Clean OCR artifacts
    - Preserve important formatting
    """
    
    # Detect language
    lang_info = detector.detect(text)
    metadata['detected_language'] = lang_info['primary']
    metadata['is_mixed_language'] = lang_info['is_mixed']
    
    # If contains Arabic, normalize it
    if lang_info['scores']['ar'] > 0.1:
        text = cleaner.normalize_arabic(text)
        
        # Extract and store Quranic/Hadith citations
        citations = cleaner.extract_citations(text)
        if citations:
            metadata['islamic_citations'] = citations
    
    # Clean OCR artifacts
    text = cleaner.clean_ocr_artifacts(text)
    
    return text

def index_multilingual_documents(chunked_docs):
    """
    Index processed multilingual documents into Pinecone
    with enhanced metadata for language filtering
    """
    
    documents = []
    
    for chunk in chunked_docs:
        # Prepare text
        prepared_text = prepare_document_for_indexing(
            chunk['text'],
            chunk['metadata']
        )
        
        # Create enhanced metadata
        enhanced_metadata = {
            'source': chunk['metadata']['source'],
            'filename': chunk['metadata']['filename'],
            'category': chunk['metadata']['category'],
            'page': chunk['metadata']['page'],
            'chunk_id': chunk['chunk_id'],
            'language': chunk['metadata'].get('detected_language', 'en'),
            'is_mixed': chunk['metadata'].get('is_mixed_language', False),
            'extraction_method': chunk['metadata'].get('extraction_method', 'digital'),
            'quality_score': chunk['metadata'].get('quality', 1.0),
        }
        
        # Add Islamic citations if present
        if 'islamic_citations' in chunk['metadata']:
            enhanced_metadata['has_quran'] = any('القرآن' in c for c in chunk['metadata']['islamic_citations'])
            enhanced_metadata['has_hadith'] = any('صحيح' in c for c in chunk['metadata']['islamic_citations'])
        
        doc = Document(
            page_content=prepared_text,
            metadata=enhanced_metadata
        )
        documents.append(doc)
    
    # Batch upload to Pinecone
    print(f"Indexing {len(documents)} multilingual document chunks...")
    vector_store.add_documents(documents, batch_size=100)
    
    print(f"✅ Successfully indexed {len(documents)} chunks")
    
    # Print language distribution
    lang_counts = {}
    for doc in documents:
        lang = doc.metadata.get('language', 'unknown')
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
    
    print("\n📊 Language Distribution:")
    for lang, count in lang_counts.items():
        print(f"  {lang}: {count} chunks ({count/len(documents)*100:.1f}%)")
    
    return True
```

#### **Step 2: Multilingual RAG Chain**

```python
# File: ai/multilingual_rag_chain.py

from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from vector_db.multilingual_pinecone_setup import vector_store
from processors.language_detector import LanguageDetector
import os

# Initialize Claude
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0.2,  # Lower for more factual responses
    max_tokens=3000   # Higher for detailed Arabic responses
)

detector = LanguageDetector()

# Multilingual Shariah prompt template
MULTILINGUAL_SHARIAH_PROMPT = """You are an expert AI assistant specialized in Islamic Finance and Shariah compliance. You are fluent in Arabic (العربية), English, and Bahasa Melayu.

Your role is to provide accurate, well-reasoned answers based on authentic Shariah sources from multiple languages.

Context from Shariah Sources (may include Arabic, English, and Malay):
{context}

User Question ({query_language}): {question}

Instructions:
1. Provide a clear, accurate answer based ONLY on the provided context
2. Cite specific sources (BNM, AAOIFI, SC, JAKIM) when making claims
3. When citing Arabic sources, include BOTH:
   - Original Arabic text (in Arabic script)
   - English translation in brackets
4. Use proper Islamic finance terminology
5. If the context doesn't contain enough information, state this clearly
6. Provide the Shariah reasoning (ta'lil/التعليل) behind the ruling
7. Respond in {response_language}
8. Maintain academic rigor and precision

Citation Format:
For Arabic sources: [Source: AAOIFI Standard #17, Section 2.3]
Arabic: "التورق المنظم جائز بشروط معينة"
Translation: [Organized Tawarruq is permissible under specific conditions]

For English sources: [Source: BNM Shariah Policy 2023, Section 4.2]

For Mixed sources: Cite both languages appropriately

Answer:"""

def create_multilingual_prompt(query_language: str, response_language: str = None):
    """Create prompt template with language context"""
    
    if not response_language:
        response_language = query_language
    
    # Language name mapping
    lang_names = {
        'ar': 'Arabic (العربية)',
        'en': 'English',
        'ms': 'Bahasa Melayu'
    }
    
    prompt = PromptTemplate(
        template=MULTILINGUAL_SHARIAH_PROMPT,
        input_variables=["context", "question"],
        partial_variables={
            "query_language": lang_names.get(query_language, 'English'),
            "response_language": lang_names.get(response_language, 'English')
        }
    )
    
    return prompt

class MultilingualShariah RAG:
    """Trilingual Shariah RAG system"""
    
    def __init__(self):
        self.llm = llm
        self.vector_store = vector_store
        self.detector = detector
    
    def query(self, question: str, language_preference: str = None, 
              filter_language: str = None, top_k: int = 8):
        """
        Query the multilingual Shariah knowledge base
        
        Args:
            question: User's question (any language)
            language_preference: Preferred response language ('ar', 'en', 'ms')
            filter_language: Filter sources by language (None = all languages)
            top_k: Number of relevant chunks to retrieve
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        
        # Detect query language
        lang_info = self.detector.detect(question)
        query_language = lang_info['primary']
        
        # Determine response language
        if not language_preference:
            language_preference = query_language
        
        # Create customized prompt
        prompt = create_multilingual_prompt(query_language, language_preference)
        
        # Setup retrieval with optional language filtering
        search_kwargs = {"k": top_k}
        
        if filter_language:
            search_kwargs["filter"] = {"language": filter_language}
        
        # Create RAG chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs=search_kwargs
            ),
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        # Execute query
        result = qa_chain.invoke({"query": question})
        
        # Process and format response
        response = self._format_response(
            result, 
            query_language, 
            language_preference
        )
        
        return response
    
    def _format_response(self, result, query_lang, response_lang):
        """Format response with multilingual metadata"""
        
        # Extract source documents
        sources = []
        languages_found = set()
        
        for doc in result["source_documents"]:
            doc_lang = doc.metadata.get("language", "en")
            languages_found.add(doc_lang)
            
            source_info = {
                "source": doc.metadata.get("source"),
                "filename": doc.metadata.get("filename"),
                "page": doc.metadata.get("page"),
                "language": doc_lang,
                "category": doc.metadata.get("category"),
                "content_snippet": doc.page_content[:300] + "...",
                "quality": doc.metadata.get("quality_score", 1.0)
            }
            
            # Add Islamic citations if present
            if doc.metadata.get("has_quran"):
                source_info["contains_quran"] = True
            if doc.metadata.get("has_hadith"):
                source_info["contains_hadith"] = True
            
            sources.append(source_info)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            result["source_documents"],
            query_lang,
            languages_found
        )
        
        return {
            "answer": result["result"],
            "sources": sources,
            "confidence": confidence,
            "metadata": {
                "query_language": query_lang,
                "response_language": response_lang,
                "languages_in_sources": list(languages_found),
                "cross_lingual": len(languages_found) > 1,
                "source_count": len(sources)
            }
        }
    
    def _calculate_confidence(self, source_docs, query_lang, langs_found):
        """
        Calculate confidence based on:
        - Number and quality of sources
        - Language match
        - Source diversity
        """
        
        if not source_docs:
            return "Low"
        
        # Base score from number of sources
        base_score = min(len(source_docs) / 5, 1.0)
        
        # Bonus for multiple languages (cross-validation)
        cross_lingual_bonus = 0.2 if len(langs_found) > 1 else 0
        
        # Bonus for high quality sources
        avg_quality = sum(
            doc.metadata.get("quality_score", 1.0) 
            for doc in source_docs
        ) / len(source_docs)
        quality_bonus = (avg_quality - 0.7) * 0.3
        
        # Calculate final score
        final_score = base_score + cross_lingual_bonus + quality_bonus
        
        if final_score >= 0.8:
            return "Very High"
        elif final_score >= 0.6:
            return "High"
        elif final_score >= 0.4:
            return "Medium"
        else:
            return "Low"

# Initialize the multilingual RAG system
rag_system = MultilingualShariah RAG()

def query_trilingual_chatbot(question: str, 
                            language_preference: str = None,
                            filter_by_language: str = None):
    """
    Main function to query the trilingual chatbot
    
    Examples:
        # Ask in English, get English response
        query_trilingual_chatbot("Is Murabaha allowed?")
        
        # Ask in Arabic, get Arabic response  
        query_trilingual_chatbot("ما هو حكم المضاربة؟")
        
        # Ask in English, request Arabic response
        query_trilingual_chatbot("What is Takaful?", language_preference='ar')
        
        # Filter to only Arabic sources
        query_trilingual_chatbot("Is Tawarruq halal?", filter_by_language='ar')
    """
    
    return rag_system.query(
        question=question,
        language_preference=language_preference,
        filter_language=filter_by_language
    )
```

#### **Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                         USER QUERY                          │
│              "Is this investment halal?"                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  QUERY PROCESSING                           │
│  • Intent Classification                                    │
│  • Query Expansion                                          │
│  • Language Detection (EN/MS/AR)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              EMBEDDING GENERATION                           │
│  Convert query to vector using embedding model              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            VECTOR SIMILARITY SEARCH                         │
│  Search Pinecone/Qdrant for relevant chunks                 │
│  • Top K = 5-10 most relevant chunks                        │
│  • Metadata filtering (source, category)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              CONTEXT RETRIEVAL                              │
│  Retrieved Documents:                                       │
│  1. BNM Policy on Shariah Governance (95% match)            │
│  2. AAOIFI Standard #17 on Investment (92% match)           │
│  3. SC Resolution on Equity Screening (88% match)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              RE-RANKING (Optional)                          │
│  • Cross-encoder reranking                                  │
│  • Relevance scoring                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           PROMPT CONSTRUCTION                               │
│  System Prompt + Retrieved Context + User Query             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM GENERATION                                 │
│  Claude 3.5 Sonnet generates response with:                 │
│  • Shariah ruling                                           │
│  • Legal reasoning                                          │
│  • Citations from sources                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           RESPONSE POST-PROCESSING                          │
│  • Citation formatting                                      │
│  • Confidence scoring                                       │
│  • Source verification                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    USER RESPONSE                            │
│  Answer + Citations + Confidence Level                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Implementation Code

#### **Step 1: Vector Database Setup**

```python
# File: vector_db/pinecone_setup.py

import os
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import Document

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Create index
index_name = "shariah-knowledge-base"

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI embedding dimension
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Initialize embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create vector store
vector_store = PineconeVectorStore(
    index_name=index_name,
    embedding=embeddings
)

def index_documents(chunked_docs):
    """Index processed documents into Pinecone"""
    
    documents = []
    
    for chunk in chunked_docs:
        doc = Document(
            page_content=chunk['text'],
            metadata={
                'source': chunk['source'],
                'filename': chunk['filename'],
                'category': chunk['category'],
                'page': chunk['page'],
                'chunk_id': chunk['chunk_id']
            }
        )
        documents.append(doc)
    
    # Batch upload to Pinecone
    vector_store.add_documents(documents)
    
    print(f"Indexed {len(documents)} document chunks")
    
    return True
```

#### **Step 2: RAG Chain Implementation**

```python
# File: ai/rag_chain.py

from langchain_anthropic import ChatAnthropic
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from vector_db.pinecone_setup import vector_store

# Initialize Claude
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0.3,  # Lower for more factual responses
    max_tokens=2000
)

# Custom prompt template for Shariah queries
SHARIAH_PROMPT_TEMPLATE = """You are an expert AI assistant specialized in Islamic Finance and Shariah compliance. Your role is to provide accurate, well-reasoned answers based on authentic Shariah sources.

Context from Shariah Sources:
{context}

User Question: {question}

Instructions:
1. Provide a clear, accurate answer based ONLY on the provided context
2. Cite specific sources (BNM, AAOIFI, SC, JAKIM) when making claims
3. Use proper Islamic finance terminology
4. If the context doesn't contain enough information, state this clearly
5. Provide the Shariah reasoning (ta'lil) behind the ruling
6. Format citations as: [Source: BNM Policy 2023, Section 4.2]

Answer:"""

prompt = PromptTemplate(
    template=SHARIAH_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)

# Create RAG chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}  # Retrieve top 5 relevant chunks
    ),
    chain_type_kwargs={"prompt": prompt},
    return_source_documents=True
)

def query_shariah_chatbot(user_question):
    """Main function to query the chatbot"""
    
    result = qa_chain.invoke({"query": user_question})
    
    response = {
        "answer": result["result"],
        "sources": [
            {
                "source": doc.metadata.get("source"),
                "filename": doc.metadata.get("filename"),
                "page": doc.metadata.get("page"),
                "content_snippet": doc.page_content[:200] + "..."
            }
            for doc in result["source_documents"]
        ],
        "confidence": calculate_confidence(result["source_documents"])
    }
    
    return response

def calculate_confidence(source_docs):
    """Calculate confidence based on source quality and quantity"""
    
    # Simple heuristic
    if len(source_docs) >= 3:
        return "High"
    elif len(source_docs) >= 1:
        return "Medium"
    else:
        return "Low"
```

#### **Step 3: FastAPI Backend**

```python
# File: main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ai.rag_chain import query_shariah_chatbot
import uvicorn

app = FastAPI(
    title="BarakahVault Shariah AI Assistant",
    description="AI-powered Shariah compliance chatbot",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    user_id: str | None = None
    session_id: str | None = None

class QueryResponse(BaseModel):
    answer: str
    sources: list
    confidence: str
    timestamp: str

@app.get("/")
async def root():
    return {
        "message": "BarakahVault Shariah AI API",
        "status": "operational",
        "version": "1.0.0"
    }

@app.post("/api/query", response_model=QueryResponse)
async def chat_query(request: QueryRequest):
    """
    Main chatbot endpoint
    """
    try:
        if not request.question or len(request.question.strip()) == 0:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Query the RAG system
        result = query_shariah_chatbot(request.question)
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/stats")
async def get_stats():
    """Get knowledge base statistics"""
    # TODO: Implement stats from vector DB
    return {
        "total_documents": 0,
        "total_chunks": 0,
        "sources": ["BNM", "AAOIFI", "SC", "JAKIM"]
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

#### **Step 4: Frontend (React/Next.js)**

```typescript
// File: app/page.tsx

'use client'

import { useState } from 'react'

interface Source {
  source: string
  filename: string
  page: string
  content_snippet: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  confidence?: string
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: input,
          session_id: 'demo-session'
        })
      })

      const data = await response.json()

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        confidence: data.confidence
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      <header className="mb-4">
        <h1 className="text-3xl font-bold">BarakahVault Shariah Assistant</h1>
        <p className="text-gray-600">AI-powered Islamic Finance Compliance</p>
      </header>

      <div className="flex-1 overflow-y-auto mb-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`p-4 rounded-lg ${
              msg.role === 'user' 
                ? 'bg-blue-100 ml-auto max-w-[80%]' 
                : 'bg-gray-100 mr-auto max-w-[80%]'
            }`}
          >
            <p className="whitespace-pre-wrap">{msg.content}</p>
            
            {msg.sources && msg.sources.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-300">
                <p className="text-sm font-semibold mb-2">Sources:</p>
                {msg.sources.map((source, i) => (
                  <div key={i} className="text-xs text-gray-700 mb-1">
                    📄 {source.source} - {source.filename} (Page {source.page})
                  </div>
                ))}
                <p className="text-xs mt-2">
                  Confidence: <span className="font-semibold">{msg.confidence}</span>
                </p>
              </div>
            )}
          </div>
        ))}
        
        {loading && (
          <div className="bg-gray-100 p-4 rounded-lg max-w-[80%]">
            <p className="animate-pulse">Analyzing Shariah sources...</p>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask about Shariah compliance..."
          className="flex-1 p-3 border rounded-lg"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  )
}
```

---

## 📊 Part 3: Innovation Features (30% Criteria)

### 3.1 Core Innovation: Trilingual Shariah Intelligence

#### **🌟 Primary Innovation - What Makes Us Different**

```yaml
Trilingual AI Assistant (Industry First):
  Capabilities:
    - Accepts queries in Arabic, English, Malay
    - Searches 1000+ documents across all 3 languages simultaneously
    - Provides answers with original Arabic citations + translations
    - Handles mixed-language documents seamlessly
    - Preserves authentic Shariah terminology in Arabic
  
  Technical Innovation:
    - Cross-lingual semantic search
    - Smart OCR cascade (Digital → Free OCR → Premium OCR)
    - Arabic text normalization for better matching
    - Language-aware confidence scoring
  
  Business Value:
    - Serves Malaysian market (EN/MS users) + GCC market (AR users)
    - First AI to cite original Arabic fatwas directly
    - Reduces translation errors in Shariah rulings
    - Appeals to scholars who prefer Arabic sources
    - Differentiates from English-only competitors
  
  Demo Impact:
    - Show live queries in all 3 languages
    - Display Arabic citations with translations
    - Prove cross-lingual understanding
    - Judges will be VERY impressed! 🎯
```

### 3.2 Additional Innovation Features

#### **Feature 1: Maqasid al-Shariah Scoring Engine**

```python
# Maqasid-based investment scoring
class MaqasidScorer:
    """
    Rate investments against the 5 Maqasid al-Shariah
    First AI to use this classical framework!
    """
    
    MAQASID = {
        'hifdh_al_din': 'Preservation of Faith',      # حفظ الدين
        'hifdh_al_nafs': 'Preservation of Life',       # حفظ النفس
        'hifdh_al_aql': 'Preservation of Intellect',   # حفظ العقل
        'hifdh_al_nasl': 'Preservation of Lineage',    # حفظ النسل
        'hifdh_al_mal': 'Preservation of Wealth',      # حفظ المال
    }
    
    def score_investment(self, investment_details, shariah_context):
        """
        Score investment against each Maqasid (0-100 each)
        
        Returns visual dashboard with reasoning
        """
        scores = {}
        
        for maqsid, description in self.MAQASID.items():
            # Use Claude to analyze against this Maqsid
            score = self._analyze_maqsid(
                investment_details,
                maqsid,
                shariah_context
            )
            scores[maqsid] = score
        
        return {
            'overall_score': sum(scores.values()) / len(scores),
            'individual_scores': scores,
            'recommendation': self._generate_recommendation(scores),
            'shariah_compliance': self._determine_compliance(scores)
        }

# Demo: Score a stock/investment
result = scorer.score_investment(
    investment_details="Technology company producing AI chatbots",
    shariah_context=retrieved_fatwas
)

# Output shows score for each Maqsid with visual chart!
```

**Innovation Value:**
- First AI to use classical Islamic framework
- Goes beyond binary halal/haram
- Provides nuanced ethical analysis
- Appeals to serious Islamic finance professionals

#### **Feature 2: Real-Time Fatwa Update System**

```python
class FatwaMonitor:
    """
    Auto-crawl and index new fatwas weekly
    Users get latest rulings automatically!
    """
    
    def monitor_sources(self):
        """Check for new documents weekly"""
        
        sources_to_monitor = [
            'https://www.bnm.gov.my/shariah',
            'http://www.e-fatwa.gov.my/',
            'https://www.sc.com.my/resources/shariah',
        ]
        
        new_documents = self.crawl_for_updates(sources_to_monitor)
        
        if new_documents:
            # Auto-process and index
            self.process_and_index(new_documents)
            
            # Notify users
            self.notify_subscribers(new_documents)
        
    def notify_subscribers(self, new_docs):
        """Email/push notification about new fatwas"""
        
        notification = f"""
        🆕 New Shariah Rulings Available!
        
        {len(new_docs)} new documents indexed:
        - {new_docs[0]['title']} (BNM)
        - {new_docs[1]['title']} (JAKIM)
        
        Ask about them now in the chatbot!
        """
        
        # Send to subscribers
```

**Innovation Value:**
- Knowledge base stays current
- Users don't miss important rulings
- Automated workflow = low maintenance
- Critical for compliance professionals

#### **Feature 3: Document Analysis & Contract Screening**

```python
def analyze_contract(contract_text: str, contract_type: str):
    """
    Upload a contract/agreement for Shariah screening
    
    Supports: Investment agreements, Murabaha contracts, 
              Mudharabah agreements, Partnership documents
    """
    
    # Extract key clauses
    clauses = extract_legal_clauses(contract_text)
    
    # Check each clause against Shariah standards
    results = []
    
    for clause in clauses:
        shariah_check = rag_system.query(
            f"Is this clause Shariah compliant? {clause['text']}"
        )
        
        results.append({
            'clause': clause['text'],
            'compliant': shariah_check['compliant'],
            'issues': shariah_check['issues'],
            'recommendations': shariah_check['recommendations'],
            'sources': shariah_check['sources']
        })
    
    # Generate compliance report
    return generate_compliance_report(results)

# Demo: Upload a Murabaha contract
report = analyze_contract(
    contract_text=uploaded_contract,
    contract_type="murabaha"
)

# Get detailed compliance report with issues highlighted!
```

**Innovation Value:**
- Practical tool for practitioners
- Saves hours of manual review
- Reduces compliance risk
- Monetization opportunity (premium feature)

#### **Feature 4: Comparative Fatwa Analysis**

```yaml
Feature: Show how different authorities rule on same issue

Example Query: "Compare AAOIFI vs BNM on Tawarruq"

Response Format:
  AAOIFI Position:
    - Ruling: Permissible with conditions
    - Source: [Standard #30, Section 4]
    - Key Conditions: ...
    
  BNM Position:
    - Ruling: Permissible
    - Source: [Shariah Policy 2023, Section 5.2]
    - Key Conditions: ...
  
  Consensus: Both allow Tawarruq
  Differences: AAOIFI adds stricter conditions on ...
  
  Scholar Opinions:
    - Dr. Abdul Rahman: Agrees with AAOIFI
    - Mufti Hassan: Prefers commodity Tawarruq
    
Innovation Value:
  - Shows nuance in Islamic jurisprudence
  - Helps users understand different schools of thought
  - Builds trust through transparency
  - Educational for students/researchers
```

#### **Feature 5: Voice Input (Whisper API Integration)**

```python
# Voice queries in Arabic/English/Malay!
import openai

def voice_to_text(audio_file, language='ar'):
    """Convert speech to text using Whisper"""
    
    audio = open(audio_file, 'rb')
    
    transcript = openai.Audio.transcribe(
        model="whisper-1",
        file=audio,
        language=language  # 'ar', 'en', 'ms'
    )
    
    # Now query the chatbot
    result = query_trilingual_chatbot(transcript.text)
    
    return result

# Demo: Ask questions by speaking in Arabic!
```

**Innovation Value:**
- Accessibility (easier than typing Arabic)
- Mobile-first experience
- Appeals to busy professionals
- Great for demo (wow factor!)

#### **Feature 6: Portfolio/Stock Screening**

```python
def screen_portfolio(stock_tickers: List[str]):
    """
    Bulk Shariah compliance screening
    Check 100+ stocks in seconds!
    """
    
    results = []
    
    for ticker in stock_tickers:
        # Get company info
        company_info = get_company_data(ticker)
        
        # Screen against AAOIFI criteria
        shariah_status = check_shariah_compliance(
            industry=company_info['industry'],
            debt_ratio=company_info['debt_ratio'],
            haram_revenue=company_info['haram_revenue_pct']
        )
        
        results.append({
            'ticker': ticker,
            'company': company_info['name'],
            'status': shariah_status['compliant'],
            'issues': shariah_status['issues'],
            'sources': shariah_status['sources']
        })
    
    return generate_screening_report(results)

# Demo: Screen entire portfolio
portfolio = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
report = screen_portfolio(portfolio)

# Get instant Shariah compliance report!
```

**Innovation Value:**
- Huge time saver for fund managers
- Clear monetization path (B2B SaaS)
- Solves real pain point
- Recurring revenue model

### 3.3 Business Model Innovation

#### **Revenue Streams**

```yaml
Tier 1 - Free (Freemium):
  Price: $0/month
  Features:
    - 10 queries per day
    - Basic chatbot (single language)
    - Public knowledge base only
    - Community support
  Target: Individual Muslims, students
  Goal: User acquisition & brand awareness

Tier 2 - Professional:
  Price: RM 49/month (~$12/month)
  Features:
    - Unlimited queries
    - Trilingual support (AR/EN/MS)
    - Document upload (5 docs/month)
    - Email support
    - Export citations
  Target: Shariah advisors, finance professionals
  Goal: Primary revenue source

Tier 3 - Enterprise:
  Price: RM 499/month (~$120/month)
  Features:
    - Everything in Pro
    - API access (10,000 calls/month)
    - Custom knowledge base training
    - Priority support
    - White-label option
    - Dedicated account manager
  Target: Islamic banks, Takaful companies, fintech
  Goal: High-value recurring revenue

Tier 4 - Custom/API:
  Price: Custom pricing
  Features:
    - Pay-per-query API
    - On-premise deployment
    - Custom model training
    - SLA guarantees
  Target: Large financial institutions
  Goal: Whale customers

Additional Revenue:
  - Document analysis: RM 20 per contract
  - Portfolio screening: RM 0.10 per stock
  - Consultation marketplace: 15% commission
  - Training & workshops: RM 2,000 per session
```

#### **Target Market Size**

```yaml
Malaysian Market:
  Islamic Banking Assets: RM 1.2 trillion
  Number of Islamic Banks: 16
  Shariah Advisors: ~500+
  Islamic Finance Professionals: 10,000+
  
  TAM (Total Addressable Market):
    - All Islamic finance professionals globally
    - ~500,000 people
    - If 1% convert at RM 49/month = RM 245K/month
  
  SAM (Serviceable Addressable Market):
    - Malaysian + GCC Islamic finance sector
    - ~100,000 professionals
  
  SOM (Serviceable Obtainable Market - Year 1):
    - Target: 1,000 paying users
    - Revenue: RM 49K/month = RM 588K/year
    - + Enterprise: 10 customers @ RM 499/month = RM 60K/year
    - Total Year 1: ~RM 650K (~$155K)

Growth Markets:
  - Indonesia: World's largest Muslim population
  - UAE/Saudi: Wealthy GCC market
  - Pakistan: Growing Islamic finance
  - Turkey: Emerging market
  
  Global Islamic Finance: $3.8 trillion (2024)
  Growing at 10-12% annually
```

#### **Go-to-Market Strategy**

```yaml
Phase 1 (Months 1-3): Launch & Validation
  - Launch free tier
  - Target: Malaysian Islamic finance LinkedIn groups
  - Partnerships: IBFIM, ISRA, AIBIM
  - Goal: 1,000 free users
  
Phase 2 (Months 4-6): Monetization
  - Launch Pro tier (RM 49/month)
  - Target: Shariah advisors, consultants
  - Content marketing: Islamic finance blogs
  - Goal: 100 paying users
  
Phase 3 (Months 7-12): Enterprise
  - Pitch to Islamic banks
  - Pilot programs with 3-5 institutions
  - Case studies & testimonials
  - Goal: 5 enterprise customers
  
Phase 4 (Year 2): Regional Expansion
  - Enter GCC market (UAE, Saudi)
  - Localize for Arabic-primary users
  - Partnership with AAOIFI
  - Goal: 500 paying users, 15 enterprise
```

### 3.4 Unique Value Propositions

```yaml
For Shariah Advisors:
  Problem: Hours spent researching fatwas across sources
  Solution: Instant access to cross-referenced rulings
  Value: Save 10+ hours per week
  
For Islamic Banks:
  Problem: Compliance risk from missed regulations
  Solution: Auto-updated knowledge base with alerts
  Value: Reduce compliance violations
  
For Investors:
  Problem: Uncertain if investments are halal
  Solution: Instant Shariah screening with sources
  Value: Confidence + peace of mind
  
For Fintech Startups:
  Problem: Need Shariah validation for products
  Solution: API integration for compliance checks
  Value: Faster product development
  
For Students/Researchers:
  Problem: Limited access to Arabic Shariah texts
  Solution: Trilingual search with translations
  Value: Better research quality
```

### 3.5 Competitive Advantages

```yaml
1. Trilingual Capability:
   - Only solution handling Arabic/English/Malay
   - Direct access to original Arabic fatwas
   - Competitor: English-only chatbots (generic)
   
2. Authoritative Sources:
   - BNM, AAOIFI, SC, JAKIM official docs
   - Competitor: Generic web scraping
   
3. Malaysian Focus:
   - Optimized for local regulations
   - Partnerships with local institutions
   - Competitor: Generic global solutions
   
4. Real-Time Updates:
   - Auto-sync with new regulations
   - Competitor: Static knowledge bases
   
5. Citation Transparency:
   - Every answer sourced
   - Audit trail for compliance
   - Competitor: Black-box AI responses
   
6. Scholar-Verified:
   - Partnership path with JAKIM/AIBIM
   - Human validation layer
   - Competitor: Pure AI (no human oversight)
```

---

## 🗓️ Part 4: 3-Day Implementation Timeline (Optimized for Beginners)

### Updated Strategy for New Developers

**Key Changes:**
- Focus on DEMO quality over code complexity
- Use pre-built tools where possible
- Prioritize Arabic handling (your competitive advantage!)
- Allocate time for pitch preparation

### Day 1 (Jan 20): Data Collection & Arabic Processing
**Morning (4 hours): Environment & Tool Setup**
```bash
# Hour 1: Install dependencies
pip install scrapy beautifulsoup4 requests
pip install pdfplumber PyPDF2 pymupdf
pip install pytesseract pdf2image
pip install langchain langchain-anthropic langchain-openai
pip install pinecone-client
pip install azure-ai-formrecognizer  # For Arabic OCR

# Install Tesseract with Arabic support
sudo apt-get install tesseract-ocr tesseract-ocr-ara

# Hour 2: Setup API keys
# - Anthropic API (Claude)
# - OpenAI API (Embeddings)
# - Pinecone (Vector DB)
# - Azure (OCR - optional but recommended)

# Hour 3-4: Build basic scrapers
# Start with simple requests + BeautifulSoup
# Target: Download 20-30 PDFs from BNM/AAOIFI websites
```

**Afternoon (4 hours): Arabic PDF Processing**
```python
# Hour 5-6: Test PDF extraction with Arabic
# Try SmartPDFExtractor on sample documents
# Verify Arabic text is extracted correctly

# Hour 7-8: Process all downloaded PDFs
# Run extraction pipeline
# Save results to JSON files
# Quality check: Manual review of 5 documents

# Expected output:
# - 20-30 processed documents
# - Mix of Arabic and English text
# - Metadata (source, language, pages)
```

**Evening (2 hours): Data Preparation**
```python
# Hour 9-10: Text chunking and cleaning
# - Normalize Arabic text (remove diacritics)
# - Chunk documents (1000 chars per chunk)
# - Prepare for indexing
# - Save processed chunks to disk

# Quality Gate:
# ✓ At least 200 text chunks ready
# ✓ Arabic text readable (spot check)
# ✓ Metadata attached to each chunk
```

**Day 1 Deliverables:**
- ✅ 20-30 PDF documents collected
- ✅ Text extracted (Arabic + English)
- ✅ 200+ document chunks prepared
- ✅ Development environment fully setup

---

### Day 2 (Jan 21): AI System Development & Integration
**Morning (4 hours): Vector Database Setup**
```python
# Hour 1-2: Pinecone setup and testing
# - Create index
# - Test embedding generation
# - Upload sample documents

# Hour 3-4: Bulk indexing
# - Index all 200+ chunks
# - Verify retrieval works
# - Test multilingual search
#   * Search in English → Find Arabic docs ✓
#   * Search in Arabic → Find relevant content ✓

# Quality Gate:
# ✓ All chunks indexed successfully
# ✓ Search returns relevant results
# ✓ Cross-lingual search working
```

**Afternoon (4 hours): RAG Pipeline**
```python
# Hour 5-6: Claude API integration
# - Setup LangChain
# - Create multilingual prompt template
# - Test basic RAG chain

# Hour 7-8: Build RAG system
# - Implement MultilingualShariahRAG class
# - Add language detection
# - Test with sample queries:
#   * "What is Murabaha?" (English)
#   * "ما هو المضاربة؟" (Arabic)
#   * "Adakah Takaful halal?" (Malay)

# Quality Gate:
# ✓ RAG responds to all 3 languages
# ✓ Citations included in responses
# ✓ Arabic text displays correctly
```

**Evening (2 hours): Backend API**
```python
# Hour 9: FastAPI setup
# - Create basic endpoints
# - /api/query (main chatbot)
# - /api/health (health check)

# Hour 10: Frontend integration prep
# - Test API with Postman/curl
# - Document API endpoints
# - Prepare for frontend connection

# Quality Gate:
# ✓ API responds to HTTP requests
# ✓ Returns proper JSON format
# ✓ Handles errors gracefully
```

**Day 2 Deliverables:**
- ✅ Vector database populated
- ✅ RAG system working (trilingual!)
- ✅ FastAPI backend running
- ✅ End-to-end query flow tested

---

### Day 3 (Jan 22): Frontend, Demo & Submission
**Morning (3 hours): User Interface**

**Option A: Simple Web UI (Recommended for beginners)**
```python
# Use Streamlit for rapid prototyping
# Hour 1-2: Build Streamlit app
pip install streamlit

# streamlit_app.py
import streamlit as st

st.title("🌙 BarakahVault - Trilingual Shariah AI")

query = st.text_input("Ask in Arabic, English, or Malay:")
if st.button("Ask"):
    result = call_api(query)
    st.write(result['answer'])
    st.write("Sources:", result['sources'])

# Hour 3: Polish UI
# - Add language selector
# - Display Arabic text properly (RTL)
# - Add example queries
```

**Option B: React Frontend (If you know React)**
```javascript
// Hour 1-3: Build Next.js interface
// - Chat interface
// - Message bubbles
// - Source citations
// - Language toggle
```

**Afternoon (4 hours): Demo Preparation & Pitch Materials**

**Hour 4-5: Record Demo Video (3-5 minutes)**
```yaml
Demo Script:
  Slide 1 (30s): Problem
    - "Islamic finance professionals spend hours researching fatwas"
    - "Most AI tools don't understand Arabic"
    - "No single source of truth"
  
  Slide 2 (30s): Solution
    - "BarakahVault: First trilingual Shariah AI"
    - "Searches BNM, AAOIFI, JAKIM, SC simultaneously"
    - "Answers in Arabic, English, or Malay"
  
  Slide 3-5 (2min): Live Demo
    1. Ask in English: "Is Murabaha allowed?"
       → Show answer with AAOIFI citation
    
    2. Ask in Arabic: "ما هو حكم التورق؟"
       → Show Arabic response + sources
    
    3. Ask in Malay: "Bagaimana Takaful berbeza dengan insurans?"
       → Show Malay response
    
    4. Show citation: Original Arabic + Translation
  
  Slide 6 (30s): Innovation
    - "Cross-lingual semantic search"
    - "Smart OCR for Arabic documents"
    - "Maqasid al-Shariah scoring"
  
  Slide 7 (30s): Business Model
    - "Freemium: RM 49/month"
    - "Target: 1,000 users Year 1"
    - "Revenue: RM 650K"
  
  Slide 8 (30s): Next Steps
    - "Seeking pilot partners"
    - "Beta launch: March 2026"
```

**Hour 6-7: Create Pitch Deck**
```yaml
Slides to Create:
  1. Cover: Team name + tagline
  2. Problem: Current pain points
  3. Solution: BarakahVault overview
  4. Demo: Screenshots of chatbot
  5. Technology: Architecture diagram
  6. Innovation: Trilingual + Maqasid scoring
  7. Business Model: Revenue streams
  8. Market: TAM/SAM/SOM
  9. Traction: Beta users (if any)
  10. Team: Your background
  11. Ask: Looking for pilot partners
```

**Hour 7: Create Architecture Diagram**
```
Use draw.io or Excalidraw:
- User Interface (trilingual)
- FastAPI Backend
- Language Detection
- Vector Database (Pinecone)
- Claude 3.5 Sonnet
- Data Sources (BNM, AAOIFI, etc.)
- OCR Pipeline (for Arabic)
```

**Evening (3 hours): Documentation & Submission**

**Hour 8-9: Technical Documentation**
```markdown
README.md:
  - Project description
  - Setup instructions
  - API documentation
  - Sample queries
  - Technology stack
  - Team members

INNOVATION.md:
  - Trilingual capability explanation
  - Cross-lingual search details
  - Arabic OCR strategy
  - Maqasid scoring methodology
```

**Hour 10: Final Testing & Quality Check**
```yaml
Test Checklist:
  □ Query in English works
  □ Query in Arabic works  
  □ Query in Malay works
  □ Citations display correctly
  □ Arabic text shows properly (RTL)
  □ API doesn't crash
  □ Demo video plays
  □ All files uploaded
```

**Hour 11: Submission**
```yaml
Submission Package:
  □ Working POC (deployed or video)
  □ Business Model Slide (PDF)
  □ Architecture Diagram (PNG/PDF)
  □ Innovation Document (PDF)
  □ Source Code (GitHub/Azure DevOps)
  □ Supporting Documentation (README)
  
Upload to: [Official portal - check WhatsApp group]
Deadline: Jan 22, 2026, 11:59 PM
```

**Day 3 Deliverables:**
- ✅ Functional web interface
- ✅ Demo video (3-5 minutes)
- ✅ Pitch deck (10-15 slides)
- ✅ Architecture diagram
- ✅ Complete documentation
- ✅ POC submitted before deadline

---

### ⚡ Emergency Fallback Plan (If Things Go Wrong)

**If you're behind schedule on Day 3:**

1. **Skip frontend** → Use Postman to demo API directly
2. **Pre-record queries** → Show screenshots instead of live demo
3. **Use fewer documents** → Even 10 documents is enough for POC
4. **Focus on one killer feature** → Trilingual > everything else
5. **Simplify pitch** → 5 slides max, nail the core value prop

**If technical issues:**
- Have backup video of working demo
- Screenshots of successful queries
- Printed API responses showing Arabic citations

**Remember:**
- Judges care more about **INNOVATION** than perfect code
- Your **trilingual capability** is the star - emphasize it!
- Demo **ONE thing really well** > many things poorly

---

### 📊 Time Allocation Summary

```yaml
Total Time: 30 hours over 3 days

Breakdown:
  Data Collection: 6 hours (20%)
  Arabic Processing: 4 hours (13%)
  AI/RAG System: 8 hours (27%)
  Frontend/UI: 3 hours (10%)
  Pitch Materials: 6 hours (20%)
  Documentation: 3 hours (10%)

Priority Levels:
  P0 (Must Have):
    - Working RAG with Arabic support
    - API endpoint that responds
    - Demo video showing trilingual queries
    - Basic pitch deck
  
  P1 (Should Have):
    - Web UI
    - 30+ documents indexed
    - Architecture diagram
    - Good documentation
  
  P2 (Nice to Have):
    - Maqasid scoring
    - Voice input
    - Advanced features
```

---

### ✅ Success Criteria (Minimum Viable POC)

**To win/advance, you MUST have:**

1. **Working Prototype** ✓
   - Accepts queries in 3 languages
   - Returns accurate answers
   - Shows citations

2. **Arabic Handling** ✓
   - Proves you can process Arabic PDFs
   - Displays Arabic text correctly
   - Citations include original Arabic

3. **Real Sources** ✓
   - At least 20 real documents from BNM/AAOIFI
   - Not fake/simulated data
   - Traceable citations

4. **Business Model** ✓
   - Clear revenue strategy
   - Defined target market
   - Realistic pricing

5. **Innovation Story** ✓
   - Why trilingual matters
   - How you solve Arabic challenge
   - What makes you different

**Bonus Points For:**
- Live demo (not just video)
- Mobile-friendly interface
- Maqasid scoring feature
- Partnership commitments

---

### 🎯 Final Reminders

**Focus Areas:**
1. **Arabic capability** - This is your secret weapon! 🔥
2. **Demo quality** - Practice your pitch 10 times
3. **Real sources** - Judges will verify authenticity
4. **Business viability** - Show you understand the market

**Don't Worry About:**
- Perfect code (it's a hackathon!)
- 100% test coverage
- Production-ready deployment
- Every possible feature

**The judges want to see:**
- Innovation that solves real problems
- Technical feasibility
- Business potential
- Team capability

---

**Good luck! You've got this! 🚀**

*Remember: Your trilingual Arabic support is a HUGE differentiator. Most teams won't have this. Make sure the judges see it!*

## 📁 Updated Project Structure (Multilingual Version)

```
barakah-vault-ai/
├── scrapers/
│   ├── __init__.py
│   ├── bnm_scraper.py              # Bank Negara Malaysia
│   ├── aaoifi_scraper.py           # AAOIFI standards (Arabic heavy)
│   ├── sc_scraper.py               # Securities Commission Malaysia
│   ├── jakim_scraper.py            # JAKIM e-Fatwa (Arabic/Malay)
│   ├── iifm_scraper.py             # International Islamic Financial Market
│   └── config.py                   # Scraper configurations
│
├── processors/
│   ├── __init__.py
│   ├── multilingual_pdf_processor.py   # Smart cascade extractor
│   ├── arabic_cleaner.py               # Arabic normalization
│   ├── language_detector.py            # Trilingual detection
│   ├── text_chunker.py                 # Smart chunking
│   └── metadata_extractor.py           # Document metadata
│
├── ocr/
│   ├── __init__.py
│   ├── pymupdf_extractor.py        # Digital PDF (Tier 1)
│   ├── tesseract_extractor.py      # Free OCR (Tier 2)
│   ├── azure_extractor.py          # Premium OCR (Tier 3)
│   └── extractor_factory.py        # Smart cascade logic
│
├── vector_db/
│   ├── __init__.py
│   ├── multilingual_pinecone_setup.py  # Enhanced with language metadata
│   ├── embeddings.py                    # Multilingual embedding configs
│   └── index_manager.py                 # Index operations
│
├── ai/
│   ├── __init__.py
│   ├── multilingual_rag_chain.py   # Trilingual RAG system
│   ├── prompts.py                  # Multilingual prompt templates
│   ├── llm_config.py               # Claude configuration
│   ├── maqasid_scorer.py           # Maqasid al-Shariah scoring
│   └── fatwa_analyzer.py           # Comparative fatwa analysis
│
├── api/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app
│   ├── routes.py                   # API endpoints
│   ├── models.py                   # Pydantic models
│   └── middleware.py               # CORS, rate limiting
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # Main chat interface
│   │   ├── layout.tsx              # RTL/LTR layout support
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx     # Message bubble (RTL support)
│   │   │   ├── LanguageSelector.tsx # AR/EN/MS toggle
│   │   │   ├── CitationCard.tsx    # Display sources with translation
│   │   │   └── ArabicText.tsx      # Arabic text renderer
│   │   └── utils/
│   │       ├── arabicUtils.ts      # Arabic text helpers
│   │       └── languageDetector.ts # Frontend language detection
│   ├── public/
│   │   ├── fonts/                  # Arabic fonts (Noto Sans Arabic)
│   │   └── locales/                # i18n translations
│   ├── package.json
│   ├── next.config.js
│   └── tailwind.config.js          # RTL plugin
│
├── data/
│   ├── raw/
│   │   ├── bnm/                    # BNM PDFs
│   │   ├── aaoifi/                 # AAOIFI standards (Arabic)
│   │   ├── sc/                     # SC Malaysia documents
│   │   ├── jakim/                  # JAKIM fatwas
│   │   └── iifm/                   # IIFM standards
│   ├── processed/
│   │   ├── arabic/                 # Extracted Arabic text
│   │   ├── english/                # Extracted English text
│   │   ├── malay/                  # Extracted Malay text
│   │   └── mixed/                  # Mixed language documents
│   ├── indexed/
│   │   ├── embeddings/             # Vector embeddings
│   │   └── metadata/               # Document metadata JSON
│   └── stats/
│       ├── extraction_stats.json   # OCR method statistics
│       └── language_distribution.json # Language breakdown
│
├── docs/
│   ├── README.md                   # Main documentation
│   ├── ARCHITECTURE.md             # System architecture
│   ├── ARABIC_HANDLING.md          # Arabic processing details
│   ├── API_DOCS.md                 # API documentation
│   ├── DEPLOYMENT.md               # Deployment guide
│   └── PITCH.md                    # Pitch deck content
│
├── tests/
│   ├── test_scrapers.py
│   ├── test_ocr/
│   │   ├── test_pymupdf.py
│   │   ├── test_tesseract.py
│   │   └── test_azure.py
│   ├── test_arabic_processing.py   # Arabic-specific tests
│   ├── test_rag.py
│   ├── test_api.py
│   └── test_multilingual.py        # Trilingual query tests
│
├── scripts/
│   ├── run_crawlers.py             # Run all scrapers
│   ├── process_pdfs.py             # Batch PDF processing
│   ├── index_documents.py          # Bulk indexing
│   ├── test_arabic_extraction.py   # Test Arabic OCR
│   └── generate_stats.py           # Generate statistics
│
├── pitch_materials/
│   ├── slides/
│   │   ├── pitch_deck.pptx         # Main pitch deck
│   │   └── architecture.png        # Architecture diagram
│   ├── demo/
│   │   ├── demo_video.mp4          # Recorded demo
│   │   └── screenshots/            # App screenshots
│   └── documents/
│       ├── business_model.pdf      # Business model slide
│       └── innovation.pdf          # Innovation strategy
│
├── .env.example                    # Environment variables template
├── .gitignore
├── requirements.txt                # Python dependencies
├── README.md                       # Project README
├── docker-compose.yml              # Docker setup (optional)
└── Dockerfile                      # Container config (optional)
```

### Key Files Explained

#### **Multilingual-Specific Files:**

1. **`processors/multilingual_pdf_processor.py`**
   - Smart cascade extraction (Digital → Free OCR → Premium OCR)
   - Handles Arabic, English, Malay PDFs
   - Quality assessment and cost tracking

2. **`processors/arabic_cleaner.py`**
   - Normalize Arabic text (remove diacritics)
   - Extract Quranic verses and Hadith references
   - Clean OCR artifacts

3. **`processors/language_detector.py`**
   - Detect query language
   - Route to appropriate response language
   - Handle mixed-language content

4. **`ai/multilingual_rag_chain.py`**
   - Trilingual RAG system
   - Cross-lingual semantic search
   - Dual-language citations (Arabic + Translation)

5. **`frontend/components/ArabicText.tsx`**
   - Proper RTL rendering
   - Arabic font loading
   - Bidirectional text handling

---

## 🔧 Environment Setup (Enhanced for Arabic)

### Required API Keys

```bash
# .env file

# Core AI Services
ANTHROPIC_API_KEY=sk-ant-...              # Claude 3.5 Sonnet
OPENAI_API_KEY=sk-...                     # For embeddings

# Vector Database
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1

# OCR Services (Optional but recommended for Arabic)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=...

# Optional Services
REDIS_URL=redis://localhost:6379          # Caching
DATABASE_URL=postgresql://...             # User data (optional)
GOOGLE_CLOUD_KEY_PATH=./google-creds.json # Google Vision API (alternative OCR)

# App Configuration
ENVIRONMENT=development
API_PORT=8000
FRONTEND_URL=http://localhost:3000
```

### Installation Commands

#### **Step 1: System Dependencies (Ubuntu/Debian)**

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11+
sudo apt-get install python3.11 python3.11-venv python3-pip -y

# Install Tesseract OCR with Arabic support
sudo apt-get install tesseract-ocr -y
sudo apt-get install tesseract-ocr-ara -y  # Arabic language pack
sudo apt-get install tesseract-ocr-eng -y  # English language pack

# Verify Tesseract installation
tesseract --version
tesseract --list-langs
# Should show: ara, eng

# Install poppler-utils (for pdf2image)
sudo apt-get install poppler-utils -y

# Install system libraries for PDF processing
sudo apt-get install libpoppler-cpp-dev -y
```

#### **Step 2: Create Project & Virtual Environment**

```bash
# Create project directory
mkdir barakah-vault-ai
cd barakah-vault-ai

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

#### **Step 3: Install Python Dependencies**

```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.0
python-dotenv==1.0.0

# AI/ML Libraries
anthropic==0.18.1
langchain==0.1.9
langchain-anthropic==0.1.5
langchain-openai==0.0.5
langchain-pinecone==0.0.3
openai==1.12.0

# Vector Database
pinecone-client==3.0.0

# PDF Processing & OCR
PyPDF2==3.0.1
pdfplumber==0.10.3
pymupdf==1.23.21                # Best for Arabic digital PDFs
pdf2image==1.17.0
Pillow==10.2.0

# OCR Engines
pytesseract==0.3.10             # Free OCR with Arabic support
azure-ai-formrecognizer==3.3.2  # Premium OCR (optional)

# Text Processing
beautifulsoup4==4.12.3
lxml==5.1.0
html5lib==1.1

# Web Scraping
scrapy==2.11.0
requests==2.31.0
aiohttp==3.9.3

# Language Detection
langdetect==1.0.9

# Utilities
tqdm==4.66.1                    # Progress bars
python-multipart==0.0.9
redis==5.0.1                    # Caching (optional)

# Testing
pytest==8.0.0
pytest-asyncio==0.23.4
httpx==0.26.0                   # For testing FastAPI

# Development
black==24.1.1                   # Code formatting
flake8==7.0.0                   # Linting
ipython==8.21.0                 # Better REPL
EOF

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import anthropic; print('✓ Anthropic installed')"
python -c "import pytesseract; print('✓ Tesseract installed')"
python -c "import fitz; print('✓ PyMuPDF installed')"
python -c "import pinecone; print('✓ Pinecone installed')"
```

#### **Step 4: Frontend Dependencies (Next.js)**

```bash
# Create frontend directory
mkdir frontend
cd frontend

# Initialize Next.js project with TypeScript
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir

# Install additional dependencies for Arabic/RTL support
npm install --save \
  @headlessui/react \
  @heroicons/react \
  clsx \
  tailwind-merge \
  i18next \
  react-i18next \
  next-i18next \
  tailwindcss-rtl

# Install Arabic fonts
npm install --save @fontsource/noto-sans-arabic

# For development
npm install --save-dev \
  @types/react \
  @types/node \
  typescript
```

#### **Step 5: Configure RTL Support (Tailwind)**

```javascript
// frontend/tailwind.config.js

const plugin = require('tailwindcss/plugin')

module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        arabic: ['Noto Sans Arabic', 'sans-serif'],
      },
    },
  },
  plugins: [
    // RTL plugin for Arabic support
    plugin(function({ addUtilities }) {
      addUtilities({
        '.rtl': {
          direction: 'rtl',
        },
        '.ltr': {
          direction: 'ltr',
        },
      })
    }),
  ],
}
```

#### **Step 6: Test Arabic Support**

```bash
# Go back to project root
cd ..

# Test Arabic PDF extraction
cat > test_arabic.py << 'EOF'
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

def test_arabic_support():
    print("Testing Arabic support...\n")
    
    # Test 1: Tesseract languages
    print("1. Available Tesseract languages:")
    import subprocess
    result = subprocess.run(['tesseract', '--list-langs'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    # Test 2: Arabic text rendering
    print("\n2. Testing Arabic text rendering:")
    arabic_text = "بسم الله الرحمن الرحيم"
    print(f"Arabic text: {arabic_text}")
    print(f"Length: {len(arabic_text)} characters")
    
    # Test 3: PyMuPDF version
    print(f"\n3. PyMuPDF version: {fitz.version}")
    
    print("\n✅ All Arabic support tests passed!")

if __name__ == "__main__":
    test_arabic_support()
EOF

python test_arabic.py
```

#### **Step 7: Setup Environment Variables**

```bash
# Create .env file
cat > .env << 'EOF'
# API Keys (REPLACE WITH YOUR ACTUAL KEYS)
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=us-east-1

# Azure (Optional - for premium OCR)
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=
AZURE_DOCUMENT_INTELLIGENCE_KEY=

# App Config
ENVIRONMENT=development
API_PORT=8000
LOG_LEVEL=INFO

# Feature Flags
ENABLE_AZURE_OCR=false
ENABLE_CACHING=false
EOF

# Make sure .env is in .gitignore
echo ".env" >> .gitignore
```

### Verification Checklist

Run these commands to verify everything is set up correctly:

```bash
# 1. Check Python version
python --version
# Expected: Python 3.11+ or Python 3.10+

# 2. Check Tesseract
tesseract --version
tesseract --list-langs | grep ara
# Expected: ara should be listed

# 3. Test imports
python << 'EOF'
import anthropic
import langchain
import pinecone
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
print("✅ All imports successful!")
EOF

# 4. Test Tesseract with sample Arabic
echo "مرحبا" | tesseract stdin stdout -l ara
# Should output something (even if not perfect)

# 5. Check API keys (without exposing them)
python << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

keys = {
    'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
}

for key, value in keys.items():
    status = "✅ Set" if value and len(value) > 10 else "❌ Not set"
    print(f"{key}: {status}")
EOF
```

### Quick Start Commands

```bash
# Backend (Terminal 1)
cd barakah-vault-ai
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd barakah-vault-ai/frontend
npm run dev

# Test API
curl http://localhost:8000/api/health

# Access frontend
# Open browser: http://localhost:3000
```

---

## 💡 Innovation Highlights for Pitch

### Technical Innovation
1. **Multi-Source RAG System** - Aggregates 5+ authoritative Shariah sources
2. **Citation Transparency** - Every answer traceable to original source
3. **Confidence Scoring** - Indicates reliability of responses
4. **Arabic NLP Support** - Handles trilingual queries (EN/MS/AR)

### Business Innovation
1. **Maqasid-Based Scoring** - First AI to use Maqasid al-Shariah framework
2. **Real-Time Updates** - Auto-sync with new fatwas and regulations
3. **API-First Design** - Easy integration with existing systems
4. **White-Label Solution** - Customizable for different institutions

### User Experience Innovation
1. **Conversational Interface** - Natural language queries
2. **Document Analysis** - Upload contracts for instant review
3. **Comparative Views** - See different scholarly opinions
4. **Learning Mode** - Explains reasoning, not just answers

---

## 📈 Success Metrics

### Technical Metrics
- ✅ Response accuracy: >90%
- ✅ Citation coverage: >95% of answers
- ✅ Response time: <3 seconds
- ✅ Source diversity: Average 3+ sources per query

### Business Metrics
- Target 1000+ queries/month (post-launch)
- 20+ institutional partnerships (Year 1)
- 80%+ user satisfaction
- 60%+ accuracy vs human Shariah scholar

---

## 🎯 Competitive Advantages

1. **Authentic Source Coverage**: Only solution indexing BNM, AAOIFI, SC, and state fatwas
2. **Real-Time Updates**: Weekly auto-crawling of new rulings
3. **Transparency**: Full citation trail for audit purposes
4. **Malaysian Context**: Optimized for Malaysian Islamic finance regulations
5. **API Access**: Easy integration for fintech companies

---

## 📞 Next Steps

### Immediate Actions (Today)
1. ✅ Setup all API accounts (Anthropic, OpenAI, Pinecone)
2. ✅ Clone/setup project structure
3. ✅ Start web crawling scripts
4. ✅ Begin PDF collection

### Tomorrow
1. ✅ Complete data processing
2. ✅ Build and test RAG system
3. ✅ Deploy backend API

### Final Day
1. ✅ Polish frontend
2. ✅ Create pitch materials
3. ✅ Record demo
4. ✅ Submit POC

---

## 📚 Additional Resources

### Shariah Finance Resources
- [AAOIFI Standards](https://aaoifi.com/)
- [BNM Shariah](https://www.bnm.gov.my/shariah)
- [SC Malaysia Islamic Capital Market](https://www.sc.com.my/resources/shariah)
- [JAKIM e-Fatwa](http://www.e-fatwa.gov.my/)

### Technical Resources
- [LangChain Documentation](https://python.langchain.com/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Pinecone Vector DB](https://docs.pinecone.io/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

### Example Projects
- [ChatPDF](https://github.com/akshata29/chatpdf)
- [PrivateGPT](https://github.com/imartinez/privateGPT)
- [Quivr](https://github.com/StanGirard/quivr)

---

## ✅ Final Checklist

### Submission Requirements
- [ ] Working POC (prototype deployed)
- [ ] Business Model Slide
- [ ] AI Architecture Diagram
- [ ] Innovation Strategy Document
- [ ] Source Code (GitHub/Azure DevOps)
- [ ] Demo Video (3-5 minutes)
- [ ] Documentation (README, API docs)

### Quality Checks
- [ ] Test 20+ different query types
- [ ] Verify all citations are accurate
- [ ] Check response quality
- [ ] Test error handling
- [ ] Validate source diversity
- [ ] Performance benchmarking

---

**Good luck with the AI Fiqh Hackathon! 🚀**

*This plan provides everything you need to build a competitive POC in 3 days. Focus on core functionality first, then add advanced features if time permits.*
