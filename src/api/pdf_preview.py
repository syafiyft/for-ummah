import fitz  # PyMuPDF
from fastapi import APIRouter, HTTPException, Response
from pathlib import Path
from src.core import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["PDF Preview"])

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
            
        # Construct path
        pdf_path = settings.data_dir / source / filename
        if not pdf_path.exists():
             # Try fuzzy match if exact match fails
            source_dir = settings.data_dir / source
            if source_dir.exists():
                potential_match = None
                # Normalize requested filename: remove extension, lower, remove separators
                req_clean = filename.lower().replace(".pdf", "").replace(" ", "").replace("_", "").replace("-", "")
                
                for f in source_dir.glob("*.pdf"):
                    # Normalize disk filename
                    disk_clean = f.name.lower().replace(".pdf", "").replace(" ", "").replace("_", "").replace("-", "")
                    
                    if disk_clean == req_clean:
                        potential_match = f
                        break
                        
                if potential_match:
                    pdf_path = potential_match
                else:
                    logger.error(f"PDF not found. Source: {source}, Request: {filename} (Clean: {req_clean})")
                    raise HTTPException(status_code=404, detail="PDF not found")
            else:
                 raise HTTPException(status_code=404, detail="Source directory not found")

        # Open PDF
        doc = fitz.open(pdf_path)
        
        # Validate page number
        if page_num < 1 or page_num > len(doc):
            raise HTTPException(status_code=400, detail=f"Invalid page number. Document has {len(doc)} pages.")
            
        page = doc.load_page(page_num - 1)
        
        # Highlight and Crop Logic
        if highlight:
            # Clean search term
            search_text = highlight.strip()
            # Search for text instances (quads)
            quads = page.search_for(search_text)
            
            if quads:
                # Add highlighting annotation
                for quad in quads:
                    page.add_highlight_annot(quad)
                
                # Calculate bounding box of all hits
                # Union of all rects
                union_rect = fitz.Rect(quads[0])
                for q in quads[1:]:
                    union_rect.include_rect(q)
                
                # Add padding (e.g. 50 pixels)
                union_rect += (-50, -50, 50, 50)
                
                # Ensure rect is within page bounds
                page_rect = page.rect
                
                # Intersect with page bounds
                crop_rect = union_rect & page_rect
                
                # Set crop box
                page.set_cropbox(crop_rect)
            else:
                logger.warning(f"Highlight text not found on page {page_num}: {highlight[:20]}...")
                # If highlight fails, maybe just show top of page or full page?
                # User specifically wanted "only on that text", so fall back to full page is better 
                # than nothing, but maybe we can just zoom to top?
                pass
        
        # Render
        pix = page.get_pixmap(dpi=150)
        img_data = pix.tobytes("png")
        doc.close()
        
        return Response(content=img_data, media_type="image/png")
        
    except Exception as e:
        logger.error(f"Preview generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
