"""Domain enums.

`MovementPattern` is the key to substitutions (spec §5.3): an exercise can only
be swapped for another sharing its pattern.
"""
from __future__ import annotations

import enum


class MovementPattern(str, enum.Enum):
    empuje_horizontal = "empuje_horizontal"
    empuje_vertical = "empuje_vertical"
    tiron_horizontal = "tiron_horizontal"
    tiron_vertical = "tiron_vertical"
    cuadriceps = "cuadriceps"
    cadena_posterior = "cadena_posterior"
    gluteo = "gluteo"
    gemelo = "gemelo"
    deltoides_lateral = "deltoides_lateral"
    triceps = "triceps"
    biceps = "biceps"
    core = "core"
    abduccion = "abduccion"


class Equipment(str, enum.Enum):
    barra = "barra"
    mancuernas = "mancuernas"
    maquina = "maquina"
    polea = "polea"
    peso_corporal = "peso_corporal"
    banda = "banda"


class SessionStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"
