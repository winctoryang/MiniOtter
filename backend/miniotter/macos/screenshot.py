"""macOS screenshot capture."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import tempfile
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


async def take_screenshot_native(
    max_width: int = 1280,
    max_height: int = 800,
    region: tuple[int, int, int, int] | None = None,
) -> str:
    """Capture screenshot using macOS native screencapture. Returns base64 PNG."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    cmd = ["screencapture", "-x", "-C"]
    if region:
        x, y, w, h = region
        cmd.extend(["-R", f"{x},{y},{w},{h}"])
    cmd.append(tmp_path)

    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.wait()

    try:
        img_bytes = Path(tmp_path).read_bytes()
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    resized = _resize_for_llm(img_bytes, max_width, max_height)
    return base64.b64encode(resized).decode()


def get_screen_scale_factor() -> float:
    try:
        from AppKit import NSScreen
        return NSScreen.mainScreen().backingScaleFactor()
    except ImportError:
        return 2.0


def get_screen_size() -> tuple[int, int]:
    try:
        from AppKit import NSScreen
        frame = NSScreen.mainScreen().frame()
        return int(frame.size.width), int(frame.size.height)
    except ImportError:
        return 1440, 900


def map_coordinates(llm_x: int, llm_y: int, image_width: int, image_height: int) -> tuple[int, int]:
    screen_w, screen_h = get_screen_size()
    return int(llm_x * screen_w / image_width), int(llm_y * screen_h / image_height)


def _resize_for_llm(img_bytes: bytes, max_width: int, max_height: int) -> bytes:
    img = Image.open(io.BytesIO(img_bytes))
    orig_w, orig_h = img.size
    scale = min(max_width / orig_w, max_height / orig_h, 1.0)
    if scale < 1.0:
        img = img.resize((int(orig_w * scale), int(orig_h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
