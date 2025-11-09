"""
Configuration loader for PDF Math Agent.
Loads configuration from YAML file and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    primary_provider: str = "groq"
    groq: Dict[str, Any] = Field(default_factory=dict)
    anthropic: Dict[str, Any] = Field(default_factory=dict)
    openai: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Agent-specific configuration."""

    chapter_agent: Dict[str, Any] = Field(default_factory=dict)
    classifier_agent: Dict[str, Any] = Field(default_factory=dict)
    composer_agent: Dict[str, Any] = Field(default_factory=dict)


class PDFConfig(BaseModel):
    """PDF processing configuration."""

    auto_detect_type: bool = True
    tools: Dict[str, str] = Field(default_factory=dict)
    ocr: Dict[str, Any] = Field(default_factory=dict)
    latex: Dict[str, Any] = Field(default_factory=dict)


class Config(BaseModel):
    """Main configuration model."""

    llm: LLMConfig
    agents: AgentConfig
    pdf: PDFConfig
    templates: Dict[str, Any] = Field(default_factory=dict)
    checkpoints: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    logging: Dict[str, Any] = Field(default_factory=dict)
    performance: Dict[str, Any] = Field(default_factory=dict)
    error_handling: Dict[str, Any] = Field(default_factory=dict)
    development: Dict[str, Any] = Field(default_factory=dict)


class ConfigLoader:
    """Load and manage application configuration."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to config.yaml file. If None, uses default location.
        """
        # Load environment variables
        load_dotenv()

        # Determine config path
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "config.yaml")

        self.config_path = Path(config_path)
        self._raw_config: Dict[str, Any] = {}
        self.config: Optional[Config] = None

    def load(self) -> Config:
        """
        Load configuration from file and environment variables.

        Returns:
            Validated configuration object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If configuration is invalid
        """
        # Load YAML configuration
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._raw_config = yaml.safe_load(f)

        # Override with environment variables
        self._apply_env_overrides()

        # Validate and create config object
        try:
            self.config = Config(**self._raw_config)
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}")

        return self.config

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # LLM provider override
        if provider := os.getenv("LLM_PROVIDER"):
            self._raw_config["llm"]["primary_provider"] = provider

        # Groq model override
        if groq_model := os.getenv("GROQ_MODEL"):
            if "groq" not in self._raw_config["llm"]:
                self._raw_config["llm"]["groq"] = {}
            self._raw_config["llm"]["groq"]["default_model"] = groq_model

        # Path overrides
        if output_dir := os.getenv("OUTPUT_DIR"):
            self._raw_config["output"]["base_dir"] = output_dir

        if checkpoint_dir := os.getenv("CHECKPOINT_DIR"):
            self._raw_config["checkpoints"]["save_dir"] = checkpoint_dir

        if cache_dir := os.getenv("CACHE_DIR"):
            self._raw_config["performance"]["cache"]["dir"] = cache_dir

        # Logging overrides
        if log_level := os.getenv("LOG_LEVEL"):
            self._raw_config["logging"]["level"] = log_level

        if log_file := os.getenv("LOG_FILE"):
            self._raw_config["logging"]["file"]["path"] = log_file

        # Debug/verbose overrides
        if debug := os.getenv("DEBUG"):
            self._raw_config["development"]["debug"] = debug.lower() == "true"

        if verbose := os.getenv("VERBOSE"):
            self._raw_config["development"]["verbose"] = verbose.lower() == "true"

        # Performance overrides
        if enable_cache := os.getenv("ENABLE_CACHE"):
            self._raw_config["performance"]["cache"]["enabled"] = (
                enable_cache.lower() == "true"
            )

        if max_retries := os.getenv("MAX_RETRIES"):
            self._raw_config["error_handling"]["max_retries"] = int(max_retries)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., "llm.groq.default_model")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> config_loader = ConfigLoader()
            >>> config_loader.load()
            >>> model = config_loader.get("llm.groq.default_model")
        """
        if self.config is None:
            raise RuntimeError("Configuration not loaded. Call load() first.")

        keys = key.split(".")
        value = self._raw_config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for specified provider.

        Args:
            provider: Provider name (groq, anthropic, openai)

        Returns:
            API key or None if not found

        Example:
            >>> config_loader = ConfigLoader()
            >>> groq_key = config_loader.get_api_key("groq")
        """
        env_var = f"{provider.upper()}_API_KEY"
        return os.getenv(env_var)


# Global config instance
_config_loader: Optional[ConfigLoader] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get global configuration instance.

    Args:
        config_path: Path to config file (only used on first call)

    Returns:
        Configuration object

    Example:
        >>> from src.utils.config_loader import get_config
        >>> config = get_config()
        >>> print(config.llm.primary_provider)
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = ConfigLoader(config_path)
        _config_loader.load()

    return _config_loader.config


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for provider.

    Args:
        provider: Provider name (groq, anthropic, openai)

    Returns:
        API key or None

    Example:
        >>> from src.utils.config_loader import get_api_key
        >>> groq_key = get_api_key("groq")
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = ConfigLoader()
        _config_loader.load()

    return _config_loader.get_api_key(provider)
