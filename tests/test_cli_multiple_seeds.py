from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any, Callable, cast

import pytest


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


def test_run_multiple_seeds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_typer_stub()
    import app.cli as cli

    captured: list[int] = []

    def fake_run(
        seed: int,
        weapon_a: str,
        weapon_b: str,
        max_seconds: int,
        ai_transition_seconds: int,
        intro_weapons: tuple[str, str] | None,
        display: bool,
        debug_flag: bool,
    ) -> None:
        captured.append(seed)

    monkeypatch.setattr(cli, "_run_single_match", fake_run)

    config = "\n".join([
        "weapon_a: katana",
        "weapon_b: shuriken",
        "seeds: [1, 2]",
    ])
    (tmp_path / "config.yml").write_text(config, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    cli.run(display=True)

    assert captured == [1, 2]
