from __future__ import annotations

import random
from pathlib import Path

import typer

from app.core.config import settings
from app.game.match import run_match
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder, Recorder

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


@app.command()
def run(
    seconds: int = 3,
    seed: int = 0,
    weapon_a: str = "katana",
    weapon_b: str = "shuriken",
    out: Path = Path("out.mp4"),
    display: bool = typer.Option(
        False, "--display/--no-display", help="Display simulation instead of recording"
    ),
) -> None:
    """Run a single match and optionally export a video."""
    random.seed(seed)
    if display:
        renderer = Renderer(settings.width, settings.height, display=True)
        recorder = NullRecorder()
    else:
        recorder = Recorder(settings.width, settings.height, settings.fps, out)
        renderer = Renderer(settings.width, settings.height)
    run_match(seconds, weapon_a, weapon_b, recorder, renderer)
    if not display:
        typer.echo(f"Saved video to {recorder.path}")


@app.command()
def batch(count: int = 1) -> None:  # noqa: ARG001 - placeholder
    """Placeholder for batch generation."""
    return


if __name__ == "__main__":  # pragma: no cover
    app()
