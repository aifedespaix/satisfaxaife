from __future__ import annotations

import random
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from app.audio import reset_default_engine
from app.audio.env import temporary_sdl_audio_driver
from app.core.config import settings
from app.game.controller import MatchTimeout
from app.game.match import create_controller
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder, Recorder, RecorderProtocol
from app.weapons import weapon_registry

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


def _sanitize(name: str) -> str:
    """Return a filesystem-safe version of ``name``."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


@app.command()  # type: ignore[misc]
def run(
    seed: int = 0,
    weapon_a: str = "katana",
    weapon_b: str = "shuriken",
    display: bool = typer.Option(
        False, "--display/--no-display", help="Display simulation instead of recording"
    ),
) -> None:
    """Run a single match and export a video to ``./generated``."""
    random.seed(seed)

    driver = None if display else "dummy"

    recorder: RecorderProtocol
    renderer: Renderer
    temp_path: Path | None = None
    winner: str | None = None

    with temporary_sdl_audio_driver(driver):
        if display:
            renderer = Renderer(settings.width, settings.height, display=True)
            recorder = NullRecorder()
        else:
            out_dir = Path("generated")
            out_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            safe_a = _sanitize(weapon_a)
            safe_b = _sanitize(weapon_b)
            temp_path = out_dir / f"{timestamp}-{safe_a}-VS-{safe_b}.mp4"
            recorder = Recorder(settings.width, settings.height, settings.fps, temp_path)
            renderer = Renderer(settings.width, settings.height)

        controller = create_controller(
            weapon_a,
            weapon_b,
            recorder,
            renderer,
            display=display,
        )
        try:
            winner = controller.run()
        except MatchTimeout as exc:
            if not display and recorder.path is not None and recorder.path.exists():
                recorder.path.unlink()
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(code=1) from None

    if not display and recorder.path is not None and temp_path is not None:
        winner_name = _sanitize(winner) if winner is not None else "draw"
        final_path = temp_path.with_name(f"{temp_path.stem}-{winner_name}_win{temp_path.suffix}")
        temp_path.rename(final_path)
        typer.echo(f"Saved video to {final_path}")


@app.command()  # type: ignore[misc]
def batch(
    count: Annotated[int, typer.Option(help="Number of videos to generate")] = 1,
    out_dir: Annotated[
        Path,
        typer.Option(
            "--out-dir",
            file_okay=False,
            dir_okay=True,
            help="Directory where generated videos are written",
        ),
    ] = Path("generated"),
) -> None:
    """Generate multiple match videos with varied seeds and weapons."""
    out_dir.mkdir(parents=True, exist_ok=True)
    names = weapon_registry.names()

    with temporary_sdl_audio_driver("dummy"):
        for _ in range(count):
            seed = random.randint(0, 1_000_000)
            weapon_a, weapon_b = random.sample(names, k=2)
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            safe_a = _sanitize(weapon_a)
            safe_b = _sanitize(weapon_b)
            temp_path = out_dir / f"{timestamp}-{safe_a}-VS-{safe_b}.mp4"

            random.seed(seed)
            recorder = Recorder(settings.width, settings.height, settings.fps, temp_path)
            renderer = Renderer(settings.width, settings.height)

            controller = create_controller(
                weapon_a,
                weapon_b,
                recorder,
                renderer,
            )
            try:
                winner = controller.run()
            except MatchTimeout as exc:
                if temp_path.exists():
                    temp_path.unlink()
                typer.echo(f"Match {seed} timed out: {exc}", err=True)
            else:
                winner_name = _sanitize(winner) if winner is not None else "draw"
                final_path = temp_path.with_name(
                    f"{temp_path.stem}-{winner_name}_win{temp_path.suffix}"
                )
                temp_path.rename(final_path)
                typer.echo(f"Saved video to {final_path}")
            finally:
                reset_default_engine()


if __name__ == "__main__":  # pragma: no cover
    app()
