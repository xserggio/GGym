"""Initial routine template (spec §8): Upper / Lower / Push / Pull / Legs.

`suggested_dow` is the ISO weekday (1=Monday .. 7=Sunday) and is purely
informational (spec §5.1): the wheel advances on completion, never by date.
Exercise names must match entries in `catalog.CATALOG` exactly.
"""
from __future__ import annotations

from dataclasses import dataclass

ROUTINE_NAME = "Upper / Lower / Push / Pull / Legs"


@dataclass(frozen=True)
class DayExercise:
    name: str          # must exist in CATALOG
    target_sets: int
    rep_min: int
    rep_max: int


@dataclass(frozen=True)
class RoutineDayTemplate:
    position: int
    name: str
    suggested_dow: int
    exercises: tuple[DayExercise, ...]


ROUTINE_DAYS: tuple[RoutineDayTemplate, ...] = (
    RoutineDayTemplate(
        position=1, name="Torso (fuerza)", suggested_dow=1,
        exercises=(
            DayExercise("Press banca", 4, 6, 8),
            DayExercise("Remo con barra", 4, 8, 10),
            DayExercise("Press militar de pie", 3, 8, 8),
            DayExercise("Jalón agarre neutro", 3, 10, 10),
            DayExercise("Elevaciones laterales en polea", 3, 15, 15),
        ),
    ),
    RoutineDayTemplate(
        position=2, name="Pierna (fuerza)", suggested_dow=2,
        exercises=(
            DayExercise("Sentadilla", 4, 5, 8),
            DayExercise("Peso muerto rumano", 3, 8, 10),
            DayExercise("Prensa", 3, 12, 12),
            DayExercise("Curl femoral tumbado", 3, 12, 12),
            DayExercise("Gemelos de pie", 4, 12, 12),
            DayExercise("Rueda abdominal", 3, 10, 10),
        ),
    ),
    RoutineDayTemplate(
        position=3, name="Empuje", suggested_dow=4,
        exercises=(
            DayExercise("Press inclinado con mancuernas", 4, 8, 10),
            DayExercise("Press de hombro en máquina", 3, 10, 10),
            DayExercise("Cruces en polea", 3, 15, 15),
            DayExercise("Elevaciones laterales con mancuernas", 3, 15, 15),
            DayExercise("Tríceps en polea", 3, 12, 12),
        ),
    ),
    RoutineDayTemplate(
        position=4, name="Tirón", suggested_dow=5,
        exercises=(
            DayExercise("Dominadas", 4, 8, 8),
            DayExercise("Remo sentado en polea", 4, 10, 10),
            DayExercise("Remo en máquina con pecho apoyado", 3, 12, 12),
            DayExercise("Face pull", 3, 15, 15),
            DayExercise("Curl con barra Z", 3, 10, 10),
            DayExercise("Curl martillo", 2, 12, 12),
        ),
    ),
    RoutineDayTemplate(
        position=5, name="Pierna (hipertrofia)", suggested_dow=6,
        exercises=(
            DayExercise("Hack squat", 4, 10, 12),
            DayExercise("Hip thrust", 3, 10, 10),
            DayExercise("Sentadilla búlgara", 3, 10, 10),
            DayExercise("Extensión de cuádriceps", 3, 15, 15),
            DayExercise("Curl femoral sentado", 3, 12, 12),
        ),
    ),
)
