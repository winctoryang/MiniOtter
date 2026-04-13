"""Chinese system prompts for all agents."""

from .gui_agent import GUI_AGENT_SYSTEM_PROMPT
from .main_agent import MAIN_AGENT_SYSTEM_PROMPT
from .text_agent import TEXT_AGENT_SYSTEM_PROMPT
from .extension_agent import EXTENSION_AGENT_SYSTEM_PROMPT

__all__ = ["MAIN_AGENT_SYSTEM_PROMPT", "GUI_AGENT_SYSTEM_PROMPT", "TEXT_AGENT_SYSTEM_PROMPT", "EXTENSION_AGENT_SYSTEM_PROMPT"]
