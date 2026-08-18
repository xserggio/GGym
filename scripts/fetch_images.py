"""Populate exercise images (dev tool, run locally).

Source: free-exercise-db (The Unlicense / public domain). Matches our exercise
slugs to that database by keywords, downloads one image, and processes it to the
"tinta sobre cemento" duotone (brief) sized 4:3. Output: web/public/exercises/
<slug>.webp — the frontend loads exercises/<slug>.webp and falls back to the
hatched placeholder when a file is missing. Unmatched exercises simply have no
image.

    ../.venv/Scripts/python scripts/fetch_images.py
"""
from __future__ import annotations

import io
import json
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "web" / "public" / "exercises"
CACHE = REPO / "scripts" / ".fedb_cache.json"
RAW = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main"

INK = (20, 22, 26)
CEMENT = (233, 231, 226)
SIZE = (640, 480)

# slug -> keywords (all must-ish match) used to score free-exercise-db names.
KEYWORDS: dict[str, list[str]] = {
    "press-banca": ["barbell", "bench", "press", "medium"],
    "press-inclinado-mancuernas": ["incline", "dumbbell", "press"],
    "cruces-polea": ["cable", "crossover"],
    "press-banca-mancuernas": ["dumbbell", "bench", "press"],
    "press-pecho-maquina": ["machine", "chest", "press"],
    "fondos-paralelas": ["dips", "chest"],
    "pec-deck": ["butterfly"],
    "press-militar-pie": ["standing", "military", "press"],
    "press-hombro-maquina": ["machine", "shoulder", "press"],
    "press-militar-mancuernas": ["dumbbell", "shoulder", "press"],
    "press-arnold": ["arnold", "press"],
    "elevaciones-laterales-polea": ["cable", "lateral", "raise"],
    "elevaciones-laterales-mancuernas": ["side", "lateral", "raise"],
    "elevaciones-laterales-maquina": ["lateral", "raise", "machine"],
    "remo-barra": ["bent", "over", "barbell", "row"],
    "remo-sentado-polea": ["seated", "cable", "row"],
    "remo-maquina-pecho-apoyado": ["lying", "t-bar", "row"],
    "remo-t": ["t-bar", "row"],
    "remo-mancuerna-unilateral": ["one-arm", "dumbbell", "row"],
    "remo-polea-agarre-ancho": ["seated", "cable", "row"],
    "face-pull": ["face", "pull"],
    "jalon-neutro": ["close-grip", "pulldown"],
    "jalon-agarre-ancho": ["wide-grip", "pulldown"],
    "dominadas": ["pullups"],
    "dominadas-asistidas": ["assisted", "pull-up"],
    "pullover-polea": ["straight-arm", "pulldown"],
    "curl-barra-z": ["ez-bar", "curl"],
    "curl-martillo": ["hammer", "curls"],
    "curl-mancuernas": ["dumbbell", "bicep", "curl"],
    "curl-banco-inclinado": ["incline", "dumbbell", "curl"],
    "curl-polea-baja": ["biceps", "cable", "curl"],
    "triceps-polea": ["triceps", "pushdown"],
    "press-frances": ["lying", "triceps", "extension"],
    "fondos-banco": ["bench", "dips"],
    "extension-triceps-sobre-cabeza": ["overhead", "triceps", "extension", "cable"],
    "sentadilla": ["barbell", "squat"],
    "sentadilla-frontal": ["front", "squat"],
    "sentadilla-multipower": ["smith", "machine", "squat"],
    "sentadilla-goblet": ["goblet", "squat"],
    "sentadilla-bulgara": ["bulgarian", "split", "squat"],
    "prensa": ["leg", "press"],
    "prensa-pies-altos": ["leg", "press"],
    "prensa-unilateral": ["leg", "press"],
    "hack-squat": ["hack", "squat"],
    "extension-cuadriceps": ["leg", "extensions"],
    "zancadas-caminando": ["dumbbell", "lunges"],
    "peso-muerto-rumano": ["romanian", "deadlift"],
    "peso-muerto-rumano-mancuernas": ["romanian", "dumbbell", "deadlift"],
    "buenos-dias": ["good", "morning"],
    "curl-femoral-tumbado": ["lying", "leg", "curls"],
    "curl-femoral-sentado": ["seated", "leg", "curl"],
    "curl-femoral-pie": ["standing", "leg", "curl"],
    "hiperextensiones": ["hyperextensions"],
    "hip-thrust": ["barbell", "hip", "thrust"],
    "hip-thrust-maquina": ["hip", "thrust"],
    "hip-thrust-mancuerna": ["hip", "thrust"],
    "patada-gluteo-polea": ["glute", "kickback"],
    "puente-gluteo": ["glute", "bridge"],
    "pull-through-polea": ["pull", "through"],
    "step-up-cajon": ["dumbbell", "step", "ups"],
    "abductora-maquina": ["thigh", "abductor"],
    # No cable/band hip-abduction in the dataset; the seated abductor machine is
    # the same movement (hip abduction), so reuse it rather than mismatch.
    "abduccion-polea": ["thigh", "abductor"],
    "gemelos-pie": ["standing", "calf", "raises"],
    "gemelos-sentado": ["seated", "calf", "raise"],
    "gemelos-en-prensa": ["calf", "press"],
    "rueda-abdominal": ["ab", "roller"],
    "elevaciones-piernas-colgado": ["hanging", "leg", "raise"],
    "plancha": ["plank"],
    "crunch-polea": ["cable", "crunch"],
}


def load_db() -> list[dict]:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    with urllib.request.urlopen(f"{RAW}/dist/exercises.json", timeout=30) as r:
        data = json.loads(r.read().decode())
    CACHE.write_text(json.dumps(data), encoding="utf-8")
    return data


def best_match(db: list[dict], keywords: list[str]) -> dict | None:
    best, best_score = None, 0
    for ex in db:
        if not ex.get("images"):
            continue
        name = ex["name"].lower()
        score = sum(1 for k in keywords if k in name)
        # On a tie, prefer the shorter (more exact) name: "Plank" over
        # "Push Up to Side Plank", "Butterfly" over a compound variant.
        if score > best_score or (
            score == best_score and best is not None and len(name) < len(best["name"])
        ):
            best, best_score = ex, score
    # require most keywords to match to avoid bad picks
    return best if best_score >= max(1, len(keywords) - 1) else None


def duotone(raw: bytes) -> Image.Image:
    src = Image.open(io.BytesIO(raw)).convert("L")
    src = ImageOps.autocontrast(src, cutoff=2)
    ramp = [
        tuple(round(INK[c] + (CEMENT[c] - INK[c]) * (i / 255)) for c in range(3))
        for i in range(256)
    ]
    channels = [src.point([ramp[i][c] for i in range(256)]) for c in range(3)]
    duo = Image.merge("RGB", channels)
    return ImageOps.fit(duo, SIZE, method=Image.LANCZOS, centering=(0.5, 0.4))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    db = load_db()
    matched = missed = 0
    for slug, keywords in KEYWORDS.items():
        ex = best_match(db, keywords)
        if ex is None:
            print(f"  no match: {slug}")
            missed += 1
            continue
        url = f"{RAW}/exercises/{ex['images'][0]}"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                raw = r.read()
            duotone(raw).save(OUT / f"{slug}.webp", "WEBP", quality=80)
            matched += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  download failed {slug}: {exc}")
            missed += 1
    print(f"\ndone: {matched} images, {missed} without a match/failed")


if __name__ == "__main__":
    main()
