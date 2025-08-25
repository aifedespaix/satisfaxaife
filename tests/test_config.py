from __future__ import annotations

import json
from pathlib import Path

from app.core import config


def test_load_settings_from_file(tmp_path: Path) -> None:
    cfg = {
        "canvas": {"width": 100, "height": 200, "fps": 30},
        "hud": {"title": "X", "watermark": "Y"},
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg))
    settings = config.load_settings(path)
    assert settings.width == 100
    assert settings.height == 200
    assert settings.fps == 30
    assert settings.hud.title == "X"
    assert settings.hud.watermark == "Y"
