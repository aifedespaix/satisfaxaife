from __future__ import annotations

from pathlib import Path

from app.video.export import export_tiktok


class _DummyClip:
    def __init__(self, w: int, h: int) -> None:
        self.w = w
        self.h = h
        self.calls: list[tuple[str, object]] = []

    def resize(self, size: tuple[int, int], method: str = "") -> _DummyClip:
        self.calls.append(("resize", size))
        self.w, self.h = size
        return self

    def margin(
        self,
        *,
        left: int = 0,
        right: int = 0,
        top: int = 0,
        bottom: int = 0,
        color: tuple[int, int, int] | None = None,
    ) -> _DummyClip:
        self.calls.append(("margin", (left, right, top, bottom)))
        self.w += left + right
        self.h += top + bottom
        return self

    def fx(self, _func: object, **kwargs: object) -> _DummyClip:
        self.calls.append(("fx", kwargs))
        return self

    def write_videofile(self, out_path: str, **kwargs: object) -> str:
        self.calls.append(("write", out_path, kwargs))
        Path(out_path).write_bytes(b"")
        return out_path


def test_export_tiktok_scales_and_pads(tmp_path: Path) -> None:
    clip = _DummyClip(800, 600)
    out = tmp_path / "out.mp4"
    export_tiktok(clip, str(out), fps=30)

    assert clip.calls[0] == ("resize", (1080, 810))
    assert clip.calls[1] == ("margin", (0, 0, 555, 555))
    assert clip.calls[2][0] == "fx"
    write_call = clip.calls[-1]
    assert write_call[0] == "write"
    params = write_call[2]
    assert params["codec"] == "libx264"
    assert "-pix_fmt" in params["ffmpeg_params"]
    assert out.exists()
