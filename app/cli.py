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
from app.core.images import sanitize_images as sanitize_directory_images
from app.game.controller import MatchTimeout
from app.game.match import create_controller
from app.intro.config import IntroConfig, set_intro_weapons
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder, Recorder, RecorderProtocol
from app.weapons import weapon_registry

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


def _sanitize(name: str) -> str:
    """Return a filesystem-safe version of ``name``."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def _load_run_defaults_from_yaml(path: Path = Path("config.yml")) -> dict[str, str]:
    """Load simple key/value defaults from a YAML file.

    The parser supports a minimal subset: ``key: value`` per line, comments
    starting with ``#``, and ignores blank lines. Values are returned as strings
    and converted by the caller as needed. Recognised keys include
    ``weapon_a``, ``weapon_b``, ``seed``, ``max_simulation_seconds`` and
    ``ai_transition_seconds``.

    Parameters
    ----------
    path: Path
        Path to the YAML configuration file.

    Returns
    -------
    dict[str, str]
        Mapping of keys to string values.
    """
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _resolve_run_parameters(
    seed: int | None,
    weapon_a: str | None,
    weapon_b: str | None,
    max_seconds: int | None,
    ai_transition_seconds: int | None,
) -> tuple[int, str, str, int, int]:
    """Return CLI parameters with defaults applied from ``config.yml``."""
    cfg = _load_run_defaults_from_yaml()
    if weapon_a is None:
        weapon_a = cfg.get("weapon_a", "katana")
    if weapon_b is None:
        weapon_b = cfg.get("weapon_b", "shuriken")
    if seed is None:
        seed = int(cfg.get("seed", "0") or 0)
    if max_seconds is None and "max_simulation_seconds" in cfg:
        try:
            max_seconds = int(cfg["max_simulation_seconds"])
        except ValueError:
            max_seconds = None
    if ai_transition_seconds is None and "ai_transition_seconds" in cfg:
        try:
            ai_transition_seconds = int(cfg["ai_transition_seconds"])
        except ValueError:
            ai_transition_seconds = None

    weapon_a = weapon_a or "katana"
    weapon_b = weapon_b or "shuriken"
    seed = int(seed or 0)
    max_seconds = max_seconds or 120
    ai_transition_seconds = int(ai_transition_seconds or 20)
    return seed, weapon_a, weapon_b, max_seconds, ai_transition_seconds


@app.command()  # type: ignore[misc]
def run(
    seed: int | None = None,
    weapon_a: str | None = None,
    weapon_b: str | None = None,
    max_seconds: Annotated[
        int | None,
        typer.Option(
            "--max-seconds",
            help="Override maximum match duration in seconds",
        ),
    ] = None,
    ai_transition_seconds: Annotated[
        int | None,
        typer.Option(
            "--ai-transition-seconds",
            help="Delay before switching to advanced AI, in seconds",
        ),
    ] = None,
    intro_weapons: Annotated[
        tuple[str, str] | None,
        typer.Option(
            "--intro-weapons",
            metavar=("left=PATH", "right=PATH"),
            help="Override intro weapon images",
        ),
    ] = None,
    display: bool = typer.Option(
        False, "--display/--no-display", help="Display simulation instead of recording"
    ),
) -> None:
    """Run a single match and export a video to ``./generated``.

    If the match exceeds the maximum duration, the partially recorded video is
    still kept on disk with a ``-timeout`` suffix.
    """
    # If parameters are not provided, read defaults from config.yml
    seed, weapon_a, weapon_b, max_seconds_val, ai_transition_seconds = _resolve_run_parameters(
        seed,
        weapon_a,
        weapon_b,
        max_seconds,
        ai_transition_seconds,
    )

    random.seed(seed)
    rng = random.Random(seed)

    driver = None if display else "dummy"

    recorder: RecorderProtocol
    renderer: Renderer
    temp_path: Path | None = None
    winner: str | None = None
    intro_config: IntroConfig | None = None

    if intro_weapons is not None:
        paths: dict[str, Path] = {}
        for item in intro_weapons:
            key, _, value = item.partition("=")
            if key not in {"left", "right"} or not value:
                raise typer.BadParameter("intro-weapons must be 'left=PATH right=PATH'")
            paths[key] = Path(value)
        intro_config = set_intro_weapons(
            paths.get("left"),
            paths.get("right"),
        )

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
            max_seconds=max_seconds_val,
            ai_transition_seconds=ai_transition_seconds,
            display=display,
            intro_config=intro_config,
            rng=rng,
        )
        try:
            winner = controller.run()
        except MatchTimeout as exc:
            if not display and temp_path is not None and temp_path.exists():
                final_path = temp_path.with_name(f"{temp_path.stem}-timeout{temp_path.suffix}")
                temp_path.rename(final_path)
                typer.echo(f"Match timed out: {exc}", err=True)
                typer.echo(f"Saved video to {final_path}")
            else:
                typer.echo(f"Match timed out: {exc}", err=True)
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
            rng = random.Random(seed)
            recorder = Recorder(settings.width, settings.height, settings.fps, temp_path)
            renderer = Renderer(settings.width, settings.height)

            controller = create_controller(
                weapon_a,
                weapon_b,
                recorder,
                renderer,
                rng=rng,
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


@app.command("sanitize-images")  # type: ignore[misc]
def sanitize_images_command(
    directory: Annotated[
        Path,
        typer.Argument(
            file_okay=False,
            dir_okay=True,
            exists=True,
            help="Directory containing image assets",
        ),
    ] = Path("assets"),
) -> None:
    """Validate and repair image files in ``directory``."""
    sanitized = sanitize_directory_images(directory)
    typer.echo(f"Sanitized {len(sanitized)} image(s) in {directory}")


if __name__ == "__main__":  # pragma: no cover
    app()
