"""
PDF Math Agent - Sistema multi-agente per generare riassunti HTML da PDF matematici.

This package provides a multi-agent system for processing mathematical PDFs
and generating navigable HTML summaries with preserved LaTeX formulas.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from src.utils.config_loader import get_config, get_api_key
from src.utils.logger import get_logger

__all__ = ["get_config", "get_api_key", "get_logger"]
