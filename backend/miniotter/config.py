"""Configuration loading and management."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .constants import (
    DEFAULT_A11Y_MAX_DEPTH,
    DEFAULT_BASH_TIMEOUT,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_TEMPERATURE,
    DEFAULT_MAX_STEPS_GUI,
    DEFAULT_MAX_STEPS_MAIN,
    DEFAULT_MAX_STEPS_TEXT,
    DEFAULT_SCREENSHOT_MAX_HEIGHT,
    DEFAULT_SCREENSHOT_MAX_WIDTH,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
)

# .api_env 文件路径（项目根目录）
# __file__ = backend/miniotter/config.py → .parent×3 = 项目根目录
_API_ENV_PATH = Path(__file__).parent.parent.parent / ".api_env"


@dataclass
class LLMConfig:
    provider: str = "claude"
    model: str = "claude-sonnet-4-20250514"
    api_key: str = ""
    base_url: str | None = None
    max_tokens: int = DEFAULT_LLM_MAX_TOKENS
    temperature: float = DEFAULT_LLM_TEMPERATURE


@dataclass
class MainAgentConfig:
    max_steps: int = DEFAULT_MAX_STEPS_MAIN


@dataclass
class GUIAgentConfig:
    max_steps: int = DEFAULT_MAX_STEPS_GUI
    screenshot_max_width: int = DEFAULT_SCREENSHOT_MAX_WIDTH
    screenshot_max_height: int = DEFAULT_SCREENSHOT_MAX_HEIGHT
    include_accessibility_tree: bool = True
    a11y_max_depth: int = DEFAULT_A11Y_MAX_DEPTH


@dataclass
class TextAgentConfig:
    max_steps: int = DEFAULT_MAX_STEPS_TEXT
    bash_timeout: int = DEFAULT_BASH_TIMEOUT


@dataclass
class ServerConfig:
    host: str = DEFAULT_SERVER_HOST
    port: int = DEFAULT_SERVER_PORT
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173"])


@dataclass
class AppConfig:
    server: ServerConfig = field(default_factory=ServerConfig)
    llm_text: LLMConfig = field(default_factory=lambda: LLMConfig(
        provider="openai", model="gpt-4o",
    ))
    llm_vision: LLMConfig = field(default_factory=lambda: LLMConfig(
        provider="claude", model="claude-sonnet-4-20250514",
    ))
    main_agent: MainAgentConfig = field(default_factory=MainAgentConfig)
    gui_agent: GUIAgentConfig = field(default_factory=GUIAgentConfig)
    text_agent: TextAgentConfig = field(default_factory=TextAgentConfig)

    def get_llm_config(self, agent_type: str) -> LLMConfig:
        """文本LLM用于主Agent和文本Agent，视觉LLM用于GUI Agent。"""
        if agent_type == "gui":
            return self.llm_vision
        return self.llm_text


# ── .api_env 读写 ──────────────────────────────────────────────


def _load_api_env() -> dict[str, str]:
    """从 .api_env 文件加载 key=value 对。"""
    env: dict[str, str] = {}
    if not _API_ENV_PATH.exists():
        return env
    for line in _API_ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def save_api_env(data: dict[str, str]) -> None:
    """将 key=value 对写入 .api_env，合并已有内容。"""
    existing = _load_api_env()
    existing.update(data)
    lines = [f"{k}={v}" for k, v in sorted(existing.items()) if v]
    _API_ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── YAML / env 解析 ───────────────────────────────────────────


def _resolve_env_vars(value: str) -> str:
    """Replace ${VAR} with environment variable values."""
    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, "")
    return re.sub(r"\$\{(\w+)}", replacer, value)


def _parse_llm_config(data: dict) -> LLMConfig:
    cfg = LLMConfig()
    if "provider" in data:
        cfg.provider = data["provider"]
    if "model" in data:
        cfg.model = data["model"]
    if "api_key" in data:
        cfg.api_key = _resolve_env_vars(data["api_key"])
    if "base_url" in data:
        cfg.base_url = data["base_url"]
    if "max_tokens" in data:
        cfg.max_tokens = data["max_tokens"]
    if "temperature" in data:
        cfg.temperature = data["temperature"]
    return cfg


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load configuration from YAML + .api_env."""
    config = AppConfig()

    # ── 1. 读 YAML ──
    paths_to_try = []
    if config_path:
        paths_to_try.append(Path(config_path))
    paths_to_try.extend([
        Path("config/default_config.yaml"),
        Path(__file__).parent.parent / "config" / "default_config.yaml",
        Path.home() / ".miniotter" / "config.yaml",
    ])

    data: dict = {}
    for p in paths_to_try:
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f) or {}
            break

    # Server
    if "server" in data:
        s = data["server"]
        config.server = ServerConfig(
            host=s.get("host", DEFAULT_SERVER_HOST),
            port=s.get("port", DEFAULT_SERVER_PORT),
            cors_origins=s.get("cors_origins", ["http://localhost:5173"]),
        )

    # LLM configs from YAML
    llm_data = data.get("llm", {})
    if "text" in llm_data:
        config.llm_text = _parse_llm_config(llm_data["text"])
    if "vision" in llm_data:
        config.llm_vision = _parse_llm_config(llm_data["vision"])

    # ── 2. 读 .api_env（覆盖 YAML 中的 key）──
    api_env = _load_api_env()

    if api_env.get("TEXT_LLM_API_KEY"):
        config.llm_text.api_key = api_env["TEXT_LLM_API_KEY"]
    if api_env.get("TEXT_LLM_PROVIDER"):
        config.llm_text.provider = api_env["TEXT_LLM_PROVIDER"]
    if api_env.get("TEXT_LLM_MODEL"):
        config.llm_text.model = api_env["TEXT_LLM_MODEL"]
    if api_env.get("TEXT_LLM_BASE_URL"):
        config.llm_text.base_url = api_env["TEXT_LLM_BASE_URL"]

    if api_env.get("VISION_LLM_API_KEY"):
        config.llm_vision.api_key = api_env["VISION_LLM_API_KEY"]
    if api_env.get("VISION_LLM_PROVIDER"):
        config.llm_vision.provider = api_env["VISION_LLM_PROVIDER"]
    if api_env.get("VISION_LLM_MODEL"):
        config.llm_vision.model = api_env["VISION_LLM_MODEL"]
    if api_env.get("VISION_LLM_BASE_URL"):
        config.llm_vision.base_url = api_env["VISION_LLM_BASE_URL"]

    # Agent configs
    agents_data = data.get("agents", {})
    if "main" in agents_data:
        config.main_agent = MainAgentConfig(
            max_steps=agents_data["main"].get("max_steps", DEFAULT_MAX_STEPS_MAIN),
        )
    if "gui" in agents_data:
        g = agents_data["gui"]
        config.gui_agent = GUIAgentConfig(
            max_steps=g.get("max_steps", DEFAULT_MAX_STEPS_GUI),
            screenshot_max_width=g.get("screenshot_max_width", DEFAULT_SCREENSHOT_MAX_WIDTH),
            screenshot_max_height=g.get("screenshot_max_height", DEFAULT_SCREENSHOT_MAX_HEIGHT),
            include_accessibility_tree=g.get("include_accessibility_tree", True),
            a11y_max_depth=g.get("a11y_max_depth", DEFAULT_A11Y_MAX_DEPTH),
        )
    if "text" in agents_data:
        t = agents_data["text"]
        config.text_agent = TextAgentConfig(
            max_steps=t.get("max_steps", DEFAULT_MAX_STEPS_TEXT),
            bash_timeout=t.get("bash_timeout", DEFAULT_BASH_TIMEOUT),
        )

    # Env var overrides for server
    if host := os.environ.get("MINIOTTER_HOST"):
        config.server.host = host
    if port := os.environ.get("MINIOTTER_PORT"):
        config.server.port = int(port)

    return config
