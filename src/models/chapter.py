"""
Chapter data model for PDF content.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Chapter(BaseModel):
    """
    Represents a chapter or section in a PDF document.

    Attributes:
        id: Unique chapter identifier (e.g., "ch1", "ch2")
        title: Chapter title
        pages: List of page numbers in this chapter (1-indexed)
        content_raw: Raw extracted text content
        parent_id: ID of parent chapter (for nested sections)
        level: Nesting level (0=main chapter, 1=section, 2=subsection, etc.)
        metadata: Additional metadata (page count, word count, etc.)
    """

    id: str = Field(..., description="Unique chapter identifier")
    title: str = Field(..., description="Chapter title", min_length=1)
    pages: List[int] = Field(..., description="Page numbers in chapter", min_length=1)
    content_raw: str = Field(..., description="Raw extracted text")
    parent_id: Optional[str] = Field(None, description="Parent chapter ID for nested sections")
    level: int = Field(0, ge=0, le=5, description="Nesting level")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @field_validator("pages")
    @classmethod
    def validate_pages(cls, v: List[int]) -> List[int]:
        """Validate that pages are positive and sorted."""
        if not all(p > 0 for p in v):
            raise ValueError("Page numbers must be positive")
        # Sort pages to ensure consistency
        return sorted(set(v))  # Remove duplicates and sort

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate chapter ID format."""
        if not v or not v.strip():
            raise ValueError("Chapter ID cannot be empty")
        # Remove whitespace
        return v.strip()

    def get_page_count(self) -> int:
        """Get number of pages in this chapter."""
        return len(self.pages)

    def get_word_count(self) -> int:
        """Get approximate word count in chapter."""
        return len(self.content_raw.split())

    def get_char_count(self) -> int:
        """Get character count in chapter."""
        return len(self.content_raw)

    def get_page_range(self) -> str:
        """
        Get page range as string (e.g., "1-5", "7", "10-12").

        Returns:
            Formatted page range string
        """
        if not self.pages:
            return ""

        pages = sorted(self.pages)
        if len(pages) == 1:
            return str(pages[0])

        # Find consecutive ranges
        ranges = []
        start = pages[0]
        end = pages[0]

        for i in range(1, len(pages)):
            if pages[i] == end + 1:
                end = pages[i]
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = pages[i]
                end = pages[i]

        # Add last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ", ".join(ranges)

    def is_nested(self) -> bool:
        """Check if this is a nested section."""
        return self.parent_id is not None

    def update_metadata(self) -> None:
        """Update metadata with computed values."""
        self.metadata.update(
            {
                "page_count": self.get_page_count(),
                "word_count": self.get_word_count(),
                "char_count": self.get_char_count(),
                "page_range": self.get_page_range(),
            }
        )

    model_config = {"json_schema_extra": {"examples": [
        {
            "id": "ch1",
            "title": "Capitolo 1: Introduzione alla Geometria Proiettiva",
            "pages": [1, 2, 3, 4],
            "content_raw": "Questo capitolo introduce i concetti base...",
            "parent_id": None,
            "level": 0,
            "metadata": {
                "page_count": 4,
                "word_count": 1250,
                "page_range": "1-4",
            },
        }
    ]}}


class ChapterCollection(BaseModel):
    """
    Collection of chapters extracted from a PDF.

    Attributes:
        chapters: List of Chapter objects
        total_pages: Total number of pages in document
        pdf_path: Path to source PDF
    """

    chapters: List[Chapter] = Field(default_factory=list, description="List of chapters")
    total_pages: int = Field(..., ge=1, description="Total pages in document")
    pdf_path: str = Field(..., description="Path to source PDF")

    @field_validator("chapters")
    @classmethod
    def validate_no_overlap(cls, v: List[Chapter]) -> List[Chapter]:
        """
        Validate that chapter page ranges don't overlap.

        Raises:
            ValueError: If chapters have overlapping pages
        """
        if not v:
            return v

        # Collect all pages and check for duplicates
        all_pages = []
        for chapter in v:
            all_pages.extend(chapter.pages)

        if len(all_pages) != len(set(all_pages)):
            # Find duplicates
            seen = set()
            duplicates = set()
            for page in all_pages:
                if page in seen:
                    duplicates.add(page)
                seen.add(page)

            raise ValueError(f"Chapters have overlapping pages: {sorted(duplicates)}")

        return v

    def get_chapter_by_id(self, chapter_id: str) -> Optional[Chapter]:
        """
        Get chapter by ID.

        Args:
            chapter_id: Chapter identifier

        Returns:
            Chapter object or None if not found
        """
        for chapter in self.chapters:
            if chapter.id == chapter_id:
                return chapter
        return None

    def get_chapter_by_page(self, page_num: int) -> Optional[Chapter]:
        """
        Get chapter containing a specific page.

        Args:
            page_num: Page number (1-indexed)

        Returns:
            Chapter object or None if not found
        """
        for chapter in self.chapters:
            if page_num in chapter.pages:
                return chapter
        return None

    def get_total_chapters(self) -> int:
        """Get total number of chapters."""
        return len(self.chapters)

    def get_coverage_percentage(self) -> float:
        """
        Get percentage of document covered by chapters.

        Returns:
            Percentage of pages covered (0-100)
        """
        if self.total_pages == 0:
            return 0.0

        covered_pages = set()
        for chapter in self.chapters:
            covered_pages.update(chapter.pages)

        return (len(covered_pages) / self.total_pages) * 100

    def sort_chapters_by_page(self) -> None:
        """Sort chapters by starting page number."""
        self.chapters.sort(key=lambda ch: min(ch.pages) if ch.pages else 0)
