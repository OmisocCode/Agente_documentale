"""
Agent modules for PDF processing pipeline.

Contains the three main agents:
- ChapterAgent: Divides PDF into logical chapters
- ClassifierAgent: Classifies content blocks
- ComposerAgent: Generates HTML output
"""

from src.agents.base_agent import BaseAgent
from src.agents.chapter_agent import ChapterAgent
from src.agents.classifier_agent import ClassifierAgent
from src.agents.composer_agent import ComposerAgent

__all__ = [
    "BaseAgent",
    "ChapterAgent",
    "ClassifierAgent",
    "ComposerAgent",
]
