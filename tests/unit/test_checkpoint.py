"""
Unit tests for checkpoint manager.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.models.enums import AgentTask, PDFType
from src.models.state import AgentState
from src.utils.checkpoint_manager import CheckpointManager


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    @pytest.fixture
    def temp_checkpoint_dir(self):
        """Create temporary checkpoint directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager(self, temp_checkpoint_dir):
        """Create CheckpointManager instance."""
        return CheckpointManager(checkpoint_dir=temp_checkpoint_dir)

    @pytest.fixture
    def sample_state(self):
        """Create sample AgentState."""
        return AgentState(
            session_id="test_session_123",
            pdf_path="test.pdf",
            pdf_type=PDFType.LATEX_COMPILED,
        )

    def test_save_checkpoint(self, manager, sample_state):
        """Test saving a checkpoint."""
        checkpoint_path = manager.save(sample_state, AgentTask.TASK_1_CHAPTER)

        assert checkpoint_path.exists()
        assert "test_session_123" in str(checkpoint_path)
        assert "task1" in str(checkpoint_path)

    def test_save_and_load_checkpoint(self, manager, sample_state):
        """Test saving and loading a checkpoint."""
        # Save
        manager.save(sample_state, AgentTask.TASK_1_CHAPTER)

        # Load
        loaded_state = manager.load("test_session_123", AgentTask.TASK_1_CHAPTER)

        assert loaded_state is not None
        assert loaded_state.session_id == sample_state.session_id
        assert loaded_state.pdf_path == sample_state.pdf_path
        assert loaded_state.pdf_type == sample_state.pdf_type

    def test_load_nonexistent_checkpoint(self, manager):
        """Test loading a checkpoint that doesn't exist."""
        state = manager.load("nonexistent_session", AgentTask.TASK_1_CHAPTER)
        assert state is None

    def test_load_latest(self, manager, sample_state):
        """Test loading latest checkpoint."""
        # Save checkpoint
        manager.save(sample_state, AgentTask.TASK_1_CHAPTER)

        # Load latest
        loaded_state = manager.load_latest("test_session_123")

        assert loaded_state is not None
        assert loaded_state.session_id == "test_session_123"

    def test_list_checkpoints(self, manager, sample_state):
        """Test listing checkpoints."""
        # Create multiple checkpoints
        manager.save(sample_state, AgentTask.TASK_1_CHAPTER)
        sample_state.start_task(AgentTask.TASK_1_CHAPTER)
        sample_state.complete_task(AgentTask.TASK_1_CHAPTER)
        manager.save(sample_state, AgentTask.TASK_2_CLASSIFIER)

        # List all checkpoints
        checkpoints = manager.list_checkpoints()

        assert len(checkpoints) >= 2  # At least Task 1 and Task 2 checkpoints

        # List for specific session
        session_checkpoints = manager.list_checkpoints("test_session_123")
        assert len(session_checkpoints) >= 2

    def test_delete_checkpoint(self, manager, sample_state):
        """Test deleting a checkpoint."""
        # Save checkpoint
        manager.save(sample_state, AgentTask.TASK_1_CHAPTER)

        # Verify it exists
        assert manager.load("test_session_123", AgentTask.TASK_1_CHAPTER) is not None

        # Delete it
        success = manager.delete_checkpoint("test_session_123", AgentTask.TASK_1_CHAPTER)
        assert success is True

        # Verify it's gone
        assert manager.load("test_session_123", AgentTask.TASK_1_CHAPTER) is None

    def test_delete_session(self, manager, sample_state):
        """Test deleting all checkpoints for a session."""
        # Create multiple checkpoints
        manager.save(sample_state, AgentTask.TASK_1_CHAPTER)
        manager.save(sample_state, AgentTask.TASK_2_CLASSIFIER)

        # Delete entire session
        deleted_count = manager.delete_session("test_session_123")

        assert deleted_count >= 2

        # Verify all gone
        checkpoints = manager.list_checkpoints("test_session_123")
        assert len(checkpoints) == 0

    def test_auto_recover(self, manager, sample_state):
        """Test auto-recovery from latest checkpoint."""
        # Complete Task 1
        sample_state.start_task(AgentTask.TASK_1_CHAPTER)
        sample_state.complete_task(AgentTask.TASK_1_CHAPTER)
        manager.save(sample_state, AgentTask.TASK_1_CHAPTER)

        # Complete Task 2
        sample_state.start_task(AgentTask.TASK_2_CLASSIFIER)
        sample_state.complete_task(AgentTask.TASK_2_CLASSIFIER)
        manager.save(sample_state, AgentTask.TASK_2_CLASSIFIER)

        # Auto-recover should load Task 2 (most recent completed)
        recovered = manager.auto_recover("test_session_123")

        assert recovered is not None
        assert recovered.is_task_completed(AgentTask.TASK_1_CHAPTER)
        assert recovered.is_task_completed(AgentTask.TASK_2_CLASSIFIER)

    def test_checkpoint_with_metadata(self, manager, sample_state):
        """Test saving checkpoint with custom metadata."""
        metadata = {"custom_field": "custom_value", "priority": "high"}

        manager.save(sample_state, AgentTask.TASK_1_CHAPTER, metadata=metadata)

        # Verify checkpoint was saved
        checkpoints = manager.list_checkpoints("test_session_123")
        assert len(checkpoints) > 0
