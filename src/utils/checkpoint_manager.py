"""
Checkpoint manager for saving and loading workflow state.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import ValidationError

from src.models.enums import AgentTask
from src.models.state import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CheckpointManager:
    """
    Manages saving and loading of workflow checkpoints.

    Supports JSON format for human-readable checkpoints with easy recovery.
    """

    def __init__(self, checkpoint_dir: str = "checkpoints"):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Checkpoint manager initialized: {self.checkpoint_dir}")

    def _get_checkpoint_path(
        self, session_id: str, task: Optional[AgentTask] = None
    ) -> Path:
        """
        Get checkpoint file path.

        Args:
            session_id: Session identifier
            task: Optional task identifier for task-specific checkpoints

        Returns:
            Path to checkpoint file
        """
        if task:
            filename = f"{session_id}_{task.value}.json"
        else:
            filename = f"{session_id}_latest.json"

        return self.checkpoint_dir / filename

    def save(
        self, state: AgentState, task: Optional[AgentTask] = None, metadata: dict = None
    ) -> Path:
        """
        Save workflow state to checkpoint.

        Args:
            state: AgentState to save
            task: Optional task identifier
            metadata: Optional additional metadata

        Returns:
            Path to saved checkpoint file

        Example:
            >>> manager = CheckpointManager()
            >>> checkpoint_path = manager.save(state, AgentTask.TASK_1_CHAPTER)
        """
        checkpoint_path = self._get_checkpoint_path(state.session_id, task)

        try:
            # Convert state to dict
            state_dict = state.model_dump(mode="json")

            # Add checkpoint metadata
            checkpoint_data = {
                "checkpoint_metadata": {
                    "saved_at": datetime.now().isoformat(),
                    "task": task.value if task else None,
                    "session_id": state.session_id,
                    "version": "1.0",
                    **(metadata or {}),
                },
                "state": state_dict,
            }

            # Save to JSON
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Checkpoint saved: {checkpoint_path}")

            # Also save as "latest" for easy recovery
            latest_path = self._get_checkpoint_path(state.session_id)
            with open(latest_path, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

            return checkpoint_path

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            raise

    def load(
        self, session_id: str, task: Optional[AgentTask] = None
    ) -> Optional[AgentState]:
        """
        Load workflow state from checkpoint.

        Args:
            session_id: Session identifier
            task: Optional task identifier to load specific checkpoint

        Returns:
            AgentState or None if not found

        Example:
            >>> manager = CheckpointManager()
            >>> state = manager.load("20240109_143022_abc123", AgentTask.TASK_1_CHAPTER)
        """
        checkpoint_path = self._get_checkpoint_path(session_id, task)

        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return None

        try:
            # Load JSON
            with open(checkpoint_path, "r", encoding="utf-8") as f:
                checkpoint_data = json.load(f)

            # Extract state
            state_dict = checkpoint_data.get("state", {})

            # Reconstruct AgentState
            state = AgentState(**state_dict)

            logger.info(f"Checkpoint loaded: {checkpoint_path}")
            logger.info(f"State summary: {state.get_summary()}")

            return state

        except ValidationError as e:
            logger.error(f"Invalid checkpoint data: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def load_latest(self, session_id: str) -> Optional[AgentState]:
        """
        Load latest checkpoint for a session.

        Args:
            session_id: Session identifier

        Returns:
            AgentState or None if not found
        """
        return self.load(session_id, task=None)

    def list_checkpoints(self, session_id: Optional[str] = None) -> List[dict]:
        """
        List available checkpoints.

        Args:
            session_id: Optional session ID to filter by

        Returns:
            List of checkpoint info dictionaries

        Example:
            >>> manager = CheckpointManager()
            >>> checkpoints = manager.list_checkpoints()
            >>> for cp in checkpoints:
            ...     print(f"{cp['session_id']} - {cp['task']} - {cp['saved_at']}")
        """
        checkpoints = []

        pattern = f"{session_id}_*.json" if session_id else "*.json"

        for checkpoint_file in self.checkpoint_dir.glob(pattern):
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("checkpoint_metadata", {})

                checkpoints.append(
                    {
                        "file": str(checkpoint_file),
                        "session_id": metadata.get("session_id"),
                        "task": metadata.get("task"),
                        "saved_at": metadata.get("saved_at"),
                        "version": metadata.get("version", "unknown"),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to read checkpoint {checkpoint_file}: {e}")

        # Sort by save time (newest first)
        checkpoints.sort(key=lambda x: x.get("saved_at", ""), reverse=True)

        return checkpoints

    def delete_checkpoint(
        self, session_id: str, task: Optional[AgentTask] = None
    ) -> bool:
        """
        Delete a checkpoint.

        Args:
            session_id: Session identifier
            task: Optional task identifier

        Returns:
            True if deleted successfully
        """
        checkpoint_path = self._get_checkpoint_path(session_id, task)

        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return False

        try:
            checkpoint_path.unlink()
            logger.info(f"Checkpoint deleted: {checkpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False

    def delete_session(self, session_id: str) -> int:
        """
        Delete all checkpoints for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of checkpoints deleted
        """
        deleted_count = 0

        for checkpoint_file in self.checkpoint_dir.glob(f"{session_id}_*.json"):
            try:
                checkpoint_file.unlink()
                deleted_count += 1
                logger.info(f"Deleted checkpoint: {checkpoint_file}")
            except Exception as e:
                logger.warning(f"Failed to delete {checkpoint_file}: {e}")

        logger.info(f"Deleted {deleted_count} checkpoints for session {session_id}")
        return deleted_count

    def auto_recover(self, session_id: str) -> Optional[AgentState]:
        """
        Auto-recover from the latest successful checkpoint.

        Attempts to load checkpoints in reverse order (Task 3 -> Task 2 -> Task 1).

        Args:
            session_id: Session identifier

        Returns:
            Latest valid AgentState or None
        """
        logger.info(f"Attempting auto-recovery for session {session_id}")

        # Try loading in reverse task order
        tasks = [AgentTask.TASK_3_COMPOSER, AgentTask.TASK_2_CLASSIFIER, AgentTask.TASK_1_CHAPTER]

        for task in tasks:
            state = self.load(session_id, task)
            if state and state.is_task_completed(task):
                logger.info(f"Recovered from {task.value} checkpoint")
                return state

        # Try latest
        state = self.load_latest(session_id)
        if state:
            logger.info("Recovered from latest checkpoint")
            return state

        logger.warning(f"No valid checkpoint found for session {session_id}")
        return None

    def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """
        Clean up checkpoints older than specified days.

        Args:
            days: Delete checkpoints older than this many days

        Returns:
            Number of checkpoints deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                saved_at_str = data.get("checkpoint_metadata", {}).get("saved_at")
                if saved_at_str:
                    saved_at = datetime.fromisoformat(saved_at_str)
                    if saved_at < cutoff_date:
                        checkpoint_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old checkpoint: {checkpoint_file}")
            except Exception as e:
                logger.warning(f"Error processing {checkpoint_file}: {e}")

        logger.info(f"Cleaned up {deleted_count} old checkpoints (older than {days} days)")
        return deleted_count


# Global checkpoint manager instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager(checkpoint_dir: str = "checkpoints") -> CheckpointManager:
    """
    Get global checkpoint manager instance.

    Args:
        checkpoint_dir: Directory for checkpoints (only used on first call)

    Returns:
        CheckpointManager instance

    Example:
        >>> from src.utils.checkpoint_manager import get_checkpoint_manager
        >>> manager = get_checkpoint_manager()
        >>> manager.save(state, AgentTask.TASK_1_CHAPTER)
    """
    global _checkpoint_manager

    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager(checkpoint_dir)

    return _checkpoint_manager
