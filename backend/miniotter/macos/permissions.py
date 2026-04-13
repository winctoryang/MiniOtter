"""Check macOS accessibility permissions."""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


def check_accessibility_permission() -> bool:
    try:
        import ApplicationServices
        trusted = ApplicationServices.AXIsProcessTrusted()
        if not trusted:
            logger.warning("辅助功能权限未授予。请在 系统偏好设置 > 隐私与安全性 > 辅助功能 中添加本应用。")
        return bool(trusted)
    except ImportError:
        logger.warning("pyobjc-framework-ApplicationServices 未安装，无法检查辅助功能权限")
        return False


def check_screen_recording_permission() -> bool:
    try:
        result = subprocess.run(["screencapture", "-x", "-t", "png", "/dev/null"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False
