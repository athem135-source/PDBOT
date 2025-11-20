"""
PDF Page Renderer for Source Citations
Uses PyMuPDF (fitz) to render PDF pages as images for the "View Source" feature.
"""
import os
from typing import Optional, TYPE_CHECKING
from PIL import Image
import io

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    fitz = None  # type: ignore

if TYPE_CHECKING:
    import fitz


def get_page_image(
    pdf_path: str,
    page_number: int,
    zoom: float = 2.0,
    dpi: int = 150
) -> Optional[Image.Image]:
    """Render a specific PDF page as a PIL Image.
    
    Args:
        pdf_path: Absolute path to the PDF file
        page_number: Page number (1-indexed)
        zoom: Zoom factor for rendering quality (default 2.0)
        dpi: DPI for rendering (default 150)
        
    Returns:
        PIL Image object or None if rendering fails
        
    Usage:
        img = get_page_image("path/to/manual.pdf", 45, zoom=2.5)
        if img:
            st.image(img, caption="Page 45", use_column_width=True)
    """
    if not FITZ_AVAILABLE or fitz is None:
        return None
        
    if not os.path.isfile(pdf_path):
        return None
        
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        
        # Convert to 0-indexed
        page_idx = page_number - 1
        
        # Validate page number
        if page_idx < 0 or page_idx >= len(doc):
            doc.close()
            return None
            
        # Get page
        page = doc.load_page(page_idx)
        
        # Create transformation matrix for zoom
        if fitz is None:
            doc.close()
            return None
        mat = fitz.Matrix(zoom, zoom)
        
        # Render page to pixmap
        pix = page.get_pixmap(matrix=mat, dpi=dpi)
        
        # Convert pixmap to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Cleanup
        doc.close()
        
        return img
        
    except Exception as e:
        print(f"[PDF Renderer] Error rendering page {page_number}: {e}")
        return None


def is_pdf_renderer_available() -> bool:
    """Check if PyMuPDF is available for rendering."""
    return FITZ_AVAILABLE


def get_pdf_page_count(pdf_path: str) -> int:
    """Get total page count of a PDF.
    
    Args:
        pdf_path: Absolute path to the PDF file
        
    Returns:
        Total page count or 0 if file cannot be opened
    """
    if not FITZ_AVAILABLE or fitz is None or not os.path.isfile(pdf_path):
        return 0
        
    try:
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except Exception:
        return 0
