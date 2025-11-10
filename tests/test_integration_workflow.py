"""
Integration tests for complete workflow with mock LLM.

These tests verify the entire pipeline (Tasks 1-3) works correctly
without requiring real API keys.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.models.enums import PDFType
from src.workflow import PDFSummarizerWorkflow


@pytest.fixture
def test_pdf_path():
    """Fixture providing path to test PDF."""
    pdf_path = "data/samples/test.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"Test PDF not found at {pdf_path}")
    return pdf_path


@pytest.fixture
def temp_output_dir():
    """Fixture providing temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestWorkflowIntegration:
    """Integration tests for the complete workflow."""

    def test_workflow_with_mock_llm(self, test_pdf_path, temp_output_dir):
        """Test complete workflow using mock LLM provider."""
        # Create workflow with mock provider
        workflow = PDFSummarizerWorkflow(
            llm_provider="mock",
            css_theme="math-document",
            enable_checkpoints=False  # Disable for simpler testing
        )

        # Override output directory
        workflow.checkpoint_manager.checkpoint_dir = temp_output_dir

        # Run workflow
        output_dir = workflow.run(
            pdf_path=test_pdf_path,
            pdf_type="latex_compiled"
        )

        # Verify output directory was created
        assert output_dir is not None
        assert os.path.exists(output_dir)

        # Verify index.html exists
        index_path = os.path.join(output_dir, "index.html")
        assert os.path.exists(index_path), "index.html should be generated"

        # Verify at least one chapter HTML exists
        html_files = list(Path(output_dir).glob("chapter_*.html"))
        assert len(html_files) > 0, "At least one chapter HTML should be generated"

    def test_workflow_task1_chapters_extracted(self, test_pdf_path):
        """Test that Task 1 correctly extracts chapters."""
        workflow = PDFSummarizerWorkflow(
            llm_provider="mock",
            enable_checkpoints=False
        )

        # Create initial state
        from src.models.state import AgentState

        state = AgentState(
            session_id="test_session",
            pdf_path=test_pdf_path,
            pdf_type=PDFType.LATEX_COMPILED
        )

        # Run only Task 1
        state = workflow.chapter_agent.run(state)

        # Verify chapters were extracted
        assert state.chapter_collection is not None, "Chapter collection should be extracted"
        assert len(state.chapter_collection.chapters) > 0, "At least one chapter should be extracted"

        # Verify chapter structure
        for chapter in state.chapter_collection.chapters:
            assert chapter.id, "Chapter should have ID"
            assert chapter.title, "Chapter should have title"
            assert len(chapter.pages) > 0, "Chapter should have at least 1 page"
            assert chapter.content_raw, "Chapter should have content"

    def test_workflow_task2_classification(self, test_pdf_path):
        """Test that Task 2 correctly classifies content."""
        workflow = PDFSummarizerWorkflow(
            llm_provider="mock",
            enable_checkpoints=False
        )

        from src.models.state import AgentState

        state = AgentState(
            session_id="test_session",
            pdf_path=test_pdf_path,
            pdf_type=PDFType.LATEX_COMPILED
        )

        # Run Task 1 + Task 2
        state = workflow.chapter_agent.run(state)
        state = workflow.classifier_agent.run(state)

        # Verify classified blocks exist
        assert state.classified_chapters is not None, "Classified chapters should exist"
        assert len(state.classified_chapters) > 0, "At least one classified chapter should exist"

        # Verify classification structure
        for classified_chapter in state.classified_chapters:
            assert classified_chapter.chapter_id, "Classified chapter should have ID"
            assert classified_chapter.blocks is not None, "Classified chapter should have blocks"
            # Blocks might be empty for simple test PDFs, so just check type
            assert isinstance(classified_chapter.blocks, list), "Blocks should be a list"

    def test_workflow_task3_html_generation(self, test_pdf_path, temp_output_dir):
        """Test that Task 3 correctly generates HTML."""
        workflow = PDFSummarizerWorkflow(
            llm_provider="mock",
            css_theme="lecture-notes",
            enable_checkpoints=False
        )

        from src.models.state import AgentState

        state = AgentState(
            session_id="test_session",
            pdf_path=test_pdf_path,
            pdf_type=PDFType.LATEX_COMPILED,
            output_dir=temp_output_dir
        )

        # Run all three tasks
        state = workflow.chapter_agent.run(state)
        state = workflow.classifier_agent.run(state)
        state = workflow.composer_agent.run(state)

        # Verify HTML files were generated
        assert state.html_files is not None, "HTML files should be generated"
        assert "index.html" in state.html_files, "index.html should be generated"

        # Verify files exist on disk
        for filename, filepath in state.html_files.items():
            assert os.path.exists(filepath), f"{filename} should exist at {filepath}"

        # Verify HTML content structure
        index_path = state.html_files["index.html"]
        with open(index_path, "r", encoding="utf-8") as f:
            index_content = f.read()

        # Check for essential HTML elements
        assert "<html" in index_content.lower(), "Should contain HTML tag"
        assert "mathjax" in index_content.lower(), "Should include MathJax"
        assert "chapter" in index_content.lower(), "Should reference chapters"

    def test_workflow_with_checkpoints(self, test_pdf_path, temp_output_dir):
        """Test workflow with checkpointing enabled."""
        # First run - complete all tasks
        workflow1 = PDFSummarizerWorkflow(
            llm_provider="mock",
            enable_checkpoints=True
        )

        workflow1.checkpoint_manager.checkpoint_dir = temp_output_dir

        session_id = "checkpoint_test_session"
        output_dir = workflow1.run(
            pdf_path=test_pdf_path,
            pdf_type="latex_compiled",
            session_id=session_id
        )

        # Verify checkpoint files exist
        checkpoint_files = list(Path(temp_output_dir).glob(f"{session_id}_task*.json"))
        assert len(checkpoint_files) > 0, "Checkpoint files should be created"

        # Second run - should be able to load from checkpoint
        workflow2 = PDFSummarizerWorkflow(
            llm_provider="mock",
            enable_checkpoints=True
        )

        workflow2.checkpoint_manager.checkpoint_dir = temp_output_dir

        # Load state from checkpoint
        from src.models.enums import AgentTask

        loaded_state = workflow2.checkpoint_manager.load(
            session_id=session_id,
            task=AgentTask.TASK_1_CHAPTER
        )

        assert loaded_state is not None, "Should be able to load from checkpoint"
        assert loaded_state.chapters is not None, "Loaded state should have chapters"

    def test_workflow_error_handling(self):
        """Test workflow error handling with invalid input."""
        workflow = PDFSummarizerWorkflow(
            llm_provider="mock",
            enable_checkpoints=False
        )

        # Test with non-existent PDF
        with pytest.raises(Exception):
            workflow.run(
                pdf_path="/nonexistent/path/to/file.pdf",
                pdf_type="latex_compiled"
            )

    def test_workflow_different_css_themes(self, test_pdf_path, temp_output_dir):
        """Test workflow with different CSS themes."""
        themes = ["math-document", "lecture-notes", "presentation"]

        for theme in themes:
            workflow = PDFSummarizerWorkflow(
                llm_provider="mock",
                css_theme=theme,
                enable_checkpoints=False
            )

            from src.models.state import AgentState

            state = AgentState(
                session_id=f"test_{theme}",
                pdf_path=test_pdf_path,
                pdf_type=PDFType.LATEX_COMPILED,
                output_dir=os.path.join(temp_output_dir, theme)
            )

            # Run workflow
            state = workflow.chapter_agent.run(state)
            state = workflow.classifier_agent.run(state)
            state = workflow.composer_agent.run(state)

            # Verify HTML was generated
            assert state.html_files is not None, f"HTML should be generated for theme {theme}"
            assert "index.html" in state.html_files, f"index.html should exist for theme {theme}"


class TestWorkflowPerformance:
    """Performance tests for workflow (optional, for future optimization)."""

    def test_workflow_completes_in_reasonable_time(self, test_pdf_path):
        """Test that workflow completes within reasonable time."""
        import time

        workflow = PDFSummarizerWorkflow(
            llm_provider="mock",
            enable_checkpoints=False
        )

        start_time = time.time()

        output_dir = workflow.run(
            pdf_path=test_pdf_path,
            pdf_type="latex_compiled"
        )

        elapsed_time = time.time() - start_time

        # With mock LLM, should complete very quickly (< 10 seconds)
        assert elapsed_time < 10, f"Workflow took too long: {elapsed_time:.2f}s"
        assert output_dir is not None, "Workflow should complete successfully"


@pytest.mark.skipif(
    not os.path.exists("data/samples/test.pdf"),
    reason="Test PDF not available"
)
class TestWorkflowRealPDF:
    """Tests with real PDF file."""

    def test_workflow_extracts_realistic_chapters(self):
        """Test that workflow extracts chapters from real test PDF."""
        workflow = PDFSummarizerWorkflow(
            llm_provider="mock",
            enable_checkpoints=False
        )

        from src.models.state import AgentState

        state = AgentState(
            session_id="real_pdf_test",
            pdf_path="data/samples/test.pdf",
            pdf_type=PDFType.LATEX_COMPILED
        )

        state = workflow.chapter_agent.run(state)

        # Verify reasonable chapter extraction
        assert len(state.chapter_collection.chapters) > 0, "Should extract at least one chapter"
        assert len(state.chapter_collection.chapters) <= 10, "Should not create excessive chapters"

        # Verify no page overlaps
        all_pages = []
        for chapter in state.chapter_collection.chapters:
            for page in chapter.pages:
                assert page not in all_pages, f"Page {page} appears in multiple chapters"
                all_pages.append(page)
