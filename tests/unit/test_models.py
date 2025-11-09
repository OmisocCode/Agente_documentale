"""
Unit tests for data models.
"""

import pytest
from datetime import datetime

from src.models.enums import BlockType, BlockAction, PDFType, ProcessingStatus, AgentTask
from src.models.chapter import Chapter, ChapterCollection
from src.models.block import ClassifiedBlock, ClassifiedChapter, ClassifiedDocument
from src.models.state import AgentState, TaskResult


class TestChapter:
    """Tests for Chapter model."""

    def test_create_chapter(self):
        """Test creating a valid chapter."""
        chapter = Chapter(
            id="ch1",
            title="Introduction",
            pages=[1, 2, 3],
            content_raw="This is the introduction...",
            level=0,
        )

        assert chapter.id == "ch1"
        assert chapter.title == "Introduction"
        assert chapter.pages == [1, 2, 3]
        assert chapter.get_page_count() == 3

    def test_chapter_page_validation(self):
        """Test that pages are sorted and deduplicated."""
        chapter = Chapter(
            id="ch1",
            title="Test",
            pages=[3, 1, 2, 1],  # Unsorted with duplicate
            content_raw="Test content",
        )

        # Should be sorted and deduplicated
        assert chapter.pages == [1, 2, 3]

    def test_page_range_formatting(self):
        """Test page range formatting."""
        # Single page
        ch1 = Chapter(id="ch1", title="Test", pages=[5], content_raw="Test")
        assert ch1.get_page_range() == "5"

        # Consecutive pages
        ch2 = Chapter(id="ch2", title="Test", pages=[1, 2, 3, 4], content_raw="Test")
        assert ch2.get_page_range() == "1-4"

        # Non-consecutive pages
        ch3 = Chapter(id="ch3", title="Test", pages=[1, 2, 5, 6, 10], content_raw="Test")
        assert ch3.get_page_range() == "1-2, 5-6, 10"

    def test_word_count(self):
        """Test word count calculation."""
        chapter = Chapter(
            id="ch1",
            title="Test",
            pages=[1],
            content_raw="This is a test chapter with ten words here.",
        )

        assert chapter.get_word_count() == 10


class TestChapterCollection:
    """Tests for ChapterCollection model."""

    def test_create_collection(self):
        """Test creating a chapter collection."""
        chapters = [
            Chapter(id="ch1", title="Chapter 1", pages=[1, 2], content_raw="Content 1"),
            Chapter(id="ch2", title="Chapter 2", pages=[3, 4], content_raw="Content 2"),
        ]

        collection = ChapterCollection(
            chapters=chapters, total_pages=10, pdf_path="test.pdf"
        )

        assert collection.get_total_chapters() == 2
        assert collection.total_pages == 10

    def test_no_overlapping_pages(self):
        """Test that overlapping pages raise error."""
        chapters = [
            Chapter(id="ch1", title="Chapter 1", pages=[1, 2, 3], content_raw="Content 1"),
            Chapter(id="ch2", title="Chapter 2", pages=[3, 4, 5], content_raw="Content 2"),
            # Page 3 overlaps!
        ]

        with pytest.raises(ValueError, match="overlapping"):
            ChapterCollection(chapters=chapters, total_pages=10, pdf_path="test.pdf")

    def test_get_chapter_by_page(self):
        """Test finding chapter by page number."""
        chapters = [
            Chapter(id="ch1", title="Chapter 1", pages=[1, 2], content_raw="Content 1"),
            Chapter(id="ch2", title="Chapter 2", pages=[3, 4], content_raw="Content 2"),
        ]

        collection = ChapterCollection(
            chapters=chapters, total_pages=10, pdf_path="test.pdf"
        )

        ch = collection.get_chapter_by_page(3)
        assert ch is not None
        assert ch.id == "ch2"

        # Page not in any chapter
        assert collection.get_chapter_by_page(10) is None

    def test_coverage_percentage(self):
        """Test coverage percentage calculation."""
        chapters = [
            Chapter(id="ch1", title="Chapter 1", pages=[1, 2, 3], content_raw="Content 1"),
            Chapter(id="ch2", title="Chapter 2", pages=[5, 6], content_raw="Content 2"),
        ]

        collection = ChapterCollection(
            chapters=chapters, total_pages=10, pdf_path="test.pdf"
        )

        # 5 pages covered out of 10 = 50%
        assert collection.get_coverage_percentage() == 50.0


class TestClassifiedBlock:
    """Tests for ClassifiedBlock model."""

    def test_create_block(self):
        """Test creating a classified block."""
        block = ClassifiedBlock(
            type=BlockType.THEOREM,
            content="For all integers a, b...",
            action=BlockAction.VERBATIM,
            name="Bézout's Theorem",
            confidence=0.95,
        )

        assert block.type == BlockType.THEOREM
        assert block.is_mathematical()
        assert block.should_preserve_verbatim()

    def test_low_confidence_flagging(self):
        """Test that low confidence blocks are flagged for review."""
        block = ClassifiedBlock(
            type=BlockType.FORMULA,
            content="x + y = z",
            action=BlockAction.LATEX,
            confidence=0.5,  # Low confidence
        )

        assert block.needs_review is True

    def test_formula_without_latex_flagged(self):
        """Test that formulas without LaTeX are flagged."""
        block = ClassifiedBlock(
            type=BlockType.FORMULA,
            content="Some formula",
            action=BlockAction.LATEX,
            latex=None,  # No LaTeX provided
            confidence=0.9,
        )

        assert block.needs_review is True


class TestClassifiedChapter:
    """Tests for ClassifiedChapter model."""

    def test_get_blocks_by_type(self):
        """Test filtering blocks by type."""
        blocks = [
            ClassifiedBlock(
                type=BlockType.NARRATIVE, content="Text", action=BlockAction.SUMMARIZE
            ),
            ClassifiedBlock(
                type=BlockType.THEOREM, content="Theorem", action=BlockAction.VERBATIM
            ),
            ClassifiedBlock(
                type=BlockType.FORMULA, content="Formula", action=BlockAction.LATEX, latex="x=1"
            ),
        ]

        chapter = ClassifiedChapter(chapter_id="ch1", title="Test", blocks=blocks)

        theorems = chapter.get_theorems()
        assert len(theorems) == 1
        assert theorems[0].type == BlockType.THEOREM

        formulas = chapter.get_formulas()
        assert len(formulas) == 1

    def test_confidence_stats(self):
        """Test confidence statistics."""
        blocks = [
            ClassifiedBlock(
                type=BlockType.NARRATIVE, content="1", action=BlockAction.SUMMARIZE, confidence=0.8
            ),
            ClassifiedBlock(
                type=BlockType.NARRATIVE, content="2", action=BlockAction.SUMMARIZE, confidence=0.9
            ),
            ClassifiedBlock(
                type=BlockType.NARRATIVE, content="3", action=BlockAction.SUMMARIZE, confidence=0.7
            ),
        ]

        chapter = ClassifiedChapter(chapter_id="ch1", title="Test", blocks=blocks)
        stats = chapter.get_confidence_stats()

        assert stats["min"] == 0.7
        assert stats["max"] == 0.9
        assert stats["avg"] == pytest.approx(0.8, 0.01)


class TestAgentState:
    """Tests for AgentState model."""

    def test_create_state(self):
        """Test creating agent state."""
        state = AgentState(
            session_id="test_session_001",
            pdf_path="test.pdf",
            pdf_type=PDFType.LATEX_COMPILED,
        )

        assert state.session_id == "test_session_001"
        assert state.pdf_type == PDFType.LATEX_COMPILED
        assert len(state.task_results) == 3  # 3 tasks initialized

    def test_task_lifecycle(self):
        """Test task start/complete/fail lifecycle."""
        state = AgentState(session_id="test", pdf_path="test.pdf")

        # Start task
        state.start_task(AgentTask.TASK_1_CHAPTER)
        assert state.current_task == AgentTask.TASK_1_CHAPTER
        result = state.get_task_result(AgentTask.TASK_1_CHAPTER)
        assert result.status == ProcessingStatus.IN_PROGRESS

        # Complete task
        state.complete_task(AgentTask.TASK_1_CHAPTER)
        assert state.current_task is None
        assert state.is_task_completed(AgentTask.TASK_1_CHAPTER)

    def test_get_next_task(self):
        """Test getting next task in sequence."""
        state = AgentState(session_id="test", pdf_path="test.pdf")

        # Initially, next task should be Task 1
        assert state.get_next_task() == AgentTask.TASK_1_CHAPTER

        # Complete Task 1
        state.start_task(AgentTask.TASK_1_CHAPTER)
        state.complete_task(AgentTask.TASK_1_CHAPTER)

        # Next should be Task 2
        assert state.get_next_task() == AgentTask.TASK_2_CLASSIFIER

        # Complete Task 2
        state.start_task(AgentTask.TASK_2_CLASSIFIER)
        state.complete_task(AgentTask.TASK_2_CLASSIFIER)

        # Next should be Task 3
        assert state.get_next_task() == AgentTask.TASK_3_COMPOSER

        # Complete Task 3
        state.start_task(AgentTask.TASK_3_COMPOSER)
        state.complete_task(AgentTask.TASK_3_COMPOSER)

        # No more tasks
        assert state.get_next_task() is None

    def test_progress_percentage(self):
        """Test progress calculation."""
        state = AgentState(session_id="test", pdf_path="test.pdf")

        # No tasks completed
        assert state.get_progress_percentage() == 0.0

        # Complete Task 1 (1/3 = 33.33%)
        state.start_task(AgentTask.TASK_1_CHAPTER)
        state.complete_task(AgentTask.TASK_1_CHAPTER)
        assert state.get_progress_percentage() == pytest.approx(33.33, 0.01)

        # Complete Task 2 (2/3 = 66.66%)
        state.start_task(AgentTask.TASK_2_CLASSIFIER)
        state.complete_task(AgentTask.TASK_2_CLASSIFIER)
        assert state.get_progress_percentage() == pytest.approx(66.66, 0.01)

        # Complete Task 3 (3/3 = 100%)
        state.start_task(AgentTask.TASK_3_COMPOSER)
        state.complete_task(AgentTask.TASK_3_COMPOSER)
        assert state.get_progress_percentage() == 100.0

    def test_get_summary(self):
        """Test state summary generation."""
        state = AgentState(session_id="test_session", pdf_path="test.pdf")

        summary = state.get_summary()

        assert summary["session_id"] == "test_session"
        assert summary["pdf_path"] == "test.pdf"
        assert "progress_percentage" in summary
        assert "completed_tasks" in summary
        assert "next_task" in summary


class TestTaskResult:
    """Tests for TaskResult model."""

    def test_task_timing(self):
        """Test task timing calculation."""
        import time

        result = TaskResult(task=AgentTask.TASK_1_CHAPTER)

        result.start()
        assert result.status == ProcessingStatus.IN_PROGRESS
        assert result.started_at is not None

        time.sleep(0.1)  # Wait a bit

        result.complete()
        assert result.status == ProcessingStatus.COMPLETED
        assert result.duration_seconds is not None
        assert result.duration_seconds > 0

    def test_task_failure(self):
        """Test task failure handling."""
        result = TaskResult(task=AgentTask.TASK_1_CHAPTER)

        result.start()
        result.fail("Test error message")

        assert result.status == ProcessingStatus.FAILED
        assert result.error == "Test error message"
        assert result.is_failed()
