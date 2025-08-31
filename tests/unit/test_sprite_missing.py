from __future__ import annotations

import logging

import pytest

from app.render.sprites import load_sprite


def test_load_sprite_missing_asset_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    missing_name = "does_not_exist.png"
    with caplog.at_level(logging.WARNING):
        with pytest.raises(FileNotFoundError):
            load_sprite(missing_name)
    assert missing_name in caplog.text
