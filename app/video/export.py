"""Video export helpers for TikTok-friendly encoding.

This module avoids importing heavy optional dependencies (MoviePy) at import
time to remain usable in constrained environments. If MoviePy is available
at runtime, we use its effects; otherwise, we gracefully fall back to no-op
effects while still performing geometry adjustments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol, runtime_checkable

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


@runtime_checkable
class ClipLike(Protocol):
    """Minimal protocol for a video clip used by export.

    Implemented by MoviePy clips and our test doubles. Kept intentionally
    small to avoid a hard dependency on MoviePy types.
    """

    w: int
    h: int

    def resize(self, size: tuple[int, int], *, method: str = "") -> "ClipLike":
        ...

    def margin(
        self,
        *,
        left: int = 0,
        right: int = 0,
        top: int = 0,
        bottom: int = 0,
        color: tuple[int, int, int] | None = None,
    ) -> "ClipLike":
        ...

    def fx(self, func: object, /, **kwargs: object) -> "ClipLike":
        ...

    def write_videofile(self, out_path: str, **kwargs: object) -> str:
        ...


def _pad_clip(clip: ClipLike) -> ClipLike:
    """Return ``clip`` scaled and padded to 1080×1920 without distortion."""

    scale = min(TARGET_WIDTH / clip.w, TARGET_HEIGHT / clip.h)
    new_w = int(round(clip.w * scale))
    new_h = int(round(clip.h * scale))
    resized = clip.resize((new_w, new_h), method="bicubic")

    pad_left = (TARGET_WIDTH - new_w) // 2
    pad_right = TARGET_WIDTH - new_w - pad_left
    pad_top = (TARGET_HEIGHT - new_h) // 2
    pad_bottom = TARGET_HEIGHT - new_h - pad_top

    return resized.margin(
        left=pad_left,
        right=pad_right,
        top=pad_top,
        bottom=pad_bottom,
        color=(0, 0, 0),
    )


def export_tiktok(
    clip: ClipLike,
    out_path: str,
    fps: int,
    bitrate: str = "15M",
    boost_tiktok: bool = True,
) -> str:
    """Encode ``clip`` with parameters suitable for TikTok."""

    processed = _pad_clip(clip)
    if boost_tiktok:
        # Import MoviePy effects lazily; if unavailable, apply a no-op effect
        # to keep behavior predictable for tests while avoiding hard deps.
        try:
            from moviepy import vfx as _vfx  # type: ignore[import-not-found]

            processed = processed.fx(_vfx.lum_contrast, contrast=1.03)
        except Exception:
            # No-op function to preserve the fx call without changing content
            def _noop(c: object, **_: object) -> object:  # pragma: no cover - trivial
                return c

            processed = processed.fx(_noop, contrast=1.03)

    ffmpeg_params = [
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-profile:v",
        "high",
        "-level",
        "4.1",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        "-color_range",
        "tv",
    ]
    if boost_tiktok:
        ffmpeg_params.extend(["-vf", "hue=s=1.05"])

    processed.write_videofile(
        out_path,
        codec="libx264",
        audio_codec="aac",
        bitrate=bitrate,
        fps=fps,
        audio_bitrate="320k",
        audio_fps=48_000,
        threads=os.cpu_count(),
        ffmpeg_params=ffmpeg_params,
    )
    return str(Path(out_path))


__all__ = ["export_tiktok"]
