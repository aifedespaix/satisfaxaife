from __future__ import annotations

import random
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(help="Génération de vidéos satisfaction (TikTok).")


def _sanitize(name: str) -> str:
    """Return a filesystem-safe version of ``name``."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def _build_final_path(
    temp_path: Path, winner: str | None, hp_ratio: float | None, *, seed: int | None
) -> Path:
    """Return final video path with winner name, HP and seed suffix.

    Parameters
    ----------
    temp_path: Path
        Temporary path used during recording (same directory, base stem).
    winner: str | None
        Winner name (sanitized) or ``None`` for a draw.
    hp_ratio: float | None
        Remaining HP ratio for the winner in ``[0, 1]``; used for a ``-NN`` suffix.
    seed: int | None
        Random seed used for the simulation; appended as ``_seed-{seed}``.

    Returns
    -------
    Path
        Final output path with composed suffixes before the extension.
    """
    winner_name = _sanitize(winner) if winner is not None else "draw"
    hp_suffix = ""
    if hp_ratio is not None:
        percent = int(round(max(0.0, min(1.0, hp_ratio)) * 100))
        hp_suffix = f"-{percent:02d}"
    seed_suffix = f"_seed-{seed}" if seed is not None else ""
    return temp_path.with_name(
        f"{temp_path.stem}-{winner_name}_win{hp_suffix}{seed_suffix}{temp_path.suffix}"
    )


def _load_run_defaults_from_yaml(path: Path = Path("config.yml")) -> dict[str, str | list[str]]:
    """Load simple key/value defaults from a YAML file.

    The parser supports a minimal subset: ``key: value`` per line, comments
    starting with ``#``, and ignores blank lines. Values are returned as strings
    except for ``seeds`` which accepts a comma-separated list on a single line.

    Recognised keys include ``weapon_a``, ``weapon_b``, ``seed``,
    ``seeds``, ``max_simulation_seconds``, ``ai_transition_seconds``,
    ``team_a_count``, ``team_b_count`` and ``debug``.

    Parameters
    ----------
    path: Path
        Path to the YAML configuration file.

    Returns
    -------
    dict[str, str | list[str]]
        Mapping of keys to string values or lists of string values.
    """
    data: dict[str, str | list[str]] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "seeds":
            if value.startswith("[") and value.endswith("]"):
                value = value[1:-1]
            items = [v.strip() for v in value.split(",") if v.strip()]
            data[key] = items
        else:
            data[key] = value
    return data


def _apply_team_counts(cfg: dict[str, str | list[str]]) -> None:
    """Apply team sizes from configuration mapping to runtime settings."""
    from app.core.config import settings

    for key in ("team_a_count", "team_b_count"):
        if key in cfg:
            try:
                setattr(settings, key, int(str(cfg[key])))
            except ValueError:
                continue


def _resolve_run_parameters(
    seed: int | None,
    weapon_a: str | None,
    weapon_b: str | None,
    max_seconds: int | None,
    ai_transition_seconds: int | None,
    debug: bool | None,
) -> tuple[list[int], str, str, int, int, bool]:
    """Return CLI parameters with defaults applied from ``config.yml``."""
    cfg = _load_run_defaults_from_yaml()
    if weapon_a is None:
        weapon_a = str(cfg.get("weapon_a", "katana"))
    if weapon_b is None:
        weapon_b = str(cfg.get("weapon_b", "shuriken"))

    seeds: list[int]
    if seed is not None:
        seeds = [int(seed)]
    elif "seeds" in cfg:
        seeds = [int(s) for s in cfg.get("seeds", [])]
    else:
        seed_val = int(str(cfg.get("seed", "0") or 0))
        seeds = [seed_val]

    if max_seconds is None and "max_simulation_seconds" in cfg:
        try:
            max_seconds = int(str(cfg["max_simulation_seconds"]))
        except ValueError:
            max_seconds = None
    if ai_transition_seconds is None and "ai_transition_seconds" in cfg:
        try:
            ai_transition_seconds = int(str(cfg["ai_transition_seconds"]))
        except ValueError:
            ai_transition_seconds = None
    if debug is None and "debug" in cfg:
        debug = str(cfg["debug"]).lower() in {"1", "true", "yes", "on"}
    _apply_team_counts(cfg)

    weapon_a = weapon_a or "katana"
    weapon_b = weapon_b or "shuriken"
    max_seconds = max_seconds or 120
    ai_transition_seconds = int(ai_transition_seconds or 20)
    debug = bool(debug)
    return seeds, weapon_a, weapon_b, max_seconds, ai_transition_seconds, debug


def _run_single_match(  # noqa: C901
    seed: int,
    weapon_a: str,
    weapon_b: str,
    max_seconds: int,
    ai_transition_seconds: int,
    intro_weapons: tuple[str, str] | None,
    display: bool,
    debug_flag: bool,
    boost_tiktok: bool,
) -> bool:
    """Run a single match and write the resulting video to disk.

    Returns ``True`` if the match completed within ``max_seconds`` and ``False``
    if a :class:`~app.game.controller.MatchTimeout` occurred. The caller may use
    the boolean to decide whether to continue processing further seeds.
    """

    from app.audio import reset_default_engine
    from app.audio.env import temporary_sdl_audio_driver
    from app.core.config import settings
    from app.core.registry import UnknownWeaponError
    from app.game.controller import MatchTimeout
    from app.game.match import create_controller
    from app.intro.config import IntroConfig, set_intro_weapons
    from app.render.renderer import Renderer
    from app.video.recorder import (
        NullRecorder,
        Recorder,
        RecorderProtocol,
        VideoMuxingError,
    )
    from app.weapons import weapon_registry

    random.seed(seed)
    rng = random.Random(seed)
    driver = None if display else "dummy"

    recorder: RecorderProtocol
    renderer: Renderer
    temp_path: Path | None = None
    winner: str | None = None
    winner_hp_ratio: float | None = None
    intro_config: IntroConfig | None = None

    if intro_weapons is not None:
        paths: dict[str, Path] = {}
        for item in intro_weapons:
            key, _, value = item.partition("=")
            if key not in {"left", "right"} or not value:
                raise typer.BadParameter("intro-weapons must be 'left=PATH right=PATH'")
            paths[key] = Path(value)
        intro_config = set_intro_weapons(paths.get("left"), paths.get("right"))

    with temporary_sdl_audio_driver(driver):
        weapon_registry.names()
        if display:
            renderer = Renderer(settings.width, settings.height, display=True, debug=debug_flag)
            recorder = NullRecorder()
        else:
            out_dir = Path("generated")
            out_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            safe_a = _sanitize(weapon_a)
            safe_b = _sanitize(weapon_b)
            # Build a neutral temp name; seed will be appended as a final suffix.
            temp_path = out_dir / f"{timestamp}-{safe_a}-VS-{safe_b}.mp4"
            recorder = Recorder(settings.width, settings.height, settings.fps, temp_path)
            renderer = Renderer(settings.width, settings.height, debug=debug_flag)

        timed_out = False
        mux_failed = False
        try:
            controller = create_controller(
                weapon_a,
                weapon_b,
                recorder,
                renderer,
                max_seconds=max_seconds,
                ai_transition_seconds=ai_transition_seconds,
                display=display,
                intro_config=intro_config,
                rng=rng,
            )
        except UnknownWeaponError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from None
        try:
            winner = controller.run()
            get_ratio = getattr(controller, "get_winner_health_ratio", None)
            if callable(get_ratio):
                winner_hp_ratio = get_ratio()
        except MatchTimeout as exc:
            timed_out = True
            if not display and temp_path is not None and temp_path.exists():
                final_path = temp_path.with_name(
                    f"{temp_path.stem}-timeout_seed-{seed}{temp_path.suffix}"
                )
                temp_path.rename(final_path)
                typer.echo(f"Match timed out: {exc}", err=True)
                typer.echo(f"Saved video to {final_path}")
            else:
                typer.echo(f"Match timed out: {exc}", err=True)
        except VideoMuxingError as exc:
            mux_failed = True
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
            typer.echo(f"Video muxing failed: {exc}", err=True)
        finally:
            reset_default_engine()

    if timed_out or mux_failed:
        return False

    if not display and recorder.path is not None and temp_path is not None:
        final_path = _build_final_path(temp_path, winner, winner_hp_ratio, seed=seed)

        from app.video.export import export_tiktok  # noqa: I001
        from moviepy.editor import VideoFileClip

        with VideoFileClip(str(temp_path)) as clip:
            export_tiktok(clip, str(final_path), fps=settings.fps, boost_tiktok=boost_tiktok)
        temp_path.unlink(missing_ok=True)
        typer.echo(f"Saved video to {final_path}")

    return True


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
    debug: Annotated[
        bool | None,
        typer.Option(
            "--debug/--no-debug",
            help="Enable debug rendering (hitboxes and helpers)",
        ),
    ] = None,
    boost_tiktok: bool = typer.Option(
        True,
        "--boost-tiktok/--no-boost-tiktok",
        help="Apply color boost suited for TikTok",
    ),
) -> None:
    """Run one or more matches and export videos to ``./generated``."""
    (
        seeds,
        weapon_a_res,
        weapon_b_res,
        max_seconds_val,
        ai_transition_seconds,
        debug_flag,
    ) = _resolve_run_parameters(
        seed,
        weapon_a,
        weapon_b,
        max_seconds,
        ai_transition_seconds,
        debug,
    )

    exit_code = 0
    for seed_val in seeds:
        ok = _run_single_match(
            seed_val,
            weapon_a_res,
            weapon_b_res,
            max_seconds_val,
            ai_transition_seconds,
            intro_weapons,
            display,
            debug_flag,
            boost_tiktok,
        )
        if not ok:
            exit_code = 1
    if exit_code:
        raise typer.Exit(code=exit_code)


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
    boost_tiktok: bool = typer.Option(
        True,
        "--boost-tiktok/--no-boost-tiktok",
        help="Apply color boost suited for TikTok",
    ),
) -> None:
    """Generate multiple match videos with varied seeds and weapons."""
    from app.audio import reset_default_engine
    from app.audio.env import temporary_sdl_audio_driver
    from app.core.config import settings
    from app.core.registry import UnknownWeaponError
    from app.game.controller import MatchTimeout
    from app.game.match import create_controller
    from app.render.renderer import Renderer
    from app.video.recorder import Recorder, VideoMuxingError
    from app.weapons import weapon_registry

    out_dir.mkdir(parents=True, exist_ok=True)

    with temporary_sdl_audio_driver("dummy"):
        names = weapon_registry.names()
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

            try:
                controller = create_controller(
                    weapon_a,
                    weapon_b,
                    recorder,
                    renderer,
                    rng=rng,
                )
            except UnknownWeaponError as exc:
                typer.echo(str(exc), err=True)
                raise typer.Exit(code=1) from None
            try:
                winner = controller.run()
            except MatchTimeout as exc:
                if temp_path.exists():
                    temp_path.unlink()
                typer.echo(f"Match {seed} timed out: {exc}", err=True)
            except VideoMuxingError as exc:
                if temp_path.exists():
                    temp_path.unlink()
                typer.echo(f"Video muxing failed: {exc}", err=True)
            else:
                winner_name = _sanitize(winner) if winner is not None else "draw"
                final_path = temp_path.with_name(
                    f"{temp_path.stem}-{winner_name}_win_seed-{seed}{temp_path.suffix}"
                )

                from app.video.export import export_tiktok  # noqa: I001
                from moviepy.editor import VideoFileClip

                with VideoFileClip(str(temp_path)) as clip:
                    export_tiktok(
                        clip, str(final_path), fps=settings.fps, boost_tiktok=boost_tiktok
                    )
                temp_path.unlink(missing_ok=True)
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
    from app.core.images import sanitize_images as sanitize_directory_images

    sanitized = sanitize_directory_images(directory)
    typer.echo(f"Sanitized {len(sanitized)} image(s) in {directory}")


if __name__ == "__main__":  # pragma: no cover
    app()
