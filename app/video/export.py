"""Video export helpers for TikTok-friendly encoding."""

from __future__ import annotations

import os
from pathlib import Path

from moviepy import vfx
from moviepy.video.VideoClip import VideoClip

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920


def _pad_clip(clip: VideoClip) -> VideoClip:
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
    clip: VideoClip,
    out_path: str,
    fps: int,
    bitrate: str = "15M",
    boost_tiktok: bool = True,
) -> str:
    """Encode ``clip`` with parameters suitable for TikTok."""

    processed = _pad_clip(clip)
    if boost_tiktok:
        processed = processed.fx(vfx.lum_contrast, contrast=1.03)

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
