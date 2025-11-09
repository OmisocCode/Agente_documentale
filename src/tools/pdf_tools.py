"""
PDF extraction tools for Chapter Agent (Task 1).

Provides tools for extracting text, detecting table of contents,
identifying headings, and analyzing document structure.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """
    PDF text extraction and analysis tools.

    Uses PyMuPDF (fitz) for fast and accurate text extraction from
    LaTeX-compiled PDFs.
    """

    def __init__(self, pdf_path: str):
        """
        Initialize PDF extractor.

        Args:
            pdf_path: Path to PDF file

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF cannot be opened
        """
        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            self.doc = fitz.open(str(self.pdf_path))
            self.total_pages = len(self.doc)
            logger.info(f"Opened PDF: {pdf_path} ({self.total_pages} pages)")
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            raise

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close PDF."""
        self.close()

    def close(self) -> None:
        """Close PDF document."""
        if hasattr(self, 'doc') and self.doc:
            self.doc.close()
            logger.debug(f"Closed PDF: {self.pdf_path}")

    def extract_text(
        self, page_range: Optional[Tuple[int, int]] = None
    ) -> str:
        """
        Extract text from page range.

        Args:
            page_range: Tuple of (start_page, end_page) (1-indexed, inclusive).
                       If None, extracts all pages.

        Returns:
            Extracted text

        Example:
            >>> extractor = PDFExtractor("document.pdf")
            >>> text = extractor.extract_text((1, 5))  # Pages 1-5
        """
        if page_range is None:
            start_page, end_page = 1, self.total_pages
        else:
            start_page, end_page = page_range

        # Convert to 0-indexed
        start_idx = max(0, start_page - 1)
        end_idx = min(self.total_pages, end_page)

        text_parts = []

        for page_num in range(start_idx, end_idx):
            try:
                page = self.doc[page_num]
                text = page.get_text()
                text_parts.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")

        full_text = "\n\n".join(text_parts)

        logger.debug(
            f"Extracted {len(full_text)} characters from pages {start_page}-{end_page}"
        )

        return full_text

    def extract_page(self, page_num: int) -> str:
        """
        Extract text from a single page.

        Args:
            page_num: Page number (1-indexed)

        Returns:
            Page text
        """
        return self.extract_text((page_num, page_num))

    def detect_toc(self) -> Optional[List[Dict[str, any]]]:
        """
        Detect table of contents if present in PDF metadata.

        Returns:
            List of TOC entries or None if not found

        Example:
            >>> toc = extractor.detect_toc()
            >>> for entry in toc:
            ...     print(f"Level {entry['level']}: {entry['title']} (page {entry['page']})")
        """
        try:
            toc = self.doc.get_toc()

            if not toc:
                logger.info("No TOC found in PDF metadata")
                return None

            # Convert to more usable format
            toc_entries = []
            for entry in toc:
                level, title, page = entry
                toc_entries.append({
                    "level": level,
                    "title": title.strip(),
                    "page": page,  # 1-indexed
                })

            logger.info(f"Found TOC with {len(toc_entries)} entries")
            return toc_entries

        except Exception as e:
            logger.warning(f"Error detecting TOC: {e}")
            return None

    def detect_headings(
        self,
        page_range: Optional[Tuple[int, int]] = None,
        patterns: Optional[List[str]] = None,
    ) -> List[Dict[str, any]]:
        """
        Detect headings using pattern matching.

        Args:
            page_range: Optional page range to search
            patterns: Custom regex patterns for headings. If None, uses defaults.

        Returns:
            List of detected headings with page numbers

        Example:
            >>> headings = extractor.detect_headings()
            >>> for h in headings:
            ...     print(f"Page {h['page']}: {h['title']}")
        """
        if patterns is None:
            # Default patterns for common heading formats
            patterns = [
                r"^Chapter\s+\d+[:\.]?\s+(.+)$",           # Chapter 1: Title
                r"^Capitolo\s+\d+[:\.]?\s+(.+)$",         # Capitolo 1: Titolo
                r"^\d+\.\s+([A-Z][^\n]{3,})$",            # 1. Title
                r"^\d+\.\d+\s+([A-Z][^\n]{3,})$",         # 1.1 Title
                r"^[A-Z][A-Z\s]{10,}$",                   # ALL CAPS HEADING
                r"^§\s*\d+[:\.]?\s+(.+)$",                # § 1: Title
            ]

        text = self.extract_text(page_range)
        lines = text.split("\n")

        headings = []
        current_page = page_range[0] if page_range else 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try each pattern
            for pattern in patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    # Extract title (group 1 if exists, else full match)
                    title = match.group(1) if match.groups() else line

                    headings.append({
                        "title": title.strip(),
                        "page": current_page,
                        "raw_text": line,
                        "pattern": pattern,
                    })
                    break

        logger.info(f"Detected {len(headings)} potential headings")
        return headings

    def analyze_structure(
        self, sample_pages: int = 5
    ) -> Dict[str, any]:
        """
        Analyze document structure to identify sections.

        Analyzes font sizes, styles, and layout to detect structure.

        Args:
            sample_pages: Number of pages to sample for analysis

        Returns:
            Dictionary with structure analysis

        Example:
            >>> structure = extractor.analyze_structure()
            >>> print(f"Average font size: {structure['avg_font_size']}")
        """
        # Sample pages evenly throughout document
        step = max(1, self.total_pages // sample_pages)
        sample_page_nums = range(0, self.total_pages, step)[:sample_pages]

        font_sizes = []
        font_names = []
        blocks_per_page = []

        for page_num in sample_page_nums:
            try:
                page = self.doc[page_num]
                blocks = page.get_text("dict")["blocks"]

                blocks_per_page.append(len(blocks))

                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                font_sizes.append(span["size"])
                                font_names.append(span["font"])

            except Exception as e:
                logger.warning(f"Error analyzing page {page_num + 1}: {e}")

        # Calculate statistics
        if font_sizes:
            avg_font_size = sum(font_sizes) / len(font_sizes)
            max_font_size = max(font_sizes)
            min_font_size = min(font_sizes)
        else:
            avg_font_size = max_font_size = min_font_size = 0

        # Most common fonts
        from collections import Counter
        font_counts = Counter(font_names)
        most_common_fonts = font_counts.most_common(5)

        structure = {
            "total_pages": self.total_pages,
            "sampled_pages": len(sample_page_nums),
            "avg_font_size": round(avg_font_size, 2),
            "max_font_size": round(max_font_size, 2),
            "min_font_size": round(min_font_size, 2),
            "font_size_range": round(max_font_size - min_font_size, 2),
            "avg_blocks_per_page": round(sum(blocks_per_page) / len(blocks_per_page), 2)
            if blocks_per_page
            else 0,
            "most_common_fonts": [
                {"font": font, "count": count} for font, count in most_common_fonts
            ],
        }

        logger.info(f"Document structure analysis: {structure}")
        return structure

    def get_page_count(self) -> int:
        """Get total number of pages."""
        return self.total_pages

    def extract_images(self, page_num: int) -> List[bytes]:
        """
        Extract images from a page.

        Args:
            page_num: Page number (1-indexed)

        Returns:
            List of image bytes
        """
        images = []

        try:
            page = self.doc[page_num - 1]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = self.doc.extract_image(xref)
                image_bytes = base_image["image"]
                images.append(image_bytes)

            logger.debug(f"Extracted {len(images)} images from page {page_num}")

        except Exception as e:
            logger.warning(f"Error extracting images from page {page_num}: {e}")

        return images

    def search_text(self, query: str, case_sensitive: bool = False) -> List[Dict[str, any]]:
        """
        Search for text across the document.

        Args:
            query: Text to search for
            case_sensitive: Whether search should be case-sensitive

        Returns:
            List of matches with page numbers

        Example:
            >>> matches = extractor.search_text("Teorema")
            >>> for match in matches:
            ...     print(f"Found on page {match['page']}")
        """
        matches = []

        for page_num in range(self.total_pages):
            try:
                page = self.doc[page_num]

                # PyMuPDF search
                if case_sensitive:
                    search_results = page.search_for(query)
                else:
                    search_results = page.search_for(query, flags=~fitz.TEXT_PRESERVE_WHITESPACE)

                for rect in search_results:
                    matches.append({
                        "page": page_num + 1,  # 1-indexed
                        "query": query,
                        "rect": rect,
                    })

            except Exception as e:
                logger.warning(f"Error searching page {page_num + 1}: {e}")

        logger.info(f"Found {len(matches)} matches for '{query}'")
        return matches


# Convenience functions
def extract_text_from_pdf(
    pdf_path: str, page_range: Optional[Tuple[int, int]] = None
) -> str:
    """
    Extract text from PDF (convenience function).

    Args:
        pdf_path: Path to PDF
        page_range: Optional (start, end) page range

    Returns:
        Extracted text
    """
    with PDFExtractor(pdf_path) as extractor:
        return extractor.extract_text(page_range)


def detect_pdf_toc(pdf_path: str) -> Optional[List[Dict[str, any]]]:
    """
    Detect table of contents (convenience function).

    Args:
        pdf_path: Path to PDF

    Returns:
        TOC entries or None
    """
    with PDFExtractor(pdf_path) as extractor:
        return extractor.detect_toc()


def analyze_pdf_structure(pdf_path: str) -> Dict[str, any]:
    """
    Analyze PDF structure (convenience function).

    Args:
        pdf_path: Path to PDF

    Returns:
        Structure analysis
    """
    with PDFExtractor(pdf_path) as extractor:
        return extractor.analyze_structure()
