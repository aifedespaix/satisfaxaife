from __future__ import annotations

import random
from pathlib import Path
from typing import Annotated, cast

import typer

from app.core.config import settings
from app.game.match import MatchTimeout, run_match
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder, Recorder
from app.weapons import weapon_registry

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


@app.command()  # type: ignore[misc]
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

    recorder: Recorder | NullRecorder
    if display:
        display_width = settings.width // 2
        display_height = settings.height // 2
        renderer = Renderer(display_width, display_height, display=True)
        recorder = NullRecorder()
    else:
        recorder = Recorder(settings.width, settings.height, settings.fps, out)
        renderer = Renderer(settings.width, settings.height)

    try:
        run_match(weapon_a, weapon_b, cast(Recorder, recorder), renderer)
    except MatchTimeout as exc:
        path = getattr(recorder, "path", None)
        if path is not None and path.exists():
            path.unlink()
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from None

    if isinstance(recorder, Recorder):
        typer.echo(f"Saved video to {recorder.path}")


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
    ] = Path("out"),
) -> None:
    """Generate multiple match videos with varied seeds and weapons."""
    out_dir.mkdir(parents=True, exist_ok=True)
    names = weapon_registry.names()

    for _ in range(count):
        seed = random.randint(0, 1_000_000)
        weapon_a, weapon_b = random.sample(names, k=2)
        filename = f"battle_seed{seed}_{weapon_a}_vs_{weapon_b}.mp4"
        out_path = out_dir / filename

        random.seed(seed)
        recorder = Recorder(settings.width, settings.height, settings.fps, out_path)
        renderer = Renderer(settings.width, settings.height)

        try:
            run_match(weapon_a, weapon_b, recorder, renderer)
        except MatchTimeout as exc:
            if out_path.exists():
                out_path.unlink()
            typer.echo(f"Match {seed} timed out: {exc}", err=True)
        else:
            typer.echo(f"Saved video to {out_path}")


if __name__ == "__main__":  # pragma: no cover
    app()
