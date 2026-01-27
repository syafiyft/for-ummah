"""
PDF preview endpoints.
Generates PNG previews of PDF pages with optional text highlighting.
Supports both local files and Supabase Storage.
"""

import fitz  # PyMuPDF
from fastapi import APIRouter, HTTPException, Response
from pathlib import Path
from src.core import settings
from src.db.client import is_supabase_configured
import logging
import io

logger = logging.getLogger(__name__)

router = APIRouter(tags=["PDF Preview"])

# Lazy-loaded storage service
_storage_service = None


def get_storage_service():
    """Get storage service if Supabase is configured."""
    global _storage_service
    if _storage_service is None and is_supabase_configured():
        from src.db.storage import StorageService
        _storage_service = StorageService()
    return _storage_service


def _load_pdf_from_storage(source: str, filename: str) -> bytes | None:
    """
    Try to load PDF from Supabase Storage.

    Args:
        source: Source directory (e.g. 'bnm', 'manual')
        filename: PDF filename

    Returns:
        PDF bytes if found, None otherwise
    """
    storage = get_storage_service()
    if not storage:
        return None

    try:
        storage_path = f"{source.lower()}/{filename}"
        return storage.download_pdf(storage_path, use_cache=True)
    except Exception as e:
        logger.debug(f"Storage download failed: {e}")
        return None


def _load_pdf_from_local(source: str, filename: str) -> Path | None:
    """
    Try to load PDF from local filesystem with fuzzy matching.

    Args:
        source: Source directory
        filename: PDF filename

    Returns:
        Path to PDF if found, None otherwise
    """
    pdf_path = settings.data_dir / source / filename
    if pdf_path.exists():
        return pdf_path

    # Try fuzzy match if exact match fails
    source_dir = settings.data_dir / source
    if source_dir.exists():
        req_clean = filename.lower().replace(".pdf", "").replace(" ", "").replace("_", "").replace("-", "")

        for f in source_dir.glob("*.pdf"):
            disk_clean = f.name.lower().replace(".pdf", "").replace(" ", "").replace("_", "").replace("-", "")
            if disk_clean == req_clean:
                return f

    return None


@router.get("/pdf/preview/{source}/{filename}/{page_num}")
async def get_pdf_preview(source: str, filename: str, page_num: int, highlight: str | None = None):
    """
    Generate a PNG preview of a specific PDF page.
    Optionally crops to the highlighted text.

    Args:
        source: Source directory (e.g. 'bnm', 'manual')
        filename: PDF filename
        page_num: Page number (1-based)
        highlight: Text to highlight and crop to

    Returns:
        PNG image bytes
    """
    try:
        # Security: Prevent path traversal
        if ".." in source or ".." in filename:
            raise HTTPException(status_code=400, detail="Invalid path")

        # Try loading from Supabase Storage first
        pdf_content = _load_pdf_from_storage(source, filename)

        if pdf_content:
            # Open from bytes
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            logger.debug(f"Loaded PDF from storage: {source}/{filename}")
        else:
            # Fall back to local file
            pdf_path = _load_pdf_from_local(source, filename)
            if not pdf_path:
                logger.error(f"PDF not found: {source}/{filename}")
                raise HTTPException(status_code=404, detail="PDF not found")

            doc = fitz.open(pdf_path)
            logger.debug(f"Loaded PDF from local: {pdf_path}")

        # Validate page number
        if page_num < 1 or page_num > len(doc):
            raise HTTPException(status_code=400, detail=f"Invalid page number. Document has {len(doc)} pages.")

        page = doc.load_page(page_num - 1)

        # Highlight and Crop Logic
        if highlight:
            search_text = highlight.strip()
            quads = page.search_for(search_text)

            if quads:
                # Add highlighting annotation
                for quad in quads:
                    page.add_highlight_annot(quad)

                # Calculate bounding box of all hits
                union_rect = fitz.Rect(quads[0])
                for q in quads[1:]:
                    union_rect.include_rect(q)

                # Add padding (e.g. 50 pixels)
                union_rect += (-50, -50, 50, 50)

                # Ensure rect is within page bounds
                page_rect = page.rect
                crop_rect = union_rect & page_rect

                # Set crop box
                page.set_cropbox(crop_rect)
            else:
                logger.warning(f"Highlight text not found on page {page_num}: {highlight[:20]}...")

        # Render
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        doc.close()

        return Response(content=img_data, media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
