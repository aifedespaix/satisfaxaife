from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.core.images import sanitize_image, sanitize_images


def _create_image(path: Path, *, orientation: int | None = None) -> None:
    image = Image.new("RGB", (2, 1), color=(255, 0, 0))
    if orientation is not None:
        exif = image.getexif()
        exif[274] = orientation  # Orientation tag
        image.save(path, exif=exif)
    else:
        image.save(path)


def test_sanitize_image_transposes_and_converts(tmp_path: Path) -> None:
    img_path = tmp_path / "test.png"
    _create_image(img_path, orientation=3)

    sanitize_image(img_path)

    with Image.open(img_path) as img:
        assert img.mode == "RGBA"
        assert 274 not in img.getexif()


def test_sanitize_image_raises_on_invalid_file(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.png"
    bad_path.write_text("not an image")

    with pytest.raises(ValueError):
        sanitize_image(bad_path)


def test_sanitize_images_scans_directory(tmp_path: Path) -> None:
    img1 = tmp_path / "a.png"
    img2 = tmp_path / "b.jpg"
    _create_image(img1)
    _create_image(img2)

    sanitized = sanitize_images(tmp_path)

    assert set(sanitized) == {img1, img2}
    for path in sanitized:
        with Image.open(path) as img:
            assert img.mode == "RGBA"
