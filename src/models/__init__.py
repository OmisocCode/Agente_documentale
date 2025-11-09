"""
Data models for agent state and workflow.

Contains Pydantic models for:
- AgentState: Global workflow state
- Chapter: Chapter representation
- ClassifiedBlock: Classified content blocks
"""

from src.models.enums import (
    AgentTask,
    BlockAction,
    BlockType,
    PDFType,
    ProcessingStatus,
)
from src.models.state import AgentState, TaskResult
from src.models.chapter import Chapter, ChapterCollection
from src.models.block import (
    ClassifiedBlock,
    ClassifiedChapter,
    ClassifiedDocument,
)

__all__ = [
    # Enums
    "AgentTask",
    "BlockAction",
    "BlockType",
    "PDFType",
    "ProcessingStatus",
    # State
    "AgentState",
    "TaskResult",
    # Chapter
    "Chapter",
    "ChapterCollection",
    # Block
    "ClassifiedBlock",
    "ClassifiedChapter",
    "ClassifiedDocument",
]
