"""
Classifier Agent - Task 2: Classify content blocks.

Uses LaTeX Tools to identify and classify mathematical structures.
"""

from typing import List

from src.agents.base_agent import BaseAgent
from src.models.block import ClassifiedBlock, ClassifiedChapter, ClassifiedDocument
from src.models.enums import AgentTask, BlockAction, BlockType
from src.models.state import AgentState
from src.tools.latex_tools import LaTeXProcessor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ClassifierAgent(BaseAgent):
    """
    Classifier Agent - classifies content blocks in chapters.

    Uses LaTeX Tools to:
    - Extract formulas
    - Detect theorems, definitions, proofs
    - Split text into logical blocks
    - Classify each block by type
    - Assign action (summarize/verbatim/latex)
    """

    def __init__(self, llm_provider: str = "groq", model: str = None):
        """
        Initialize Classifier Agent.

        Args:
            llm_provider: LLM provider (groq, anthropic, openai)
            model: Model name (if None, uses config default)
        """
        super().__init__(
            task=AgentTask.TASK_2_CLASSIFIER,
            llm_provider=llm_provider,
            model=model,
        )

        # Initialize LaTeX processor
        self.latex_processor = LaTeXProcessor()

    def execute(self, state: AgentState) -> AgentState:
        """
        Execute content classification.

        Args:
            state: Current workflow state (must have chapter_collection)

        Returns:
            Updated state with classified_document populated
        """
        if not state.chapter_collection:
            raise ValueError("Chapter collection is required for classification")

        logger.info(
            f"Classifying {state.chapter_collection.get_total_chapters()} chapters"
        )

        classified_chapters = []

        for chapter in state.chapter_collection.chapters:
            logger.info(f"Classifying chapter: {chapter.title}")

            # Classify chapter
            classified_chapter = self._classify_chapter(chapter)

            classified_chapters.append(classified_chapter)

            logger.info(
                f"  Classified {classified_chapter.get_block_count()} blocks "
                f"({len(classified_chapter.get_blocks_needing_review())} need review)"
            )

        # Create classified document
        classified_document = ClassifiedDocument(
            pdf_path=state.pdf_path,
            chapters=classified_chapters,
        )

        # Update state
        state.classified_document = classified_document

        # Log statistics
        stats = classified_document.get_document_stats()
        logger.info(f"Classification complete:")
        logger.info(f"  Total blocks: {stats['total_blocks']}")
        logger.info(f"  Formulas: {stats['total_formulas']}")
        logger.info(f"  Theorems: {stats['total_theorems']}")
        logger.info(f"  Definitions: {stats['total_definitions']}")
        logger.info(f"  Needing review: {stats['total_needing_review']}")

        return state

    def _classify_chapter(self, chapter) -> ClassifiedChapter:
        """
        Classify blocks in a single chapter.

        Args:
            chapter: Chapter object

        Returns:
            ClassifiedChapter with blocks
        """
        # Use LaTeX tools to split into blocks
        raw_blocks = self.latex_processor.split_into_blocks(
            chapter.content_raw, min_block_size=50
        )

        # Convert to ClassifiedBlock objects
        classified_blocks = []

        for raw_block in raw_blocks:
            # Create ClassifiedBlock
            block = ClassifiedBlock(
                type=raw_block["type"],
                content=raw_block["content"],
                action=raw_block.get("action", BlockAction.SUMMARIZE),
                name=raw_block.get("name"),
                latex=raw_block.get("latex"),
                confidence=raw_block.get("confidence", 0.7),
            )

            classified_blocks.append(block)

        # Create ClassifiedChapter
        classified_chapter = ClassifiedChapter(
            chapter_id=chapter.id,
            title=chapter.title,
            blocks=classified_blocks,
        )

        # Update metadata
        classified_chapter.update_metadata()

        return classified_chapter
