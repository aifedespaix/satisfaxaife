from __future__ import annotations

from pathlib import Path

import imageio
import numpy as np
from pytest import CaptureFixture

from app.video.recorder import Recorder


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
