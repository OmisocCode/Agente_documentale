"""
Enumerations for PDF Math Agent data models.
"""

from enum import Enum


class BlockType(str, Enum):
    """
    Type of content block in a document.

    Attributes:
        NARRATIVE: Regular text/explanation
        THEOREM: Theorem, lemma, or corollary
        DEFINITION: Mathematical definition
        FORMULA: Mathematical formula/equation
        PROOF: Proof of theorem
        EXAMPLE: Worked example
        EXERCISE: Exercise or problem
        REMARK: Remark or note
    """

    NARRATIVE = "narrative"
    THEOREM = "theorem"
    DEFINITION = "definition"
    FORMULA = "formula"
    PROOF = "proof"
    EXAMPLE = "example"
    EXERCISE = "exercise"
    REMARK = "remark"


class BlockAction(str, Enum):
    """
    Action to take on a content block.

    Attributes:
        SUMMARIZE: Summarize the content
        VERBATIM: Keep content as-is
        LATEX: Render as LaTeX (for formulas)
        SKIP: Skip this block
    """

    SUMMARIZE = "summarize"
    VERBATIM = "verbatim"
    LATEX = "latex"
    SKIP = "skip"


class PDFType(str, Enum):
    """
    Type of PDF document.

    Attributes:
        AUTO: Auto-detect PDF type
        LATEX_COMPILED: PDF compiled from LaTeX source
        SCANNED: Scanned document (requires OCR)
        HANDWRITTEN: Handwritten document (requires vision models)
        MIXED: Mixed content (some digital, some scanned)
    """

    AUTO = "auto"
    LATEX_COMPILED = "latex_compiled"
    SCANNED = "scanned"
    HANDWRITTEN = "handwritten"
    MIXED = "mixed"


class ProcessingStatus(str, Enum):
    """
    Status of workflow processing.

    Attributes:
        PENDING: Not yet started
        IN_PROGRESS: Currently processing
        COMPLETED: Successfully completed
        FAILED: Processing failed
        CANCELLED: Cancelled by user
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTask(str, Enum):
    """
    Agent task identifier.

    Attributes:
        TASK_1_CHAPTER: Chapter extraction (Task 1)
        TASK_2_CLASSIFIER: Content classification (Task 2)
        TASK_3_COMPOSER: HTML composition (Task 3)
    """

    TASK_1_CHAPTER = "task1"
    TASK_2_CLASSIFIER = "task2"
    TASK_3_COMPOSER = "task3"
