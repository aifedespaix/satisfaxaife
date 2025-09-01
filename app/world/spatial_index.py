# app/world/spatial_index.py

from __future__ import annotations

from collections.abc import Iterator

import pymunk


class SpatialIndex:
    """Uniform grid spatial index for fast neighbor queries.

    Shapes are tracked but cell assignments are rebuilt on demand.
    The grid uses ``cell_size`` square cells covering the full world.
    """

    def __init__(self, cell_size: float = 256.0) -> None:
        self.cell_size = cell_size
        self._tracked: set[pymunk.Shape] = set()
        self._cells: dict[tuple[int, int], set[pymunk.Shape]] = {}

    def track(self, shape: pymunk.Shape) -> None:
        """Register ``shape`` to be indexed."""
        self._tracked.add(shape)

    def untrack(self, shape: pymunk.Shape) -> None:
        """Remove ``shape`` from the index."""
        self._tracked.discard(shape)
        # Cells will be cleaned on next rebuild.

    def rebuild(self) -> None:
        """Recompute cell membership for all tracked shapes."""
        self._cells.clear()
        for shape in self._tracked:
            for cell in self._iter_shape_cells(shape):
                self._cells.setdefault(cell, set()).add(shape)

    def query(self, shape: pymunk.Shape) -> set[pymunk.Shape]:
        """Return shapes potentially colliding with ``shape``."""
        results: set[pymunk.Shape] = set()
        for cell in self._iter_shape_cells(shape):
            results.update(self._cells.get(cell, ()))
        return results

    # ------------------------------------------------------------------ utils
    def _iter_shape_cells(self, shape: pymunk.Shape) -> Iterator[tuple[int, int]]:
        bb = shape.bb
        min_x = int(bb.left // self.cell_size)
        max_x = int(bb.right // self.cell_size)
        min_y = int(bb.bottom // self.cell_size)
        max_y = int(bb.top // self.cell_size)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                yield (x, y)
