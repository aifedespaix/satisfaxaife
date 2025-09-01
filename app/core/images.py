from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

SUPPORTED_IMAGE_SUFFIXES: tuple[str, ...] = (".png", ".jpg", ".jpeg")


def sanitize_image(path: Path) -> None:
    """Validate and repair an image file in-place.

    The function ensures that the image at ``path`` can be loaded. If the
    image contains orientation metadata, it is normalized using
    :func:`ImageOps.exif_transpose`. The result is converted to ``RGBA`` and
    written back to ``path``.

    Parameters
    ----------
    path:
        Path to the image file to sanitize.

    Raises
    ------
    ValueError
        If the file cannot be opened as an image.
    """

    try:
        with Image.open(path) as img:
            ImageOps.exif_transpose(img).convert("RGBA").save(path)
    except (UnidentifiedImageError, OSError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid image file: {path}") from exc


def sanitize_images(directory: Path) -> list[Path]:
    """Sanitize all image files in ``directory`` recursively.

    Parameters
    ----------
    directory:
        Root directory to scan for images. Only files with extensions defined
        in :data:`SUPPORTED_IMAGE_SUFFIXES` are processed.

    Returns
    -------
    list[pathlib.Path]
        Paths of the images that were successfully sanitized.
    """

    sanitized: list[Path] = []
    for path in directory.rglob("*"):
        if path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            continue
        try:
            sanitize_image(path)
        except ValueError:
            continue
        sanitized.append(path)
    return sanitized
