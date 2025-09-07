from __future__ import annotations

from pathlib import Path

import pytest

from app.video.slowmo import append_slowmo_ending


def test_append_slowmo_ending_missing_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """append_slowmo_ending raises FileNotFoundError for an unknown path."""
    path = tmp_path / "missing.mp4"
    monkeypatch.setattr(
        "app.video.slowmo.subprocess.run",
        lambda *a, **k: pytest.fail("subprocess.run should not be called"),
    )
    with pytest.raises(FileNotFoundError, match="Video file not found"):
        append_slowmo_ending(
            path=path,
            death_ts=1.0,
            pre_s=0.5,
            post_s=0.5,
            slow_factor=0.5,
        )
