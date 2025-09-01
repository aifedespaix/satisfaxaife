"""Utilities for rendering to a resizable window.

This module provides a ``Display`` class that scales a fixed-size surface to
fill the available window while preserving the 9:16 aspect ratio. Black bars are
added as necessary (letterboxing or pillarboxing) to avoid any deformation.

The internal rendering resolution remains constant, typically ``1080×1920`` for
TikTok-style vertical videos. The window can be resized freely or toggled to
fullscreen, and the content will scale accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

try:  # pragma: no cover - optional at import time
    import pygame
except ModuleNotFoundError:  # pragma: no cover - allows tests without pygame
    pygame = None

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    import pygame as _pygame

Size = tuple[int, int]


def calculate_scale(window_size: Size, target_size: Size) -> float:
    """Return the maximal uniform scale factor for *target_size* within *window_size*.

    Parameters
    ----------
    window_size:
        Current width and height of the window.
    target_size:
        Fixed base resolution to fit inside the window.

    Returns
    -------
    float
        Scale factor that preserves aspect ratio.

    Raises
    ------
    ValueError
        If any dimension is non-positive.
    """
    win_w, win_h = window_size
    tgt_w, tgt_h = target_size
    if win_w <= 0 or win_h <= 0 or tgt_w <= 0 or tgt_h <= 0:
        msg = "window and target dimensions must be positive"
        raise ValueError(msg)
    return min(win_w / tgt_w, win_h / tgt_h)


@dataclass(slots=True)
class Display:
    """Resizable window that preserves a fixed aspect ratio.

    Parameters
    ----------
    target_width:
        Width of the internal rendering surface.
    target_height:
        Height of the internal rendering surface.
    """

    target_width: int
    target_height: int
    _is_fullscreen: bool = field(init=False, default=False)
    _flags: int = field(init=False, default=0)
    _window: _pygame.Surface = field(init=False)
    _cached_win_size: Size | None = field(init=False, default=None)
    _scaled_surface: _pygame.Surface | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        if pygame is None:  # pragma: no cover - defensive
            msg = "pygame is required for Display"
            raise RuntimeError(msg)
        self._flags = pygame.RESIZABLE
        info = pygame.display.Info()
        screen_w, screen_h = info.current_w, info.current_h
        scale = calculate_scale((screen_w, screen_h), self.target_size)
        window_size = (
            int(self.target_width * scale),
            int(self.target_height * scale),
        )
        self._window = pygame.display.set_mode(window_size, self._flags)

    @property
    def target_size(self) -> Size:
        """Return the fixed internal rendering size."""
        return (self.target_width, self.target_height)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle resize and fullscreen toggle events."""
        if pygame is None:  # pragma: no cover
            return
        if event.type == pygame.VIDEORESIZE and not self._is_fullscreen:
            self._window = pygame.display.set_mode(event.size, self._flags)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            self.toggle_fullscreen()

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        if pygame is None:  # pragma: no cover
            return
        if self._is_fullscreen:
            self._window = pygame.display.set_mode(self._window.get_size(), self._flags)
        else:
            self._window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self._is_fullscreen = not self._is_fullscreen

    def present(self, surface: pygame.Surface) -> None:
        """Scale *surface* to the window while preserving aspect ratio.

        The expensive ``smoothscale`` operation is only performed when the window
        size changes. Subsequent calls reuse the last scaled surface if the
        dimensions remain constant.
        """
        if pygame is None:  # pragma: no cover
            return
        window = pygame.display.get_surface()
        if window is None:
            return
        win_size = window.get_size()
        if self._scaled_surface is None or self._cached_win_size != win_size:
            scale = calculate_scale(win_size, self.target_size)
            scaled_size = (
                int(self.target_width * scale),
                int(self.target_height * scale),
            )
            self._scaled_surface = pygame.transform.smoothscale(surface, scaled_size)
            self._cached_win_size = win_size
        window.fill((0, 0, 0))
        assert self._scaled_surface is not None  # for type checkers
        scaled_size = self._scaled_surface.get_size()
        offset = (
            (win_size[0] - scaled_size[0]) // 2,
            (win_size[1] - scaled_size[1]) // 2,
        )
        window.blit(self._scaled_surface, offset)
        pygame.display.flip()
