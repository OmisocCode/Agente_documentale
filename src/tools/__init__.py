"""
Tools for agent operations.

Includes PDF extraction, LaTeX processing, and template rendering tools.
"""

from src.tools.pdf_tools import (
    PDFExtractor,
    extract_text_from_pdf,
    detect_pdf_toc,
    analyze_pdf_structure,
)
from src.tools.latex_tools import (
    LaTeXProcessor,
    extract_formulas_from_text,
    split_text_into_blocks,
)
from src.tools.template_tools import (
    TemplateRenderer,
    render_chapter_html,
    inject_mathjax_into_html,
)

__all__ = [
    # PDF Tools
    "PDFExtractor",
    "extract_text_from_pdf",
    "detect_pdf_toc",
    "analyze_pdf_structure",
    # LaTeX Tools
    "LaTeXProcessor",
    "extract_formulas_from_text",
    "split_text_into_blocks",
    # Template Tools
    "TemplateRenderer",
    "render_chapter_html",
    "inject_mathjax_into_html",
]
