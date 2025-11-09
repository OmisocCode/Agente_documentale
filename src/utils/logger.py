"""
Logging utility for PDF Math Agent.
Provides structured, colorized logging with file and console output.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


class Logger:
    """Centralized logger with file and console handlers."""

    _instances = {}

    @classmethod
    def get_logger(
        cls,
        name: str,
        level: str = "INFO",
        log_file: Optional[str] = None,
        console_output: bool = True,
        colorize: bool = True,
    ) -> logging.Logger:
        """
        Get or create a logger instance.

        Args:
            name: Logger name (usually __name__)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            console_output: Enable console output
            colorize: Colorize console output (uses Rich)

        Returns:
            Configured logger instance
        """
        # Return existing logger if already created
        if name in cls._instances:
            return cls._instances[name]

        # Create new logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        logger.handlers.clear()  # Clear any existing handlers

        # Console handler with Rich formatting
        if console_output:
            if colorize:
                console = Console(stderr=True)
                console_handler = RichHandler(
                    console=console,
                    rich_tracebacks=True,
                    tracebacks_show_locals=True,
                    markup=True,
                )
                console_handler.setFormatter(logging.Formatter("%(message)s"))
            else:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                    )
                )
            logger.addHandler(console_handler)

        # File handler with rotation
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            logger.addHandler(file_handler)

        # Prevent duplicate logs
        logger.propagate = False

        # Cache logger instance
        cls._instances[name] = logger

        return logger


def setup_logging(config: dict) -> None:
    """
    Setup logging based on configuration.

    Args:
        config: Configuration dictionary with logging settings
    """
    log_config = config.get("logging", {})

    # Extract settings
    level = log_config.get("level", "INFO")
    console_config = log_config.get("console", {})
    file_config = log_config.get("file", {})

    # Setup root logger
    root_logger = Logger.get_logger(
        "pdf_math_agent",
        level=level,
        log_file=file_config.get("path") if file_config.get("enabled") else None,
        console_output=console_config.get("enabled", True),
        colorize=console_config.get("colorize", True),
    )

    root_logger.info(f"Logging initialized at {level} level")


# Convenience function for getting module loggers
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Usually __name__ of the module

    Returns:
        Logger instance

    Example:
        >>> from src.utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    # Use environment variable or default level
    level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "logs/pdf_math_agent.log")

    return Logger.get_logger(
        name,
        level=level,
        log_file=log_file if os.getenv("LOG_TO_FILE", "true").lower() == "true" else None,
        console_output=True,
        colorize=True,
    )
