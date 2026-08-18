"""Phase assessment: seven questions in, a defensible plan out.

This decides *which* phase to run, not only how fast — which is the question
people actually have. Every answer changes something; a question that could not
move the outcome would be theatre.

It is deliberately deterministic. The same answers always give the same plan and
the same written reasons, so the advice can be shown, argued with and audited.
The reasoning is the standard one a decent coach applies:

* months of dieting earn a break before anything else;
* poor sleep and energy make a deficit a bad trade;
* stacking a surplus on top of high body fat mostly buys fat;
* very lean people lose muscle when they push a deficit further.

Nothing here is a medical judgement, and none of it needs food intake.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..models import PhaseKind
from . import phases

# --- answer vocabularies -------------------------------------------------
GOALS = ("ganar_musculo", "bajar_grasa", "mantener_rendir")
FAT = ("muy_alta", "alta", "media", "baja", "muy_baja")
EXPERIENCE = ("menos_6m", "6m_1a", "1_3a", "3_5a", "mas_5a")
DIET_HISTORY = ("meses_deficit", "vengo_de_volumen", "nada_especial")
DEADLINE = ("hay_fecha", "sin_prisa")
PRIORITY = ("fuerza", "estetica", "equilibrio")
ENERGY = ("bien", "regular", "mal")

# Deficit rate by how much fat there is to lose. With plenty in reserve the body
# draws on fat happily; the leaner you get, the more of the same deficit comes
# out of muscle instead.
DEFICIT_BY_FAT = {
    "muy_alta": -1.00,
    "alta": -0.80,
    "media": -0.60,
    "baja": -0.40,
    "muy_baja": -0.30,
}

# Surplus rate by training age. Muscle arrives quickly at the start and very
# slowly later; past that point the extra food is just fat. Calibrated against
# lean-gain practice of roughly 1-1.5% of body weight a month for a beginner,
# halving from there: a faster surplus does not build muscle faster, it just
# lengthens the cut that follows.
SURPLUS_BY_EXPERIENCE = {
    "menos_6m": 0.35,
    "6m_1a": 0.28,
    "1_3a": 0.20,
    "3_5a": 0.14,
    "mas_5a": 0.10,
}

# Suggested block length. A deficit is a sprint, a surplus a long walk, and a
# break after dieting only works if it lasts long enough to matter.
WEEKS = {
    PhaseKind.definicion: 12,
    PhaseKind.superavit: 16,
    PhaseKind.mantenimiento: 6,
}


@dataclass
class Plan:
    kind: PhaseKind
    rate_pct: float
    weeks: int
    # Keys the UI turns into sentences; ordered most important first.
    reasons: list[str] = field(default_factory=list)


def _pick_kind(answers: dict[str, str], reasons: list[str]) -> PhaseKind:
    goal = answers.get("objetivo")
    fat = answers.get("grasa")
    diet = answers.get("dieta_reciente")
    energy = answers.get("energia")

    # Recovery first: these override the stated goal, and the app says why.
    if diet == "meses_deficit":
        reasons.append("descanso_tras_deficit")
        return PhaseKind.mantenimiento
    if energy == "mal":
        # What poor recovery cannot pay for is a deficit, not a surplus. If the
        # goal is muscle and nothing else argues for cutting, a gentle surplus
        # still goes ahead — just slower, and saying why.
        if goal == "ganar_musculo" and fat not in ("muy_alta", "alta") and diet != "vengo_de_volumen":
            reasons.append("energia_baja_volumen")
            return PhaseKind.superavit
        reasons.append("energia_baja")
        return PhaseKind.mantenimiento

    if goal == "ganar_musculo":
        if fat in ("muy_alta", "alta"):
            # Adding food on top of high body fat mostly adds more fat; losing
            # some first makes the later surplus work far better.
            reasons.append("bajar_antes_de_ganar")
            return PhaseKind.definicion
        if diet == "vengo_de_volumen" and fat == "media":
            # Stacking a second surplus on the last one is how a lean bulk turns
            # into a long one: take the gains down before adding more.
            reasons.append("vienes_de_volumen")
            return PhaseKind.definicion
        reasons.append("objetivo_ganar")
        return PhaseKind.superavit

    if goal == "bajar_grasa":
        if fat == "muy_baja":
            reasons.append("ya_muy_definida")
            return PhaseKind.mantenimiento
        reasons.append("objetivo_bajar")
        return PhaseKind.definicion

    reasons.append("objetivo_mantener")
    return PhaseKind.mantenimiento


def _pick_rate(kind: PhaseKind, answers: dict[str, str], reasons: list[str]) -> float:
    if kind == PhaseKind.mantenimiento:
        return 0.0

    if kind == PhaseKind.definicion:
        fat = answers.get("grasa") if answers.get("grasa") in DEFICIT_BY_FAT else "media"
        rate = DEFICIT_BY_FAT[fat]
        reasons.append("ritmo_por_grasa_" + fat)
    else:
        exp = (
            answers.get("experiencia")
            if answers.get("experiencia") in SURPLUS_BY_EXPERIENCE
            else "1_3a"
        )
        rate = SURPLUS_BY_EXPERIENCE[exp]
        reasons.append("ritmo_por_experiencia_" + exp)

    # Softening factors. They only ever make the plan gentler: nothing in the
    # questionnaire can talk the app into a harder target than the guidelines.
    if answers.get("energia") == "regular":
        rate *= 0.8
        reasons.append("suavizado_energia")
    elif answers.get("energia") == "mal":
        rate *= 0.6
        reasons.append("suavizado_energia_mal")
    if kind == PhaseKind.definicion and answers.get("prioridad") == "fuerza":
        rate *= 0.75
        reasons.append("suavizado_fuerza")
    if kind == PhaseKind.superavit and answers.get("prioridad") == "estetica":
        rate *= 0.8
        reasons.append("suavizado_estetica")

    return round(phases.clamp_rate(kind, rate), 2)


def evaluate(answers: dict[str, str]) -> Plan:
    reasons: list[str] = []
    kind = _pick_kind(answers, reasons)
    rate = _pick_rate(kind, answers, reasons)

    weeks = WEEKS[kind]
    if kind == PhaseKind.mantenimiento and answers.get("dieta_reciente") != "meses_deficit":
        weeks = 8  # a plain maintenance block, not a recovery one
    if answers.get("fecha") == "hay_fecha" and kind != PhaseKind.mantenimiento:
        reasons.append("con_fecha")

    return Plan(kind=kind, rate_pct=rate, weeks=weeks, reasons=reasons)
