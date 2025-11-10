"""
Mock LLM responses for testing without API calls.

This module provides realistic mock responses for testing the agent pipeline
without requiring actual API keys or making real LLM calls.
"""

import json
from typing import Dict, Any, Optional


class MockLLMResponse:
    """Generates realistic mock responses based on the agent type and prompt."""

    @staticmethod
    def chapter_agent_toc_response(total_pages: int = 10) -> str:
        """Mock response for chapter extraction with TOC detection."""
        chapters = []
        pages_per_chapter = max(1, total_pages // 3)

        for i in range(3):
            start = i * pages_per_chapter + 1
            end = min(start + pages_per_chapter - 1, total_pages)
            chapters.append({
                "title": f"Chapter {i + 1}",
                "start_page": start,
                "end_page": end
            })

        return json.dumps({"chapters": chapters}, indent=2)

    @staticmethod
    def chapter_agent_heading_response(total_pages: int = 10) -> str:
        """Mock response for chapter extraction via heading detection."""
        return json.dumps({
            "chapters": [
                {
                    "title": "Introduction",
                    "start_page": 1,
                    "end_page": 3
                },
                {
                    "title": "Main Content",
                    "start_page": 4,
                    "end_page": 7
                },
                {
                    "title": "Conclusion",
                    "start_page": 8,
                    "end_page": total_pages
                }
            ]
        }, indent=2)

    @staticmethod
    def chapter_agent_llm_response(total_pages: int = 10) -> str:
        """Mock response for chapter extraction via LLM (returns array directly)."""
        chapters = []
        pages_per_chapter = max(1, total_pages // 3)

        for i in range(min(3, total_pages)):
            start = i * pages_per_chapter + 1
            end = min(start + pages_per_chapter - 1, total_pages)
            if start <= total_pages:
                chapters.append({
                    "title": f"Chapter {i + 1}",
                    "start_page": start,
                    "estimated_pages": end - start + 1
                })

        return json.dumps(chapters, indent=2)

    @staticmethod
    def classifier_agent_response(chapter_content: str) -> str:
        """Mock response for content classification."""
        # Simulate realistic classification
        blocks = []

        # Check for mathematical content
        if "theorem" in chapter_content.lower() or "lemma" in chapter_content.lower():
            blocks.append({
                "type": "theorem",
                "name": "Fundamental Theorem",
                "content": "Let X be a topological space...",
                "action": "verbatim"
            })

        # Check for formulas
        if "$" in chapter_content or "\\(" in chapter_content:
            blocks.append({
                "type": "formula",
                "latex": "x^2 + y^2 = r^2",
                "action": "latex"
            })

        # Add narrative blocks
        blocks.append({
            "type": "narrative",
            "content": "This section introduces the main concepts...",
            "action": "summarize"
        })

        return json.dumps({"blocks": blocks}, indent=2)

    @staticmethod
    def composer_agent_summary(block_content: str, max_words: int = 50) -> str:
        """Mock response for content summarization."""
        return f"Summary of the content (max {max_words} words): " \
               f"The text discusses key mathematical concepts and their applications."


class MockLLMClient:
    """
    Mock LLM client that simulates API responses without making real calls.

    Can be used in tests by setting llm_provider to 'mock' in agent initialization.
    """

    def __init__(self, agent_type: str = "generic"):
        """
        Initialize mock client.

        Args:
            agent_type: Type of agent (chapter_agent, classifier_agent, composer_agent)
        """
        self.agent_type = agent_type
        self.call_count = 0

    def chat_completions_create(
        self,
        messages: list,
        model: str = "mock-model",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> "MockChatCompletion":
        """
        Mock the chat.completions.create() method.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (ignored in mock)
            temperature: Temperature (ignored in mock)
            max_tokens: Max tokens (ignored in mock)

        Returns:
            MockChatCompletion object with mock response
        """
        self.call_count += 1

        # Extract prompt from messages
        prompt = ""
        for msg in messages:
            if msg.get("role") == "user":
                prompt += msg.get("content", "")

        # Generate appropriate response based on agent type and prompt
        response_text = self._generate_response(prompt)

        return MockChatCompletion(response_text)

    def _generate_response(self, prompt: str) -> str:
        """Generate appropriate mock response based on prompt content."""
        prompt_lower = prompt.lower()

        # Chapter Agent responses
        if "table of contents" in prompt_lower or "toc" in prompt_lower:
            return MockLLMResponse.chapter_agent_toc_response()
        elif "content samples" in prompt_lower or "identify logical chapters" in prompt_lower:
            # LLM-based extraction (returns array directly)
            # Try to extract total_pages from prompt
            import re
            match = re.search(r'(\d+)\s+pages', prompt)
            total_pages = int(match.group(1)) if match else 10
            return MockLLMResponse.chapter_agent_llm_response(total_pages)
        elif "headings" in prompt_lower:
            return MockLLMResponse.chapter_agent_heading_response()

        # Classifier Agent responses
        elif "classify" in prompt_lower or "blocks" in prompt_lower:
            return MockLLMResponse.classifier_agent_response(prompt)

        # Composer Agent responses
        elif "summarize" in prompt_lower:
            return MockLLMResponse.composer_agent_summary(prompt)

        # Generic fallback
        else:
            return json.dumps({
                "status": "success",
                "message": "Mock response generated successfully"
            }, indent=2)


class MockChatCompletion:
    """Mock chat completion response object."""

    def __init__(self, content: str):
        self.choices = [MockChoice(content)]
        self.model = "mock-model"
        self.usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }


class MockChoice:
    """Mock choice in chat completion."""

    def __init__(self, content: str):
        self.message = MockMessage(content)
        self.finish_reason = "stop"
        self.index = 0


class MockMessage:
    """Mock message in chat completion choice."""

    def __init__(self, content: str):
        self.content = content
        self.role = "assistant"


def create_mock_llm_client(agent_type: str = "generic") -> MockLLMClient:
    """
    Factory function to create a mock LLM client.

    Usage in tests:
        client = create_mock_llm_client("chapter_agent")
        response = client.chat_completions_create(
            messages=[{"role": "user", "content": "Extract chapters"}],
            model="mock"
        )

    Args:
        agent_type: Type of agent requesting the client

    Returns:
        Configured MockLLMClient instance
    """
    return MockLLMClient(agent_type=agent_type)
