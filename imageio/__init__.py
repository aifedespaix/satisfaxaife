"""Stub imageio module used for tests when the real dependency is absent."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import numpy as np


class _Writer:
    def append_data(self, _frame: Any) -> None:  # pragma: no cover - stub
        return None

    def close(self) -> None:  # pragma: no cover - stub
        return None


def get_writer(*_args: Any, **_kwargs: Any) -> _Writer:  # pragma: no cover - stub
    """Return a dummy writer that discards frames."""
    return _Writer()


class _Reader:
    def get_data(self, _index: int) -> np.ndarray:  # pragma: no cover - stub
        return np.zeros((1, 1, 3), dtype=np.uint8)

    def __enter__(self) -> _Reader:  # pragma: no cover - stub
        return self

    def __exit__(self, *_exc: object) -> None:  # pragma: no cover - stub
        return None


def get_reader(*_args: Any, **_kwargs: Any) -> _Reader:  # pragma: no cover - stub
    """Return a dummy reader that yields a single black frame."""
    return _Reader()


class FormatError(RuntimeError):
    """Stub ``imageio`` format error."""


core = SimpleNamespace(FormatError=FormatError)
