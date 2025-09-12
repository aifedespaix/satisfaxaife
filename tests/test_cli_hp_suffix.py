from __future__ import annotations

import contextlib
import sys
import types
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import pytest


@contextlib.contextmanager
def _dummy_driver(_driver: str | None) -> Iterator[None]:
    yield


class _DummyRenderer:
    def __init__(
        self, width: int, height: int, display: bool = False, *, debug: bool = False
    ) -> None:
        self.width = width
        self.height = height
        self.display = display
        self.debug = debug


class _DummyRecorder:
    def __init__(self, width: int, height: int, fps: int, path: Path) -> None:
        self.path = path

    def add_frame(self, _frame: object) -> None:  # pragma: no cover - interface compat
        pass

    def close(
        self, _audio: object | None = None, rate: int = 48_000
    ) -> None:  # pragma: no cover - compat
        if self.path:
            self.path.write_bytes(b"data")


def _fake_create_controller(
    weapon_a: str,
    weapon_b: str,
    recorder: _DummyRecorder,
    renderer: _DummyRenderer,
    **_kwargs: Any,
) -> Any:
    class Controller:
        def run(self) -> str:
            if recorder.path:
                recorder.path.write_bytes(b"data")
            return weapon_a

        def get_winner_health_ratio(self) -> float:
            return 0.42

    return Controller()


def _install_typer_stub() -> None:
    class _Typer:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def command(
            self, *args: object, **kwargs: object
        ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                return func

            return decorator

    def _option(*args: object, **kwargs: object) -> None:
        return None

    def _argument(*args: object, **kwargs: object) -> None:
        return None

    def _echo(*args: object, **kwargs: object) -> None:
        pass

    class _Exit(Exception):
        pass

    class _BadParameter(Exception):
        pass

    typer_stub = cast(
        types.ModuleType,
        types.SimpleNamespace(
            Typer=_Typer,
            Option=_option,
            Argument=_argument,
            echo=_echo,
            Exit=_Exit,
            BadParameter=_BadParameter,
        ),
    )
    sys.modules["typer"] = typer_stub


def test_run_single_match_appends_hp_suffix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Video filename includes winner HP percentage when available."""
    _install_typer_stub()
    import sys
    import types

    sys.modules.setdefault("imageio", types.ModuleType("imageio"))
    sys.modules.setdefault("imageio_ffmpeg", types.ModuleType("imageio_ffmpeg"))
    import app.audio as audio_mod
    import app.audio.env as audio_env
    import app.cli as cli_module
    import app.game.match as match_mod
    import app.render.renderer as renderer_mod
    import app.video.recorder as recorder_mod

    # Stub moviepy module used during export.
    class _DummyClip:
        def __init__(self, path: str) -> None:
            self.path = Path(path)

        def __enter__(self) -> _DummyClip:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

    def _fake_video_file_clip(path: str) -> _DummyClip:
        return _DummyClip(path)

    sys.modules.setdefault("moviepy", types.ModuleType("moviepy"))
    moviepy_editor = types.SimpleNamespace(VideoFileClip=_fake_video_file_clip)
    sys.modules["moviepy.editor"] = moviepy_editor

    def _fake_export(clip: _DummyClip, out_path: str, **_kwargs: object) -> str:
        Path(out_path).write_bytes(clip.path.read_bytes())
        return out_path

    monkeypatch.setattr("app.video.export.export_tiktok", _fake_export)
    import app.weapons as weapons_mod

    monkeypatch.setattr(weapons_mod.weapon_registry, "names", lambda: None)
    monkeypatch.setattr(audio_env, "temporary_sdl_audio_driver", _dummy_driver)
    monkeypatch.setattr(audio_mod, "reset_default_engine", lambda: None)
    monkeypatch.setattr(renderer_mod, "Renderer", _DummyRenderer)
    monkeypatch.setattr(recorder_mod, "Recorder", _DummyRecorder)
    monkeypatch.setattr(match_mod, "create_controller", _fake_create_controller)

    monkeypatch.chdir(tmp_path)
    cli_module._run_single_match(
        seed=1,
        weapon_a="katana",
        weapon_b="shuriken",
        max_seconds=1,
        ai_transition_seconds=1,
        intro_weapons=None,
        display=False,
        debug_flag=False,
        boost_tiktok=True,
    )

    files = list((tmp_path / "generated").glob("*.mp4"))
    assert len(files) == 1
    assert files[0].name.endswith("_win-42.mp4")
