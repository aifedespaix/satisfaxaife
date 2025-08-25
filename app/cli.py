from __future__ import annotations

import random
from pathlib import Path

import typer

from app.core.config import settings
from app.game.match import MatchTimeout, run_match
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder, Recorder

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


@app.command()
def run(
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

    # Choix du renderer et du recorder selon le mode
    if display:
        renderer = Renderer(settings.width, settings.height, display=True)
        recorder = NullRecorder()
    else:
        recorder = Recorder(settings.width, settings.height, settings.fps, out)
        renderer = Renderer(settings.width, settings.height)

    try:
        # API unifiée : la gestion du temps est interne et peut lever MatchTimeout
        # (adapte si run_match diffère dans ton codebase)
        run_match(weapon_a, weapon_b, recorder, renderer)
    except MatchTimeout as exc:
        # Nettoyage du fichier partiel si un Recorder fichier était utilisé
        path = getattr(recorder, "path", None)
        if path is not None and path.exists():
            path.unlink()
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    if not display:
        typer.echo(f"Saved video to {recorder.path}")


@app.command()
def batch(count: int = 1) -> None:  # noqa: ARG001 - placeholder
    """Placeholder for batch generation."""
    return


if __name__ == "__main__":  # pragma: no cover
    app()
