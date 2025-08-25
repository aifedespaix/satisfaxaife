from __future__ import annotations

import random
from pathlib import Path

import typer

from app.core.config import settings
from app.game.match import MatchTimeout, run_match
from app.video.recorder import Recorder

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


@app.command()
def run(
    seed: int = 0,
    weapon_a: str = "katana",
    weapon_b: str = "shuriken",
    out: Path = Path("out.mp4"),
) -> None:
    """Run a single match and export a video."""
    random.seed(seed)
    recorder = Recorder(settings.width, settings.height, settings.fps, out)
    try:
        run_match(weapon_a, weapon_b, recorder)
    except MatchTimeout as exc:
        if recorder.path.exists():
            recorder.path.unlink()
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Saved video to {recorder.path}")


@app.command()
def batch(count: int = 1) -> None:  # noqa: ARG001 - placeholder
    """Placeholder for batch generation."""
    return


if __name__ == "__main__":  # pragma: no cover
    app()
