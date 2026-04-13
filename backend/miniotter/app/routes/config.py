"""Configuration routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...config import AppConfig, LLMConfig, save_api_env
from ..deps import get_config
from ..schemas import ConfigUpdate, LLMConfigUpdate

router = APIRouter()


def _llm_to_dict(cfg: LLMConfig) -> dict:
    return {
        "provider": cfg.provider,
        "model": cfg.model,
        "base_url": cfg.base_url,
        "has_key": bool(cfg.api_key),
    }


@router.get("/config")
async def get_configuration(config: AppConfig = Depends(get_config)):
    return {
        "text_llm": _llm_to_dict(config.llm_text),
        "vision_llm": _llm_to_dict(config.llm_vision),
        "agents": {
            "main": {"max_steps": config.main_agent.max_steps},
            "gui": {
                "max_steps": config.gui_agent.max_steps,
                "screenshot_max_width": config.gui_agent.screenshot_max_width,
                "screenshot_max_height": config.gui_agent.screenshot_max_height,
                "include_accessibility_tree": config.gui_agent.include_accessibility_tree,
            },
            "text": {
                "max_steps": config.text_agent.max_steps,
                "bash_timeout": config.text_agent.bash_timeout,
            },
        },
    }


def _apply_llm_update(
    cfg: LLMConfig, update: LLMConfigUpdate, prefix: str, env_data: dict[str, str]
) -> None:
    """更新内存配置并收集需要持久化的字段。"""
    if update.provider is not None:
        cfg.provider = update.provider
        env_data[f"{prefix}_PROVIDER"] = update.provider
    if update.model is not None:
        cfg.model = update.model
        env_data[f"{prefix}_MODEL"] = update.model
    if update.api_key is not None:
        cfg.api_key = update.api_key
        env_data[f"{prefix}_API_KEY"] = update.api_key
    if update.base_url is not None:
        cfg.base_url = update.base_url
        env_data[f"{prefix}_BASE_URL"] = update.base_url


@router.put("/config")
async def update_configuration(update: ConfigUpdate, config: AppConfig = Depends(get_config)):
    env_data: dict[str, str] = {}

    if update.text_llm:
        _apply_llm_update(config.llm_text, update.text_llm, "TEXT_LLM", env_data)
    if update.vision_llm:
        _apply_llm_update(config.llm_vision, update.vision_llm, "VISION_LLM", env_data)

    # 持久化到 .api_env
    if env_data:
        save_api_env(env_data)

    return {"ok": True}
