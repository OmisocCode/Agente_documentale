"""
Workflow orchestrator for PDF Math Agent.

Coordinates the three-agent pipeline:
Task 1 → Task 2 → Task 3
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.agents.chapter_agent import ChapterAgent
from src.agents.classifier_agent import ClassifierAgent
from src.agents.composer_agent import ComposerAgent
from src.models.enums import PDFType
from src.models.state import AgentState
from src.utils.checkpoint_manager import get_checkpoint_manager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFSummarizerWorkflow:
    """
    Main workflow orchestrator for PDF summarization.

    Executes the three-agent pipeline:
    1. Chapter Agent: Extract chapters
    2. Classifier Agent: Classify blocks
    3. Composer Agent: Generate HTML
    """

    def __init__(
        self,
        llm_provider: str = "groq",
        css_theme: str = "math-document",
        enable_checkpoints: bool = True,
    ):
        """
        Initialize workflow.

        Args:
            llm_provider: LLM provider (groq, anthropic, openai)
            css_theme: CSS theme for HTML output
            enable_checkpoints: Whether to save checkpoints after each task
        """
        self.llm_provider = llm_provider
        self.css_theme = css_theme
        self.enable_checkpoints = enable_checkpoints

        # Initialize agents
        self.chapter_agent = ChapterAgent(llm_provider=llm_provider)
        self.classifier_agent = ClassifierAgent(llm_provider=llm_provider)
        self.composer_agent = ComposerAgent(
            llm_provider=llm_provider, css_theme=css_theme
        )

        # Checkpoint manager
        if enable_checkpoints:
            self.checkpoint_manager = get_checkpoint_manager()
        else:
            self.checkpoint_manager = None

        logger.info(f"Workflow initialized with provider: {llm_provider}")

    def run(
        self,
        pdf_path: str,
        pdf_type: str = "auto",
        session_id: Optional[str] = None,
    ) -> str:
        """
        Run complete workflow on a PDF.

        Args:
            pdf_path: Path to input PDF file
            pdf_type: PDF type (auto, latex_compiled, scanned, handwritten)
            session_id: Optional session ID (generated if not provided)

        Returns:
            Path to output directory

        Example:
            >>> workflow = PDFSummarizerWorkflow()
            >>> output_dir = workflow.run("document.pdf")
            >>> print(f"HTML generated in: {output_dir}")
        """
        # Validate PDF exists
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Generate session ID
        if session_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_uuid = str(uuid.uuid4())[:8]
            session_id = f"{timestamp}_{short_uuid}"

        logger.info(f"Starting workflow - Session: {session_id}")
        logger.info(f"PDF: {pdf_path}")

        # Create initial state
        state = AgentState(
            session_id=session_id,
            pdf_path=str(pdf_path_obj.absolute()),
            pdf_type=PDFType(pdf_type),
        )

        try:
            # Task 1: Extract chapters
            logger.info("=" * 60)
            logger.info("TASK 1: CHAPTER EXTRACTION")
            logger.info("=" * 60)

            state = self.chapter_agent.run(state)

            if self.checkpoint_manager:
                self.checkpoint_manager.save(state, task=state.current_task or state.get_completed_tasks()[-1])

            # Task 2: Classify blocks
            logger.info("=" * 60)
            logger.info("TASK 2: CONTENT CLASSIFICATION")
            logger.info("=" * 60)

            state = self.classifier_agent.run(state)

            if self.checkpoint_manager:
                self.checkpoint_manager.save(state, task=state.current_task or state.get_completed_tasks()[-1])

            # Task 3: Generate HTML
            logger.info("=" * 60)
            logger.info("TASK 3: HTML COMPOSITION")
            logger.info("=" * 60)

            state = self.composer_agent.run(state)

            if self.checkpoint_manager:
                self.checkpoint_manager.save(state, task=state.current_task or state.get_completed_tasks()[-1])

            # Final summary
            logger.info("=" * 60)
            logger.info("WORKFLOW COMPLETE")
            logger.info("=" * 60)

            summary = state.get_summary()
            logger.info(f"Session ID: {summary['session_id']}")
            logger.info(f"Progress: {summary['progress_percentage']}%")
            logger.info(f"Chapters: {summary['chapters_extracted']}")
            logger.info(f"Blocks: {summary['blocks_classified']}")
            logger.info(f"HTML files: {summary['html_files_generated']}")
            logger.info(f"Duration: {summary['total_duration_seconds']:.2f}s")
            logger.info(f"Output: {summary['output_dir']}")

            return state.output_dir

        except Exception as e:
            logger.error(f"Workflow failed: {e}")

            # Save checkpoint on failure
            if self.checkpoint_manager:
                self.checkpoint_manager.save(
                    state, metadata={"error": str(e), "failed": True}
                )

            raise

    def resume(self, session_id: str) -> str:
        """
        Resume workflow from last checkpoint.

        Args:
            session_id: Session ID to resume

        Returns:
            Path to output directory

        Example:
            >>> workflow = PDFSummarizerWorkflow()
            >>> output_dir = workflow.resume("20240109_143022_abc123")
        """
        if not self.checkpoint_manager:
            raise ValueError("Checkpoints are disabled")

        logger.info(f"Resuming workflow - Session: {session_id}")

        # Auto-recover state
        state = self.checkpoint_manager.auto_recover(session_id)

        if state is None:
            raise ValueError(f"No checkpoint found for session: {session_id}")

        logger.info(f"Recovered from checkpoint")
        logger.info(f"Progress: {state.get_progress_percentage()}%")

        # Determine next task
        next_task = state.get_next_task()

        if next_task is None:
            logger.info("All tasks already completed")
            return state.output_dir

        logger.info(f"Resuming from: {next_task.value}")

        # Continue workflow from next task
        try:
            if next_task.value == "task2":
                state = self.classifier_agent.run(state)
                if self.checkpoint_manager:
                    self.checkpoint_manager.save(state, task=state.get_completed_tasks()[-1])

            if next_task.value == "task3" or state.get_next_task():
                state = self.composer_agent.run(state)
                if self.checkpoint_manager:
                    self.checkpoint_manager.save(state, task=state.get_completed_tasks()[-1])

            logger.info("Workflow resumed successfully")
            return state.output_dir

        except Exception as e:
            logger.error(f"Workflow resume failed: {e}")

            # Save checkpoint on failure
            if self.checkpoint_manager:
                self.checkpoint_manager.save(
                    state, metadata={"error": str(e), "resumed": True, "failed": True}
                )

            raise
