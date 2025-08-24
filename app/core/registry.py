from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """Simple plugin registry."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], T]] = {}

    def register(self, name: str, factory: Callable[[], T]) -> None:
        if name in self._factories:
            msg = f"Factory already registered for {name}"
            raise ValueError(msg)
        self._factories[name] = factory

    def create(self, name: str) -> T:
        return self._factories[name]()

    def names(self) -> list[str]:
        return sorted(self._factories)
