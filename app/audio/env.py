from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator

from .weapons import reset_default_engine


@contextlib.contextmanager
def temporary_sdl_audio_driver(driver: str | None) -> Iterator[None]:
    """Temporarily set the SDL audio driver.

    Parameters
    ----------
    driver:
        Name of the SDL audio driver to use. Use ``"dummy"`` to disable
        playback. When ``None``, the variable is removed.
    """
    previous = os.environ.get("SDL_AUDIODRIVER")
    if driver is None:
        os.environ.pop("SDL_AUDIODRIVER", None)
    else:
        os.environ["SDL_AUDIODRIVER"] = driver
    try:
        yield
    finally:
        reset_default_engine()
        if previous is None:
            os.environ.pop("SDL_AUDIODRIVER", None)
        else:
            os.environ["SDL_AUDIODRIVER"] = previous
