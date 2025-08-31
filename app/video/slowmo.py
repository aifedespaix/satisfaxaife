"""Utilities to append a slow-motion replay at the end of a video."""

from __future__ import annotations

import subprocess
from pathlib import Path

import imageio_ffmpeg


def append_slowmo_ending(
    path: Path,
    death_ts: float,
    pre_s: float,
    post_s: float,
    slow_factor: float,
    min_start: float = 0.0,
) -> None:
    """Append a slow-motion segment around ``death_ts`` to ``path``.

    The original video remains intact and a replay covering ``pre_s`` seconds before
    ``death_ts`` and ``post_s`` seconds after is extracted, slowed down by
    ``slow_factor`` (``0 < slow_factor <= 1``) and appended to the end of the
    video. Video and audio are processed so that their durations stay aligned.
    Extraction never begins before ``min_start`` so that intro footage is
    preserved.

    Parameters
    ----------
    path:
        Path to the video to post-process. The file must be an ``.mp4`` with an
        audio track.
    death_ts:
        Timestamp of the fatal hit in seconds.
    pre_s:
        Number of seconds to include before ``death_ts``.
    post_s:
        Number of seconds to include after ``death_ts``.
    slow_factor:
        Playback speed for the slow-motion segment. ``0.5`` means half speed.
    min_start:
        Minimum timestamp, in seconds, from which extraction can start. Must be
        non-negative and typically corresponds to the intro duration.
    """
    if slow_factor <= 0:
        msg = "slow_factor must be positive"
        raise ValueError(msg)
    if min_start < 0:
        msg = "min_start must be non-negative"
        raise ValueError(msg)

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    start = max(min_start, death_ts - pre_s)
    end = death_ts + post_s

    slow_segment = path.with_suffix(".slow.mp4")
    original = path.with_suffix(".orig.mp4")
    path.rename(original)

    vf = f"trim=start={start}:end={end},setpts=PTS/{slow_factor}"
    af = f"atrim=start={start}:end={end},asetpts=PTS/{slow_factor},atempo={slow_factor}"
    cmd_segment = [
        ffmpeg,
        "-y",
        "-i",
        str(original),
        "-filter_complex",
        f"[0:v]{vf}[v];[0:a]{af}[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        str(slow_segment),
    ]
    subprocess.run(cmd_segment, check=True, capture_output=True)

    cmd_concat = [
        ffmpeg,
        "-y",
        "-i",
        str(original),
        "-i",
        str(slow_segment),
        "-filter_complex",
        "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        str(path),
    ]
    subprocess.run(cmd_concat, check=True, capture_output=True)

    slow_segment.unlink(missing_ok=True)
    original.unlink(missing_ok=True)
