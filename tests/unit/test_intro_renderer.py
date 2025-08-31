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


def test_draw_glow_passes(monkeypatch: pytest.MonkeyPatch) -> None:
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

    renderer.draw(surface, ("A", "B"), 1.0, IntroState.HOLD)

    left, right, center = renderer.compute_positions(1.0)
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


def test_draw_overlay_only_logo_in(monkeypatch: pytest.MonkeyPatch) -> None:
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

    renderer.draw(surface, ("A", "B"), 0.5, IntroState.LOGO_IN)
    assert (0, 0) in calls

    calls.clear()
    renderer.draw(surface, ("A", "B"), 0.5, IntroState.WEAPONS_IN)
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


def test_fade_out_interpolates_to_hud(monkeypatch: pytest.MonkeyPatch) -> None:
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
    blits: list[tuple[int, int]] = []

    original_blit = pygame.Surface.blit

    def tracking_blit(
        self: _pygame.Surface,
        source: _pygame.Surface,
        dest: _pygame.Rect | tuple[int, int],
        *args: object,
        **kwargs: object,
    ) -> _pygame.Rect:
        center = dest.center if hasattr(dest, "center") else dest
        blits.append((int(center[0]), int(center[1])))
        return original_blit(self, source, dest, *args, **kwargs)

    monkeypatch.setattr(pygame.Surface, "blit", tracking_blit)

    renderer.draw(surface, labels, 0.5, IntroState.FADE_OUT, targets)
    left_start, right_start, center_start = renderer.compute_positions(1.0)
    ordered_starts = (center_start, left_start, right_start)
    expected_mid = [
        (int((s[0] + t.centerx) / 2), int((s[1] + t.centery) / 2))
        for s, t in zip(ordered_starts, targets, strict=False)
    ]
    for center in expected_mid:
        assert center in blits

    blits.clear()
    renderer.draw(surface, labels, 0.0, IntroState.FADE_OUT, targets)
    expected_final = [t.center for t in targets]
    for center in expected_final:
        assert center in blits
    pygame.quit()
