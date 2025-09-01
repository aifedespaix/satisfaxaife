from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

pygame = pytest.importorskip("pygame")

if TYPE_CHECKING:  # pragma: no cover - type hints only
    import pygame as _pygame

from app.intro import IntroAssets, IntroConfig, IntroState  # noqa: E402
from app.render.hud import Hud  # noqa: E402
from app.render.intro_renderer import IntroRenderer  # noqa: E402
from app.render.theme import TeamColors, Theme  # noqa: E402


def test_compute_positions_slide_and_center() -> None:
    renderer = IntroRenderer(200, 100)
    left_start, right_start, center = renderer.compute_positions(0.0)
    assert left_start[0] < 0
    assert right_start[0] > renderer.width
    assert center == (100.0, 45.0)

    left_end, right_end, _ = renderer.compute_positions(1.0)
    assert left_end == (50.0, 60.0)
    assert right_end == (150.0, 60.0)


def test_compute_positions_custom_config() -> None:
    config = IntroConfig(
        left_pos_pct=(0.3, 0.4),
        right_pos_pct=(0.7, 0.6),
        center_pos_pct=(0.5, 0.5),
        slide_offset_pct=0.4,
    )
    renderer = IntroRenderer(100, 200, config=config)
    left_end, right_end, center = renderer.compute_positions(1.0)
    assert left_end == (30.0, 80.0)
    assert right_end == (70.0, 120.0)
    assert center == (50.0, 100.0)


def test_compute_alpha_logo_in_fades_in() -> None:
    renderer = IntroRenderer(200, 100)
    progresses = [0.0, 0.3, 0.6, 1.0]
    alphas = [renderer.compute_alpha(p, IntroState.LOGO_IN) for p in progresses]
    assert alphas[0] == 0
    assert alphas[-1] == 255
    assert all(a0 <= a1 for a0, a1 in zip(alphas, alphas[1:], strict=False))


def test_compute_alpha_weapons_in_stays_opaque() -> None:
    renderer = IntroRenderer(200, 100)
    for p in (0.0, 0.25, 0.5, 0.75, 1.0):
        assert renderer.compute_alpha(p, IntroState.WEAPONS_IN) == 255


def test_compute_alpha_fade_out() -> None:
    renderer = IntroRenderer(200, 100)
    progresses = [1.0, 0.75, 0.5, 0.25, 0.0]
    alphas = [renderer.compute_alpha(p, IntroState.FADE_OUT) for p in progresses]
    assert alphas[0] == 255
    assert alphas[-1] == 0
    assert all(a0 >= a1 for a0, a1 in zip(alphas, alphas[1:], strict=False))


def test_compute_alpha_custom_fade() -> None:
    config = IntroConfig(fade=lambda t: t)
    renderer = IntroRenderer(200, 100, config=config)
    assert renderer.compute_alpha(0.25, IntroState.LOGO_IN) == int(0.25 * 255)


def test_blit_elements_glow_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    blits: list[tuple[int, int]] = []

    original_blit = pygame.Surface.blit

    def counting_blit(
        self: _pygame.Surface,
        source: _pygame.Surface,
        dest: _pygame.Rect | tuple[int, int],
        *args: object,
        **kwargs: object,
    ) -> _pygame.Rect:
        center = dest.center if hasattr(dest, "center") else dest
        blits.append(center)
        return original_blit(self, source, dest, *args, **kwargs)

    monkeypatch.setattr(pygame.Surface, "blit", counting_blit)

    left, right, center = renderer.compute_positions(1.0)
    elements = renderer._prepare_elements(("A", "B"), 1.0, left, right, center)
    angle, scale = renderer._compute_transform(1.0)
    renderer._blit_elements(
        surface, elements, angle, scale, 255, IntroState.HOLD, 1.0
    )

    expected_centers: list[tuple[int, int]] = []
    for base in (left, right, center):
        bx, by = int(base[0]), int(base[1])
        expected_centers.extend(
            [
                (bx + 4, by + 4),
                (bx - 2, by),
                (bx + 2, by),
                (bx, by - 2),
                (bx, by + 2),
                (bx, by),
            ]
        )

    assert len(blits) == len(expected_centers)
    assert set(expected_centers).issubset(set(blits))


def test_blit_elements_overlay_only_logo_in(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    calls: list[object] = []

    original_blit = pygame.Surface.blit

    def tracking_blit(
        self: _pygame.Surface,
        source: _pygame.Surface,
        dest: _pygame.Rect | tuple[int, int],
        *args: object,
        **kwargs: object,
    ) -> _pygame.Rect:
        calls.append(dest)
        return original_blit(self, source, dest, *args, **kwargs)

    monkeypatch.setattr(pygame.Surface, "blit", tracking_blit)

    left, right, center = renderer.compute_positions(0.5)
    elements = renderer._prepare_elements(("A", "B"), 0.5, left, right, center)
    angle, scale = renderer._compute_transform(0.5)
    renderer._blit_elements(
        surface, elements, angle, scale, 255, IntroState.LOGO_IN, 0.5
    )
    assert (0, 0) in calls

    calls.clear()
    renderer._blit_elements(
        surface, elements, angle, scale, 255, IntroState.WEAPONS_IN, 0.5
    )
    assert (0, 0) not in calls
    pygame.quit()


def test_draw_with_assets(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    config = IntroConfig(
        font_path=Path("assets/fonts/FightKickDemoRegular.ttf"),
        logo_path=Path("assets/vs.png"),
        weapon_a_path=Path("assets/ball-a.png"),
        weapon_b_path=Path("assets/ball-b.png"),
    )
    assert config.logo_scale == 0.5
    assets = IntroAssets.load(config)
    renderer = IntroRenderer(200, 100, config=config, assets=assets)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    blits: list[tuple[int, int]] = []

    original_blit = pygame.Surface.blit

    def counting_blit(
        self: _pygame.Surface,
        source: _pygame.Surface,
        dest: _pygame.Rect | tuple[int, int],
        *args: object,
        **kwargs: object,
    ) -> _pygame.Rect:
        center = dest.center if hasattr(dest, "center") else dest
        blits.append(center)
        return original_blit(self, source, dest, *args, **kwargs)

    monkeypatch.setattr(pygame.Surface, "blit", counting_blit)

    renderer.draw(surface, ("A", "B"), 1.0, IntroState.HOLD)

    left_text, right_text, center = renderer.compute_positions(1.0)
    assert renderer.font is not None
    label_a = renderer.font.render("A", True, (255, 255, 255))
    label_b = renderer.font.render("B", True, (255, 255, 255))
    scale = renderer.width * renderer.WEAPON_WIDTH_RATIO / assets.weapon_a.get_width()
    weapon_a = pygame.transform.rotozoom(assets.weapon_a, (1.0 - 0.5) * 10, scale)
    weapon_b = pygame.transform.rotozoom(assets.weapon_b, (1.0 - 0.5) * 10, scale)
    gap = renderer.IMAGE_TEXT_GAP
    weapon_a_pos = (
        left_text[0],
        left_text[1] - label_a.get_height() / 2 - gap - weapon_a.get_height() / 2,
    )
    weapon_b_pos = (
        right_text[0],
        right_text[1] - label_b.get_height() / 2 - gap - weapon_b.get_height() / 2,
    )
    expected_centers: list[tuple[int, int]] = []
    for base in (weapon_a_pos, weapon_b_pos, center, left_text, right_text):
        bx, by = int(base[0]), int(base[1])
        expected_centers.extend(
            [
                (bx + 4, by + 4),
                (bx - 2, by),
                (bx + 2, by),
                (bx, by - 2),
                (bx, by + 2),
                (bx, by),
            ]
        )

    assert len(blits) == len(expected_centers)
    assert set(expected_centers).issubset(set(blits))
    pygame.quit()


def test_logo_scaled_to_config() -> None:
    pygame.init()
    config = IntroConfig(
        font_path=Path("assets/fonts/FightKickDemoRegular.ttf"),
        logo_path=Path("assets/vs.png"),
        weapon_a_path=Path("assets/ball-a.png"),
        weapon_b_path=Path("assets/ball-b.png"),
    )
    assets = IntroAssets.load(config)
    renderer = IntroRenderer(200, 100, config=config, assets=assets)
    left, right, center = renderer.compute_positions(1.0)
    elements = renderer._prepare_elements(("A", "B"), 1.0, left, right, center)
    logo_surface = elements[2][0]
    angle, scale_factor = renderer._compute_transform(1.0)
    expected_logo = pygame.transform.rotozoom(
        assets.logo, angle, config.logo_scale * scale_factor
    )
    assert logo_surface.get_size() == expected_logo.get_size()
    pygame.quit()


def test_apply_fade_out_interpolates_to_hud(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    theme = Theme(
        team_a=TeamColors((0, 0, 0), ((255, 0, 0),)),
        team_b=TeamColors((0, 0, 0), ((0, 0, 255),)),
        hp_empty=(0, 0, 0),
        hp_warning=(255, 0, 0),
    )
    hud = Hud(theme)
    labels = ("A", "B")
    label_a_rect, label_b_rect, logo_rect, _ = hud.compute_layout(surface, labels)
    targets = (logo_rect, label_a_rect, label_b_rect)

    left, right, center = renderer.compute_positions(1.0)
    elements = renderer._prepare_elements(labels, 1.0, left, right, center)
    angle, _ = renderer._compute_transform(1.0)

    mid_elements, _ = renderer._apply_fade_out(
        [e for e in elements], angle, 0.5, targets, None, left, right, center
    )
    end_elements, _ = renderer._apply_fade_out(
        [e for e in elements], angle, 0.0, targets, None, left, right, center
    )

    ordered_starts = (center, left, right)
    expected_mid = [
        (int((s[0] + t.centerx) / 2), int((s[1] + t.centery) / 2))
        for s, t in zip(ordered_starts, targets, strict=False)
    ]
    for idx, center_pos in enumerate(expected_mid, start=0):
        ex_x, ex_y = center_pos
        pos = mid_elements[idx][1]
        assert int(pos[0]) == ex_x
        assert int(pos[1]) == ex_y

    expected_final = [t.center for t in targets]
    for idx, center_pos in enumerate(expected_final, start=0):
        ex_x, ex_y = center_pos
        pos = end_elements[idx][1]
        assert int(pos[0]) == ex_x
        assert int(pos[1]) == ex_y
    pygame.quit()


def test_apply_fade_out_weapon_animation(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    config = IntroConfig()
    assets = IntroAssets.load(config)
    renderer = IntroRenderer(200, 100, config=config, assets=assets)
    ball_positions = ((10.0, 20.0), (190.0, 80.0))

    left, right, center = renderer.compute_positions(1.0)
    elements = renderer._prepare_elements(("A", "B"), 1.0, left, right, center)
    angle, _ = renderer._compute_transform(1.0)

    elements, _ = renderer._apply_fade_out(
        elements, angle, 0.0, None, ball_positions, left, right, center
    )

    for i in range(2):
        pos = elements[i][1]
        ex_x, ex_y = ball_positions[i]
        assert int(pos[0]) == int(ex_x)
        assert int(pos[1]) == int(ex_y)
    pygame.quit()


def test_weapons_in_starts_from_logo_in_final(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pygame.init()
    config = IntroConfig(
        font_path=Path("assets/fonts/FightKickDemoRegular.ttf"),
        logo_path=Path("assets/vs.png"),
        weapon_a_path=Path("assets/ball-a.png"),
        weapon_b_path=Path("assets/ball-b.png"),
    )
    assets = IntroAssets.load(config)
    renderer = IntroRenderer(200, 100, config=config, assets=assets)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    calls: list[tuple[float, float]] = []

    original_rotozoom = pygame.transform.rotozoom

    def tracking_rotozoom(
        img: _pygame.Surface, angle: float, scale: float
    ) -> _pygame.Surface:
        calls.append((angle, scale))
        return original_rotozoom(img, angle, scale)

    monkeypatch.setattr(pygame.transform, "rotozoom", tracking_rotozoom)

    renderer.draw(surface, ("A", "B"), 1.0, IntroState.LOGO_IN)
    logo_calls = calls.copy()
    calls.clear()
    renderer.draw(surface, ("A", "B"), 1.0, IntroState.WEAPONS_IN)

    assert calls == logo_calls
    pygame.quit()


def test_weapons_in_uses_cache_and_progress(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)

    compute_calls: list[float] = []
    original_compute = renderer.compute_positions

    def tracking_compute(
        progress: float,
    ) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        compute_calls.append(progress)
        return original_compute(progress)

    monkeypatch.setattr(renderer, "compute_positions", tracking_compute)

    prepare_calls: list[
        tuple[float, tuple[tuple[float, float], tuple[float, float], tuple[float, float]]]
    ] = []

    def fake_prepare(
        labels: tuple[str, str],
        prog: float,
        left: tuple[float, float],
        right: tuple[float, float],
        center: tuple[float, float],
    ) -> list[tuple[_pygame.Surface, tuple[float, float]]]:
        prepare_calls.append((prog, (left, right, center)))
        return []

    monkeypatch.setattr(renderer, "_prepare_elements", fake_prepare)

    renderer.draw(surface, ("A", "B"), 0.25, IntroState.WEAPONS_IN)

    assert compute_calls == [1.0]
    assert prepare_calls[0][0] == 0.25
    assert prepare_calls[0][1] == original_compute(1.0)
    pygame.quit()


def test_cached_positions_and_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    calls: list[float] = []

    original_compute = renderer.compute_positions

    def tracking(
        progress: float,
    ) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        calls.append(progress)
        return original_compute(progress)

    monkeypatch.setattr(renderer, "compute_positions", tracking)

    renderer.draw(surface, ("A", "B"), 0.0, IntroState.WEAPONS_IN)
    renderer.draw(surface, ("A", "B"), 0.0, IntroState.HOLD)
    renderer.draw(surface, ("A", "B"), 0.0, IntroState.FADE_OUT)

    assert calls == [1.0]

    renderer.reset()
    renderer.draw(surface, ("A", "B"), 0.0, IntroState.HOLD)
    assert calls == [1.0, 1.0]
    pygame.quit()


def test_apply_hold_effect_oscillates(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    config = IntroConfig(hold_float_amplitude=5.0, hold_float_frequency=2.0)
    renderer = IntroRenderer(200, 100, config=config)

    surf = pygame.Surface((10, 10), flags=pygame.SRCALPHA)
    _, _, center = renderer.compute_positions(1.0)
    base_elements = [(surf, center)]
    base_angle, _ = renderer._compute_transform(1.0)

    import math
    import statistics

    times = [i * 0.1 for i in range(int(2 * math.pi / 0.1))]
    angles: list[float] = []
    positions: list[float] = []
    for t in times:
        elems, angle = renderer._apply_hold_effect(base_elements, base_angle, t)
        angles.append(angle)
        positions.append(elems[0][1][1])

    mean_pos = statistics.fmean(positions)
    mean_angle = statistics.fmean(angles)

    assert abs(mean_pos - center[1]) < 0.1
    assert abs(mean_angle - base_angle) < 0.1
    assert max(positions) - min(positions) > 0
    assert max(angles) - min(angles) > 0
    pygame.quit()
