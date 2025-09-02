from __future__ import annotations

import random
from pathlib import Path

from app.ai.stateful_policy import policy_for_weapon
from app.audio import BallAudio, get_default_engine
from app.core.config import settings
from app.core.registry import UnknownWeaponError
from app.game.controller import (
    GameController,
    MatchTimeout,  # noqa: F401 - re-exported
    Player,
    _MatchView,  # noqa: F401 - re-exported for tests
)
from app.intro import IntroConfig, IntroManager, set_intro_weapons
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import RecorderProtocol
from app.weapons import weapon_registry
from app.world.entities import Ball
from app.world.physics import PhysicsWorld

__all__ = [
    "create_controller",
    "run_match",
    "GameController",
    "MatchTimeout",
    "Player",
    "_MatchView",
]


def create_controller(
    weapon_a: str,
    weapon_b: str,
    recorder: RecorderProtocol,
    renderer: Renderer | None = None,
    *,
    max_seconds: int = 120,
    ai_transition_seconds: int = 20,
    display: bool = False,
    intro_config: IntroConfig | None = None,
    rng: random.Random | None = None,
) -> GameController:
    """Construct a :class:`GameController` with default components.

    Parameters
    ----------
    weapon_a, weapon_b:
        Names of the weapons used by the two players.
    recorder:
        Recorder responsible for writing frames to disk.
    renderer:
        Optional renderer. When ``None`` a new instance is created.
    max_seconds:
        Maximum duration of the match before raising :class:`MatchTimeout`.
    ai_transition_seconds:
        Delay before the AI switches to its advanced behaviour.
    display:
        Whether to render to the screen instead of recording frames.
    intro_config:
        Intro sequence configuration. Defaults to :class:`IntroConfig()`.
    rng:
        Random number generator controlling AI behaviour. When ``None``, a new
        instance derived from a random seed is used.
    """
    engine = get_default_engine()
    world = PhysicsWorld()
    renderer = renderer or Renderer(settings.width, settings.height, display=display)
    hud = Hud(settings.theme)

    rng = rng or random.Random(random.randint(0, 2**63 - 1))
    rng_a = random.Random(rng.randint(0, 2**63 - 1))
    rng_b = random.Random(rng.randint(0, 2**63 - 1))

    ball_a = Ball.spawn(world, (settings.width * 0.25, settings.height * 0.5))
    ball_b = Ball.spawn(world, (settings.width * 0.75, settings.height * 0.5))

    try:
        weapon_a_obj = weapon_registry.create(weapon_a)
    except UnknownWeaponError as exc:
        raise UnknownWeaponError(exc.name, exc.available) from None

    try:
        weapon_b_obj = weapon_registry.create(weapon_b)
    except UnknownWeaponError as exc:
        raise UnknownWeaponError(exc.name, exc.available) from None

    players = [
        Player(
            ball_a.eid,
            ball_a,
            weapon_a_obj,
            policy_for_weapon(weapon_a, weapon_b, ai_transition_seconds, rng=rng_a),
            (1.0, 0.0),
            settings.theme.team_a.primary,
            BallAudio(engine=engine),
        ),
        Player(
            ball_b.eid,
            ball_b,
            weapon_b_obj,
            policy_for_weapon(weapon_b, weapon_a, ai_transition_seconds, rng=rng_b),
            (-1.0, 0.0),
            settings.theme.team_b.primary,
            BallAudio(engine=engine),
        ),
    ]

    intro_config = intro_config or IntroConfig()
    weapons_dir = Path(__file__).resolve().parents[2] / "assets" / "weapons"
    weapon_a_path = weapons_dir / weapon_a / "weapon.png"
    weapon_b_path = weapons_dir / weapon_b / "weapon.png"
    intro_config = set_intro_weapons(weapon_a_path, weapon_b_path, config=intro_config)
    intro = IntroManager(config=intro_config)
    return GameController(
        weapon_a,
        weapon_b,
        players,
        world,
        renderer,
        hud,
        engine,
        recorder,
        intro,
        max_seconds=max_seconds,
        ai_transition_seconds=ai_transition_seconds,
        display=display,
    )


def run_match(
    weapon_a: str,
    weapon_b: str,
    recorder: RecorderProtocol,
    renderer: Renderer | None = None,
    *,
    max_seconds: int = 120,
    display: bool = False,
) -> str | None:
    """Run a match using a :class:`GameController`.

    This function is kept for backward compatibility; it simply
    instantiates a controller and returns the result of its :meth:`run`.
    """
    controller = create_controller(
        weapon_a,
        weapon_b,
        recorder,
        renderer,
        max_seconds=max_seconds,
        display=display,
    )
    return controller.run()
