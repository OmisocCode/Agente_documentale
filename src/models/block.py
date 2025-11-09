"""
Classified content block models.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from src.models.enums import BlockAction, BlockType


class ClassifiedBlock(BaseModel):
    """
    Represents a classified block of content within a chapter.

    Attributes:
        type: Type of block (narrative, theorem, formula, etc.)
        content: Text content of the block
        action: Action to take (summarize, verbatim, latex)
        name: Optional name (e.g., "Teorema di Bézout")
        latex: LaTeX formula (if type is FORMULA)
        confidence: Confidence score of classification (0-1)
        needs_review: Flag indicating manual review needed
        metadata: Additional metadata
    """

    type: BlockType = Field(..., description="Type of content block")
    content: str = Field(..., description="Text content", min_length=1)
    action: BlockAction = Field(..., description="Action to take on this block")
    name: Optional[str] = Field(None, description="Name of theorem/definition/etc.")
    latex: Optional[str] = Field(None, description="LaTeX formula if applicable")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Classification confidence")
    needs_review: bool = Field(False, description="Requires manual review")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @field_validator("latex")
    @classmethod
    def validate_latex_for_formula(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure LaTeX is provided for FORMULA blocks."""
        block_type = info.data.get("type")
        if block_type == BlockType.FORMULA and not v:
            # Set needs_review if formula has no LaTeX
            return None
        return v

    @field_validator("confidence")
    @classmethod
    def flag_low_confidence(cls, v: float, info) -> float:
        """Auto-flag blocks with low confidence for review."""
        if v < 0.6:  # Configurable threshold
            # This will be caught after validation
            pass
        return v

    def model_post_init(self, __context) -> None:
        """Post-initialization hook to set needs_review based on confidence."""
        if self.confidence < 0.6:
            self.needs_review = True
        if self.type == BlockType.FORMULA and not self.latex:
            self.needs_review = True

    def is_mathematical(self) -> bool:
        """Check if block contains mathematical content."""
        return self.type in {
            BlockType.FORMULA,
            BlockType.THEOREM,
            BlockType.DEFINITION,
            BlockType.PROOF,
        }

    def should_preserve_verbatim(self) -> bool:
        """Check if content should be preserved verbatim."""
        return self.action == BlockAction.VERBATIM

    def should_summarize(self) -> bool:
        """Check if content should be summarized."""
        return self.action == BlockAction.SUMMARIZE

    def get_display_name(self) -> str:
        """
        Get display name for the block.

        Returns:
            Block name or type if no name specified
        """
        if self.name:
            return self.name
        return self.type.value.capitalize()

    model_config = {"json_schema_extra": {"examples": [
        {
            "type": "theorem",
            "content": "Siano a e b due interi non entrambi nulli...",
            "action": "verbatim",
            "name": "Teorema di Bézout",
            "latex": None,
            "confidence": 0.95,
            "needs_review": False,
            "metadata": {"page": 12, "line_start": 45},
        },
        {
            "type": "formula",
            "content": "ax + by = gcd(a,b)",
            "action": "latex",
            "name": None,
            "latex": "ax + by = \\gcd(a,b)",
            "confidence": 0.88,
            "needs_review": False,
            "metadata": {"extracted_by": "pix2tex"},
        },
    ]}}


class ClassifiedChapter(BaseModel):
    """
    Chapter with classified content blocks.

    Attributes:
        chapter_id: Reference to original Chapter ID
        title: Chapter title
        blocks: List of classified blocks
        summary: Optional chapter summary
        metadata: Additional metadata
    """

    chapter_id: str = Field(..., description="Original chapter ID")
    title: str = Field(..., description="Chapter title")
    blocks: List[ClassifiedBlock] = Field(
        default_factory=list, description="Classified content blocks"
    )
    summary: Optional[str] = Field(None, description="Optional chapter summary")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    def get_block_count(self) -> int:
        """Get total number of blocks."""
        return len(self.blocks)

    def get_blocks_by_type(self, block_type: BlockType) -> List[ClassifiedBlock]:
        """
        Get all blocks of a specific type.

        Args:
            block_type: Type of block to retrieve

        Returns:
            List of matching blocks
        """
        return [block for block in self.blocks if block.type == block_type]

    def get_blocks_needing_review(self) -> List[ClassifiedBlock]:
        """
        Get all blocks flagged for review.

        Returns:
            List of blocks needing review
        """
        return [block for block in self.blocks if block.needs_review]

    def get_formulas(self) -> List[ClassifiedBlock]:
        """Get all formula blocks."""
        return self.get_blocks_by_type(BlockType.FORMULA)

    def get_theorems(self) -> List[ClassifiedBlock]:
        """Get all theorem blocks."""
        return self.get_blocks_by_type(BlockType.THEOREM)

    def get_definitions(self) -> List[ClassifiedBlock]:
        """Get all definition blocks."""
        return self.get_blocks_by_type(BlockType.DEFINITION)

    def has_mathematical_content(self) -> bool:
        """Check if chapter contains mathematical content."""
        return any(block.is_mathematical() for block in self.blocks)

    def get_confidence_stats(self) -> dict:
        """
        Get confidence statistics for blocks.

        Returns:
            Dictionary with min, max, avg, median confidence
        """
        if not self.blocks:
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "median": 0.0}

        confidences = [block.confidence for block in self.blocks]
        sorted_conf = sorted(confidences)

        return {
            "min": min(confidences),
            "max": max(confidences),
            "avg": sum(confidences) / len(confidences),
            "median": sorted_conf[len(sorted_conf) // 2],
            "review_needed_count": len(self.get_blocks_needing_review()),
        }

    def update_metadata(self) -> None:
        """Update metadata with computed statistics."""
        self.metadata.update(
            {
                "block_count": self.get_block_count(),
                "has_math": self.has_mathematical_content(),
                "formula_count": len(self.get_formulas()),
                "theorem_count": len(self.get_theorems()),
                "definition_count": len(self.get_definitions()),
                "confidence_stats": self.get_confidence_stats(),
            }
        )


class ClassifiedDocument(BaseModel):
    """
    Complete document with all classified chapters.

    Attributes:
        pdf_path: Path to source PDF
        chapters: List of classified chapters
        total_blocks: Total number of blocks across all chapters
        metadata: Document-level metadata
    """

    pdf_path: str = Field(..., description="Path to source PDF")
    chapters: List[ClassifiedChapter] = Field(
        default_factory=list, description="Classified chapters"
    )
    total_blocks: int = Field(0, ge=0, description="Total blocks in document")
    metadata: dict = Field(default_factory=dict, description="Document metadata")

    def model_post_init(self, __context) -> None:
        """Calculate total blocks after initialization."""
        self.total_blocks = sum(ch.get_block_count() for ch in self.chapters)

    def get_chapter_by_id(self, chapter_id: str) -> Optional[ClassifiedChapter]:
        """
        Get chapter by ID.

        Args:
            chapter_id: Chapter identifier

        Returns:
            ClassifiedChapter or None
        """
        for chapter in self.chapters:
            if chapter.chapter_id == chapter_id:
                return chapter
        return None

    def get_all_blocks_needing_review(self) -> List[tuple[str, ClassifiedBlock]]:
        """
        Get all blocks needing review across all chapters.

        Returns:
            List of tuples (chapter_id, block)
        """
        review_blocks = []
        for chapter in self.chapters:
            for block in chapter.get_blocks_needing_review():
                review_blocks.append((chapter.chapter_id, block))
        return review_blocks

    def get_document_stats(self) -> dict:
        """
        Get document-level statistics.

        Returns:
            Dictionary with document statistics
        """
        total_formulas = sum(len(ch.get_formulas()) for ch in self.chapters)
        total_theorems = sum(len(ch.get_theorems()) for ch in self.chapters)
        total_definitions = sum(len(ch.get_definitions()) for ch in self.chapters)
        total_review = len(self.get_all_blocks_needing_review())

        return {
            "total_chapters": len(self.chapters),
            "total_blocks": self.total_blocks,
            "total_formulas": total_formulas,
            "total_theorems": total_theorems,
            "total_definitions": total_definitions,
            "total_needing_review": total_review,
            "avg_blocks_per_chapter": (
                self.total_blocks / len(self.chapters) if self.chapters else 0
            ),
        }
