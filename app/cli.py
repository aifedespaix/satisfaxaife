from __future__ import annotations

import random
from pathlib import Path

import typer

from app.core.config import settings
from app.game.match import run_match
from app.video.recorder import Recorder

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


@app.command()
def run(seconds: int = 3, seed: int = 0, out: Path = Path("out.mp4")) -> None:
    """Run a single stub match and export a video."""
    random.seed(seed)
    recorder = Recorder(settings.width, settings.height, settings.fps, out)
    run_match(seconds, recorder)
    typer.echo(f"Saved video to {recorder.path}")


@app.command()
def batch(count: int = 1) -> None:  # noqa: ARG001 - placeholder
    """Placeholder for batch generation."""
    return


if __name__ == "__main__":  # pragma: no cover
    app()
