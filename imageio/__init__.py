"""Stub imageio module used for tests when the real dependency is absent."""

from __future__ import annotations

from typing import Any


class _Writer:
    def append_data(self, _frame: Any) -> None:  # pragma: no cover - stub
        return None

    def close(self) -> None:  # pragma: no cover - stub
        return None


def get_writer(*_args: Any, **_kwargs: Any) -> _Writer:  # pragma: no cover - stub
    """Return a dummy writer that discards frames."""
    return _Writer()
