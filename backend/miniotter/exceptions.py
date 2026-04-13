"""Custom exceptions."""


class MiniOtterError(Exception):
    """Base exception."""


class LLMError(MiniOtterError):
    """LLM provider error."""


class ToolExecutionError(MiniOtterError):
    """Tool execution failed."""


class AgentError(MiniOtterError):
    """Agent execution error."""


class ConfigError(MiniOtterError):
    """Configuration error."""


class TaskCancelledError(MiniOtterError):
    """Task was cancelled by user."""
