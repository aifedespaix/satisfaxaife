from __future__ import annotations

import random
from pathlib import Path

import typer

from app.core.config import settings
from app.game.match import run_match
from app.video.recorder import Recorder
from app.weapons import weapon_registry

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


@app.command()
def run(
    seconds: int = 3,
    seed: int = 0,
    weapon_a: str = "katana",
    weapon_b: str = "shuriken",
    out: Path = Path("out.mp4"),
) -> None:
    """Run a single match and export a video."""
    random.seed(seed)
    recorder = Recorder(settings.width, settings.height, settings.fps, out)
    run_match(seconds, weapon_a, weapon_b, recorder)
    typer.echo(f"Saved video to {recorder.path}")


@app.command()
def batch(
    count: int = 1,
    out_dir: Path = Path("out"),
) -> None:
    """Generate *count* videos with varying seeds and weapons."""
    names = weapon_registry.names()
    if len(names) < 2:
        msg = "At least two weapons are required"
        raise typer.BadParameter(msg)
    out_dir.mkdir(parents=True, exist_ok=True)
    for _ in range(count):
        seed = random.randint(0, 2**32 - 1)
        weapon_a, weapon_b = random.sample(names, 2)
        random.seed(seed)
        filename = f"battle_seed{seed}_{weapon_a}_vs_{weapon_b}.mp4"
        path = out_dir / filename
        recorder = Recorder(settings.width, settings.height, settings.fps, path)
        run_match(3, weapon_a, weapon_b, recorder)
        typer.echo(f"Saved video to {recorder.path}")


if __name__ == "__main__":  # pragma: no cover
    app()
