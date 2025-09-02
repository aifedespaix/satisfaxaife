from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("pydantic")
from typer.testing import CliRunner

import app.cli as cli_module
from app.cli import app


class DummyRenderer:
    def __init__(self, width: int, height: int, display: bool = False) -> None:
        self.width = width
        self.height = height
        self.display = display

    def close(self) -> None:  # pragma: no cover - interface compatibility
        pass


def _clear_weapon_modules() -> None:
    for name in list(sys.modules):
        if name.startswith("app.weapons"):
            sys.modules.pop(name)


def test_run_without_preimport(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_weapon_modules()

    class DummyRecorder:
        def __init__(self, width: int, height: int, fps: int, path: Path) -> None:  # noqa: ARG002
            self.path: Path | None = None

        def add_frame(self, _frame: object) -> None:  # pragma: no cover - interface compatibility
            pass

        def close(
            self, _audio: object | None = None, rate: int = 48_000
        ) -> None:  # pragma: no cover - interface compatibility
            pass

    def fake_create_controller(*_args: object, **_kwargs: object) -> object:
        class Controller:
            def run(self) -> str:
                return "winner"

        return Controller()

    monkeypatch.setattr(cli_module, "Recorder", DummyRecorder)
    monkeypatch.setattr(cli_module, "Renderer", DummyRenderer)
    monkeypatch.setattr(cli_module, "create_controller", fake_create_controller)

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["run", "--seed", "1", "--weapon-a", "katana", "--weapon-b", "shuriken"],
        )
    assert result.exit_code == 0


def test_batch_without_preimport(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_weapon_modules()

    class DummyRecorder:
        def __init__(self, width: int, height: int, fps: int, path: Path) -> None:  # noqa: ARG002
            self.path = path

        def add_frame(self, _frame: object) -> None:  # pragma: no cover - interface compatibility
            pass

        def close(
            self, _audio: object | None = None, rate: int = 48_000
        ) -> None:  # pragma: no cover - interface compatibility
            pass

    def fake_create_controller(
        _weapon_a: str,
        _weapon_b: str,
        recorder: DummyRecorder,
        _renderer: DummyRenderer,
        **_kwargs: object,
    ) -> object:
        class Controller:
            def run(self) -> str:
                if recorder.path is not None:
                    recorder.path.write_bytes(b"data")
                return "winner"

        return Controller()

    monkeypatch.setattr(cli_module, "Recorder", DummyRecorder)
    monkeypatch.setattr(cli_module, "Renderer", DummyRenderer)
    monkeypatch.setattr(cli_module, "create_controller", fake_create_controller)

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["batch", "--count", "1"])
    assert result.exit_code == 0
