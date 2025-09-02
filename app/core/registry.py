from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Generic, TypeVar

T = TypeVar("T")


class UnknownWeaponError(KeyError):
    """Raised when a weapon name is not registered.

    The message also hints that some weapons rely on optional dependencies and
    shows how to inspect the original import error.
    """

    def __init__(self, name: str, available: Sequence[str]) -> None:
        self.name = name
        self.available = sorted(available)
        options = ", ".join(self.available) or "<none>"
        hint = (
            f"Unknown weapon '{name}'. Available weapons: {options}. "
            "Note: some weapons require optional dependencies. "
            f"Run `python -m app.weapons.{name}` to view the import error."
        )
        super().__init__(hint)


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

        Raises
        ------
        UnknownWeaponError
            If ``name`` is not associated with a registered factory.
        """

        try:
            return self._factories[name]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise UnknownWeaponError(name, self.names()) from exc

    def names(self) -> list[str]:
        return sorted(self._factories)
