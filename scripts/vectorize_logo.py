"""Trace a raster logo to SVG with a transparent background (dev tool).

    ../.venv/Scripts/python scripts/vectorize_logo.py <input.png> [output.svg]

The source is a rendered bitmap: it is cropped to its content, the near-white
paper is knocked out to alpha, and the result is traced with vtracer. Colour
tracing keeps the shading of the original; a black-and-white trace would throw
away everything except the silhouette.
"""
from __future__ import annotations

import sys
from pathlib import Path

import vtracer
from PIL import Image

# Anything this close to white is treated as paper, not art. The source is a
# clean render, so a tight threshold avoids eating the light metallic areas.
WHITE_CUTOFF = 238
EDGE_FEATHER = 6  # pixels of margin kept around the artwork


def prepare(src: Path) -> tuple[Path, tuple[int, int]]:
    img = Image.open(src).convert("RGBA")
    pixels = img.load()
    w, h = img.size

    # Knock out the background: a pixel is paper when all channels are bright
    # and nearly equal (grey), which the coloured artwork never is.
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r >= WHITE_CUTOFF and g >= WHITE_CUTOFF and b >= WHITE_CUTOFF:
                pixels[x, y] = (255, 255, 255, 0)

    box = img.getbbox()
    if box:
        box = (
            max(0, box[0] - EDGE_FEATHER),
            max(0, box[1] - EDGE_FEATHER),
            min(w, box[2] + EDGE_FEATHER),
            min(h, box[3] + EDGE_FEATHER),
        )
        img = img.crop(box)

    out = src.with_name(src.stem + "-clean.png")
    img.save(out)
    return out, img.size


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".svg")

    clean, size = prepare(src)
    vtracer.convert_image_to_svg_py(
        str(clean),
        str(dst),
        colormode="color",
        hierarchical="stacked",
        mode="spline",
        filter_speckle=8,     # drop tracing noise from the render's soft edges
        color_precision=6,
        layer_difference=24,  # fewer, flatter colour bands
        corner_threshold=60,
        path_precision=3,
    )
    print(f"cropped to {size[0]}x{size[1]} -> {clean.name}")
    print(f"traced -> {dst}  ({dst.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def flat(src: Path, dst: Path) -> None:
    """Single-colour silhouette. Tracing a glossy render in colour keeps the
    gradients as visible banding; flattening first gives clean, scalable shapes
    that also work on either theme."""
    img = Image.open(src).convert("RGBA")
    mask = Image.new("RGBA", img.size, (255, 255, 255, 255))
    px, mx = img.load(), mask.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            if a > 40 and not (r >= WHITE_CUTOFF and g >= WHITE_CUTOFF and b >= WHITE_CUTOFF):
                mx[x, y] = (0, 0, 0, 255)
    tmp = dst.with_name(dst.stem + "-mask.png")
    mask.convert("RGB").save(tmp)
    vtracer.convert_image_to_svg_py(
        str(tmp), str(dst), colormode="binary", mode="spline",
        filter_speckle=12, corner_threshold=60, path_precision=3,
    )
    tmp.unlink()
    print(f"flat -> {dst} ({dst.stat().st_size / 1024:.0f} KB)")
