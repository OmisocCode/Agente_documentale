"""
Agent state model for workflow management.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from src.models.block import ClassifiedChapter, ClassifiedDocument
from src.models.chapter import Chapter, ChapterCollection
from src.models.enums import AgentTask, PDFType, ProcessingStatus


class TaskResult(BaseModel):
    """
    Result of a single agent task.

    Attributes:
        task: Task identifier
        status: Processing status
        started_at: Task start timestamp
        completed_at: Task completion timestamp
        duration_seconds: Task duration in seconds
        error: Error message if failed
        metadata: Additional task metadata
    """

    task: AgentTask = Field(..., description="Task identifier")
    status: ProcessingStatus = Field(
        ProcessingStatus.PENDING, description="Processing status"
    )
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_seconds: Optional[float] = Field(None, ge=0, description="Duration in seconds")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: dict = Field(default_factory=dict, description="Task metadata")

    def start(self) -> None:
        """Mark task as started."""
        self.status = ProcessingStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete(self) -> None:
        """Mark task as completed."""
        self.status = ProcessingStatus.COMPLETED
        self.completed_at = datetime.now()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def fail(self, error_message: str) -> None:
        """
        Mark task as failed.

        Args:
            error_message: Error description
        """
        self.status = ProcessingStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error_message
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def is_completed(self) -> bool:
        """Check if task completed successfully."""
        return self.status == ProcessingStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status == ProcessingStatus.FAILED


class AgentState(BaseModel):
    """
    Global state for the PDF processing workflow.

    This state is passed through all three agent tasks:
    - Task 1 (Chapter Agent): Populates chapters
    - Task 2 (Classifier Agent): Populates classified_document
    - Task 3 (Composer Agent): Populates html_files and output_dir

    Attributes:
        session_id: Unique session identifier
        pdf_path: Path to input PDF
        pdf_type: Type of PDF (auto-detected or specified)
        created_at: State creation timestamp
        updated_at: Last update timestamp

        # After Task 1
        chapter_collection: Extracted chapters

        # After Task 2
        classified_document: Document with classified blocks

        # After Task 3
        html_files: Generated HTML files (chapter_id -> file_path)
        output_dir: Output directory path

        # Task tracking
        task_results: Results for each task
        current_task: Current task being executed

        # Metadata
        metadata: Additional state metadata
    """

    # Core identifiers
    session_id: str = Field(..., description="Unique session ID")
    pdf_path: str = Field(..., description="Path to input PDF")
    pdf_type: PDFType = Field(PDFType.AUTO, description="PDF type")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")

    # Task 1 output
    chapter_collection: Optional[ChapterCollection] = Field(
        None, description="Extracted chapters (after Task 1)"
    )

    # Task 2 output
    classified_document: Optional[ClassifiedDocument] = Field(
        None, description="Classified document (after Task 2)"
    )

    # Task 3 output
    html_files: Dict[str, str] = Field(
        default_factory=dict, description="Generated HTML files (chapter_id -> path)"
    )
    output_dir: Optional[str] = Field(None, description="Output directory")

    # Task tracking
    task_results: Dict[str, TaskResult] = Field(
        default_factory=dict, description="Task results"
    )
    current_task: Optional[AgentTask] = Field(None, description="Current task")

    # Metadata
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @field_validator("pdf_path")
    @classmethod
    def validate_pdf_exists(cls, v: str) -> str:
        """Validate that PDF file exists (skip validation for now, will check at runtime)."""
        return v

    def model_post_init(self, __context) -> None:
        """Initialize task results."""
        if not self.task_results:
            self.task_results = {
                AgentTask.TASK_1_CHAPTER.value: TaskResult(task=AgentTask.TASK_1_CHAPTER),
                AgentTask.TASK_2_CLASSIFIER.value: TaskResult(task=AgentTask.TASK_2_CLASSIFIER),
                AgentTask.TASK_3_COMPOSER.value: TaskResult(task=AgentTask.TASK_3_COMPOSER),
            }

    def update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()

    def start_task(self, task: AgentTask) -> None:
        """
        Mark a task as started.

        Args:
            task: Task to start
        """
        self.current_task = task
        self.task_results[task.value].start()
        self.update_timestamp()

    def complete_task(self, task: AgentTask) -> None:
        """
        Mark a task as completed.

        Args:
            task: Task to complete
        """
        self.task_results[task.value].complete()
        self.current_task = None
        self.update_timestamp()

    def fail_task(self, task: AgentTask, error: str) -> None:
        """
        Mark a task as failed.

        Args:
            task: Task that failed
            error: Error message
        """
        self.task_results[task.value].fail(error)
        self.current_task = None
        self.update_timestamp()

    def get_task_result(self, task: AgentTask) -> TaskResult:
        """
        Get result for a specific task.

        Args:
            task: Task to query

        Returns:
            TaskResult object
        """
        return self.task_results[task.value]

    def is_task_completed(self, task: AgentTask) -> bool:
        """
        Check if a task is completed.

        Args:
            task: Task to check

        Returns:
            True if task completed successfully
        """
        return self.task_results[task.value].is_completed()

    def get_completed_tasks(self) -> List[AgentTask]:
        """
        Get list of completed tasks.

        Returns:
            List of completed task identifiers
        """
        completed = []
        for task_name, result in self.task_results.items():
            if result.is_completed():
                completed.append(AgentTask(task_name))
        return completed

    def get_next_task(self) -> Optional[AgentTask]:
        """
        Get next task to execute.

        Returns:
            Next task or None if all completed
        """
        task_order = [
            AgentTask.TASK_1_CHAPTER,
            AgentTask.TASK_2_CLASSIFIER,
            AgentTask.TASK_3_COMPOSER,
        ]

        for task in task_order:
            if not self.is_task_completed(task):
                return task

        return None  # All tasks completed

    def get_progress_percentage(self) -> float:
        """
        Get overall progress percentage.

        Returns:
            Progress as percentage (0-100)
        """
        completed_count = len(self.get_completed_tasks())
        total_tasks = 3
        return (completed_count / total_tasks) * 100

    def get_total_duration(self) -> float:
        """
        Get total processing duration in seconds.

        Returns:
            Total duration across all tasks
        """
        total = 0.0
        for result in self.task_results.values():
            if result.duration_seconds:
                total += result.duration_seconds
        return total

    def get_summary(self) -> dict:
        """
        Get state summary.

        Returns:
            Dictionary with state summary
        """
        return {
            "session_id": self.session_id,
            "pdf_path": self.pdf_path,
            "pdf_type": self.pdf_type.value,
            "created_at": self.created_at.isoformat(),
            "progress_percentage": self.get_progress_percentage(),
            "completed_tasks": [t.value for t in self.get_completed_tasks()],
            "current_task": self.current_task.value if self.current_task else None,
            "next_task": self.get_next_task().value if self.get_next_task() else None,
            "total_duration_seconds": self.get_total_duration(),
            "chapters_extracted": (
                self.chapter_collection.get_total_chapters()
                if self.chapter_collection
                else 0
            ),
            "blocks_classified": (
                self.classified_document.total_blocks if self.classified_document else 0
            ),
            "html_files_generated": len(self.html_files),
            "output_dir": self.output_dir,
        }

    def validate_task1_output(self) -> bool:
        """
        Validate Task 1 output.

        Returns:
            True if valid
        """
        if not self.chapter_collection:
            return False
        return self.chapter_collection.get_total_chapters() > 0

    def validate_task2_output(self) -> bool:
        """
        Validate Task 2 output.

        Returns:
            True if valid
        """
        if not self.classified_document:
            return False
        return len(self.classified_document.chapters) > 0

    def validate_task3_output(self) -> bool:
        """
        Validate Task 3 output.

        Returns:
            True if valid
        """
        if not self.output_dir or not self.html_files:
            return False
        # Check that output directory exists
        return Path(self.output_dir).exists()

    model_config = {"json_schema_extra": {"examples": [
        {
            "session_id": "20240109_143022_abc123",
            "pdf_path": "data/samples/geometria_proiettiva.pdf",
            "pdf_type": "latex_compiled",
            "created_at": "2024-01-09T14:30:22",
            "updated_at": "2024-01-09T14:35:10",
            "current_task": "task2",
            "metadata": {"user": "researcher", "priority": "high"},
        }
    ]}}
