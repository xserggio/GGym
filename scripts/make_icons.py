"""App icons, built from the brand mark.

The mark itself arrived as a metallic PNG. Gradients and bevels are the first
thing to turn to mud at 48px on a launcher, so everything here is flat: the
alpha channel is used purely as a stencil and filled with one solid colour. What
survives at icon size is the silhouette, and the silhouette is the brand.

The mark is 1.65:1 — wide for a square tile. Scaling it by width and centring it
is deliberate: a wide shape shrunk to fit a square by its diagonal would end up
too small to read at all.

Android adaptive icons are two layers (a background the launcher may mask and a
foreground it may parallax), so the foreground keeps its content inside the 66%
safe zone. `icon.png` is the flattened fallback for launchers and stores that
still want one square image.

Usage:  python scripts/make_icons.py [--preview]
Then:   cd web && npx capacitor-assets generate --android
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "brand" / "ggym-gemini-transparente.png"
OUT = ROOT / "web" / "assets"

# The wordmark sits below a clear band of empty rows; the symbol is what goes on
# an icon (letters are unreadable at this size anyway).
SYMBOL_BOTTOM = 552

INK = (20, 22, 26, 255)  # --ink
PAPER = (247, 246, 243, 255)  # --paper
# A brighter blue than the app's --blue on purpose. #2b5fd9 sits at 3.2:1
# against ink: fine as a button fill under white text, but as a *figure* on a
# near-black tile it goes dim and the thin bars close up at 48px. This one holds
# 6.7:1 and still reads as the same blue rather than a washed-out pastel.
BLUE = (77, 159, 255, 255)

# Share of the tile the mark spans, by width.
#
# capacitor-assets already insets this image by 16.7% when it writes the
# adaptive layers, which lands it exactly on the 72dp visible viewport — so this
# span is measured against what the launcher actually shows, not against the
# full canvas. Holding back another 38% on top of that (as an earlier version
# did) just makes the mark look lost inside its own circle.
FOREGROUND_SPAN = 0.80
FLAT_SPAN = 0.72
SIZE = 1024


def symbol_mask() -> Image.Image:
    """The mark as a stencil: alpha only, cropped tight, metal discarded."""
    art = Image.open(SOURCE).convert("RGBA").crop((0, 0, Image.open(SOURCE).width, SYMBOL_BOTTOM))
    alpha = art.split()[3]
    box = alpha.getbbox()
    return alpha.crop(box)


def tile(background: tuple, foreground: tuple, span: float, size: int = SIZE) -> Image.Image:
    mask = symbol_mask()
    width = round(size * span)
    height = round(width * mask.height / mask.width)
    mask = mask.resize((width, height), Image.LANCZOS)

    canvas = Image.new("RGBA", (size, size), background)
    ink = Image.new("RGBA", mask.size, foreground)
    canvas.paste(ink, ((size - width) // 2, (size - height) // 2), mask)
    return canvas


def write() -> None:
    """Capacitor's sources, plus the PWA icons — installing from the browser and
    installing the APK have to put the same thing on the home screen."""
    OUT.mkdir(parents=True, exist_ok=True)
    tile((0, 0, 0, 0), BLUE, FOREGROUND_SPAN).save(OUT / "icon-foreground.png")
    Image.new("RGBA", (SIZE, SIZE), INK).save(OUT / "icon-background.png")
    tile(INK, BLUE, FLAT_SPAN).save(OUT / "icon.png")

    public = ROOT / "web" / "public"
    for size in (192, 512):
        tile(INK, BLUE, FLAT_SPAN, size).save(public / f"icon-{size}.png")
    # Maskable icons get cropped to whatever shape the launcher likes, so the
    # mark shrinks to the safe zone and the ink runs to the edges.
    tile(INK, BLUE, FOREGROUND_SPAN, 512).save(public / "icon-maskable-512.png")
    print(f"escritos {OUT} (3) y {public} (3)")


CANDIDATES = {
    "a-tinta": (INK, PAPER),
    "b-azul": ((43, 95, 217, 255), PAPER),
    "c-papel": (PAPER, INK),
    "d-azul-sobre-tinta": (INK, (91, 141, 238, 255)),
}


def preview() -> Path:
    """A sheet at real sizes. An icon is judged at 48px, not at 1024."""
    sizes = (192, 96, 48)
    pad, label = 24, 34
    width = pad + len(CANDIDATES) * (192 + pad)
    height = label + pad + sum(s + pad for s in sizes)
    sheet = Image.new("RGB", (width, height), (233, 231, 226))
    for col, (name, (bg, fg)) in enumerate(CANDIDATES.items()):
        x = pad + col * (192 + pad)
        y = label + pad
        for size in sizes:
            sheet.paste(tile(bg, fg, FLAT_SPAN, size).convert("RGB"), (x, y))
            y += size + pad
    path = ROOT / "brand" / "icon-candidatos.png"
    sheet.save(path)
    print(f"candidatos: {list(CANDIDATES)} -> {path}")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    if args.preview:
        preview()
    else:
        write()
