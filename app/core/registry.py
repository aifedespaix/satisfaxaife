from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Generic, TypeVar

T = TypeVar("T")


class UnknownWeaponError(KeyError):
    """Raised when a weapon name is not registered."""

    def __init__(self, name: str, available: Sequence[str]) -> None:
        self.name = name
        self.available = sorted(available)
        options = ", ".join(self.available) or "<none>"
        super().__init__(f"Unknown weapon '{name}'. Available weapons: {options}")


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
        try:
            factory = self._factories[name]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise UnknownWeaponError(name, self.names()) from exc
        return factory()

    def factory(self, name: str) -> Callable[[], T]:
        """Return the registered factory for ``name``.

        Parameters
        ----------
        name:
            Identifier of the factory to retrieve.

        Returns
        -------
        Callable[[], T]
            The factory function associated with ``name``.
        """

        return self._factories[name]

    def names(self) -> list[str]:
        return sorted(self._factories)
