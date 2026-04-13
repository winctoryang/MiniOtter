"""macOS accessibility tree extraction via pyobjc."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_accessibility_tree(app_name: str | None = None, max_depth: int = 5) -> str:
    """Get the accessibility tree of the focused or specified application."""
    try:
        import ApplicationServices
        from AppKit import NSWorkspace
    except ImportError:
        return "错误：pyobjc 未安装，无法获取无障碍树"

    try:
        if app_name:
            app = _find_app_by_name(app_name)
        else:
            app = NSWorkspace.sharedWorkspace().frontmostApplication()

        if not app:
            return "错误：未找到应用程序"

        pid = app.processIdentifier()
        app_ref = ApplicationServices.AXUIElementCreateApplication(pid)

        lines: list[str] = [f"应用: {app.localizedName()} (PID: {pid})"]
        _traverse_element(app_ref, depth=0, max_depth=max_depth, lines=lines)
        return "\n".join(lines)
    except Exception as e:
        logger.exception("Failed to get accessibility tree")
        return f"错误：获取无障碍树失败 - {e}"


def _find_app_by_name(name: str):
    from AppKit import NSWorkspace
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.localizedName() and name.lower() in app.localizedName().lower():
            return app
    return None


def _get_attribute(element, attr_name: str):
    import ApplicationServices
    err, value = ApplicationServices.AXUIElementCopyAttributeValue(element, attr_name, None)
    if err == 0:
        return value
    return None


def _traverse_element(element, depth: int, max_depth: int, lines: list[str]) -> None:
    if depth > max_depth:
        return

    indent = "  " * depth
    role = _get_attribute(element, "AXRole") or "Unknown"
    title = _get_attribute(element, "AXTitle") or ""
    value = _get_attribute(element, "AXValue") or ""
    description = _get_attribute(element, "AXDescription") or ""
    position = _get_attribute(element, "AXPosition")
    size = _get_attribute(element, "AXSize")

    parts = [f"{indent}[{role}]"]
    if title:
        parts.append(f'"{title}"')
    if value:
        val_str = str(value)
        if len(val_str) > 100:
            val_str = val_str[:100] + "..."
        parts.append(f"value={val_str!r}")
    if description:
        parts.append(f"desc={description!r}")
    if position and size:
        try:
            parts.append(f"pos=({int(position.x)},{int(position.y)}) size=({int(size.width)},{int(size.height)})")
        except (AttributeError, TypeError):
            pass

    lines.append(" ".join(parts))

    children = _get_attribute(element, "AXChildren")
    if children:
        for child in children:
            _traverse_element(child, depth + 1, max_depth, lines)
