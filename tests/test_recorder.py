from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from pytest import CaptureFixture, LogCaptureFixture

import imageio
from app.video.recorder import NullRecorder, Recorder


def test_recorder_preserves_dimensions(tmp_path: Path, capfd: CaptureFixture[str]) -> None:
    width, height = 100, 58
    recorder = Recorder(width, height, 30, tmp_path / "out.mp4")
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    recorder.add_frame(frame)
    recorder.close()
    err = capfd.readouterr().err
    assert "WARNING" not in err
    with imageio.get_reader(tmp_path / "out.mp4") as reader:
        out_frame = reader.get_data(0)
    assert out_frame.shape == (height, width, 3)


def test_null_recorder_path_is_none() -> None:
    """NullRecorder exposes a path attribute set to ``None``."""
    recorder = NullRecorder()
    assert recorder.path is None


def test_recorder_logs_each_second(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    width, height, fps = 10, 10, 5
    recorder = Recorder(width, height, fps, tmp_path / "out.mp4")
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    with caplog.at_level(logging.DEBUG, logger="app.video.recorder"):
        for _ in range(fps * 3):
            recorder.add_frame(frame)
    recorder.close()
    messages = [r.message for r in caplog.records if r.name == "app.video.recorder"]
    assert messages == [
        "Recorded 1 second(s) of video",
        "Recorded 2 second(s) of video",
        "Recorded 3 second(s) of video",
    ]
