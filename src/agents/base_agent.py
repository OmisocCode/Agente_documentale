"""
Base agent class for PDF Math Agent.

Provides common functionality for all agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from groq import Groq

from src.models.enums import AgentTask
from src.models.state import AgentState
from src.utils.config_loader import get_api_key, get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents.

    Provides common functionality:
    - LLM client initialization
    - State management
    - Error handling
    - Retry logic
    """

    def __init__(
        self,
        task: AgentTask,
        llm_provider: str = "groq",
        model: Optional[str] = None,
        max_retries: int = 3,
    ):
        """
        Initialize base agent.

        Args:
            task: Task identifier for this agent
            llm_provider: LLM provider (groq, anthropic, openai)
            model: Model name (if None, uses config default)
            max_retries: Maximum retry attempts
        """
        self.task = task
        self.llm_provider = llm_provider
        self.max_retries = max_retries

        # Load config
        self.config = get_config()

        # Get model name
        if model is None:
            # Use task-specific model from config
            task_models = self.config.llm.groq.get("models", {})
            agent_name = self._get_agent_name()
            model = task_models.get(agent_name, self.config.llm.groq["default_model"])

        self.model = model

        # Initialize LLM client
        self._init_llm_client()

        logger.info(
            f"{self.__class__.__name__} initialized with {llm_provider}/{model}"
        )

    def _get_agent_name(self) -> str:
        """Get agent name for config lookup."""
        task_to_agent = {
            AgentTask.TASK_1_CHAPTER: "chapter_agent",
            AgentTask.TASK_2_CLASSIFIER: "classifier_agent",
            AgentTask.TASK_3_COMPOSER: "composer_agent",
        }
        return task_to_agent.get(self.task, "default")

    def _init_llm_client(self) -> None:
        """Initialize LLM client based on provider."""
        if self.llm_provider == "mock":
            # Mock client for testing (no API key required)
            try:
                from tests.mocks.mock_llm import create_mock_llm_client
                agent_name = self._get_agent_name()
                self.client = create_mock_llm_client(agent_type=agent_name)
                logger.debug(f"Mock LLM client initialized for {agent_name}")
            except ImportError:
                logger.warning("Mock LLM client not available, falling back to basic mock")
                self.client = None

        elif self.llm_provider == "groq":
            api_key = get_api_key("groq")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")

            self.client = Groq(api_key=api_key)
            logger.debug("Groq client initialized")

        elif self.llm_provider == "anthropic":
            api_key = get_api_key("anthropic")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")

            from anthropic import Anthropic

            self.client = Anthropic(api_key=api_key)
            logger.debug("Anthropic client initialized")

        elif self.llm_provider == "openai":
            api_key = get_api_key("openai")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")

            from openai import OpenAI

            self.client = OpenAI(api_key=api_key)
            logger.debug("OpenAI client initialized")

        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Call LLM with prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLM response text

        Raises:
            Exception: If LLM call fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                if self.llm_provider == "mock":
                    # Mock LLM response for testing
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})

                    if self.client:
                        response = self.client.chat_completions_create(
                            messages=messages,
                            model=self.model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        return response.choices[0].message.content
                    else:
                        # Fallback mock response
                        return '{"status": "mock", "message": "Mock response"}'

                elif self.llm_provider == "groq":
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})

                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                    return response.choices[0].message.content

                elif self.llm_provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        system=system_prompt or "",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                    return response.content[0].text

                elif self.llm_provider == "openai":
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})

                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                    return response.choices[0].message.content

            except Exception as e:
                logger.warning(
                    f"LLM call failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt == self.max_retries - 1:
                    logger.error("All LLM call attempts failed")
                    raise

                # Exponential backoff
                import time
                time.sleep(2 ** attempt)

        raise Exception("LLM call failed after all retries")

    @abstractmethod
    def execute(self, state: AgentState) -> AgentState:
        """
        Execute agent task.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state

        This method must be implemented by subclasses.
        """
        pass

    def _validate_state(self, state: AgentState) -> None:
        """
        Validate state before execution.

        Args:
            state: State to validate

        Raises:
            ValueError: If state is invalid
        """
        if not state.pdf_path:
            raise ValueError("PDF path is required")

        # Task-specific validation can be added in subclasses

    def run(self, state: AgentState) -> AgentState:
        """
        Run agent with error handling and state management.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        logger.info(f"Starting {self.__class__.__name__} (Task: {self.task.value})")

        try:
            # Validate state
            self._validate_state(state)

            # Mark task as started
            state.start_task(self.task)

            # Execute agent logic
            state = self.execute(state)

            # Validate output
            self._validate_output(state)

            # Mark task as completed
            state.complete_task(self.task)

            logger.info(f"{self.__class__.__name__} completed successfully")

        except Exception as e:
            logger.error(f"{self.__class__.__name__} failed: {e}")
            state.fail_task(self.task, str(e))
            raise

        return state

    def _validate_output(self, state: AgentState) -> None:
        """
        Validate agent output.

        Args:
            state: State to validate

        Raises:
            ValueError: If output is invalid

        This method can be overridden by subclasses for specific validation.
        """
        # Default validation based on task
        if self.task == AgentTask.TASK_1_CHAPTER:
            if not state.validate_task1_output():
                raise ValueError("Invalid Task 1 output: no chapters extracted")

        elif self.task == AgentTask.TASK_2_CLASSIFIER:
            if not state.validate_task2_output():
                raise ValueError("Invalid Task 2 output: no classified blocks")

        elif self.task == AgentTask.TASK_3_COMPOSER:
            if not state.validate_task3_output():
                raise ValueError("Invalid Task 3 output: no HTML files generated")
