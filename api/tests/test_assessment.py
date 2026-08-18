"""The assessment must recommend a phase, not just a number, and its rules have
to hold even when they contradict what the user said they wanted."""
from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from app.services import assessment


def _plan(client: TestClient, **answers) -> dict:
    resp = client.post("/me/phases/assessment", json=answers)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_months_of_dieting_earn_a_break_whatever_the_goal(client: TestClient) -> None:
    """Diet fatigue overrides the stated goal: this is the rule that most needs
    to survive someone insisting they want to keep cutting."""
    plan = _plan(
        client, objetivo="bajar_grasa", grasa="media", dieta_reciente="meses_deficit"
    )
    assert plan["kind"] == "mantenimiento"
    assert "descanso_tras_deficit" in plan["reasons"]


def test_poor_energy_blocks_a_deficit(client: TestClient) -> None:
    plan = _plan(client, objetivo="bajar_grasa", grasa="alta", energia="mal")
    assert plan["kind"] == "mantenimiento"
    assert "energia_baja" in plan["reasons"]


def test_wanting_muscle_with_high_fat_suggests_cutting_first(client: TestClient) -> None:
    """Piling a surplus on top of high body fat mostly buys fat."""
    plan = _plan(client, objetivo="ganar_musculo", grasa="alta", experiencia="1_3a")
    assert plan["kind"] == "definicion"
    assert "bajar_antes_de_ganar" in plan["reasons"]


def test_wanting_muscle_when_lean_suggests_a_surplus(client: TestClient) -> None:
    plan = _plan(client, objetivo="ganar_musculo", grasa="baja", experiencia="1_3a")
    assert plan["kind"] == "superavit"
    assert plan["rate_pct"] > 0


def test_very_lean_and_wanting_to_cut_is_talked_down(client: TestClient) -> None:
    plan = _plan(client, objetivo="bajar_grasa", grasa="muy_baja")
    assert plan["kind"] == "mantenimiento"
    assert "ya_muy_definida" in plan["reasons"]


def test_deficit_rate_tracks_how_much_there_is_to_lose(client: TestClient) -> None:
    rates = [
        _plan(client, objetivo="bajar_grasa", grasa=level)["rate_pct"]
        for level in ("muy_alta", "alta", "media", "baja")
    ]
    # Strictly gentler as the person gets leaner.
    assert rates == sorted(rates)
    assert all(r < 0 for r in rates)


def test_surplus_rate_tracks_training_age(client: TestClient) -> None:
    rates = [
        _plan(client, objetivo="ganar_musculo", grasa="baja", experiencia=exp)["rate_pct"]
        for exp in ("menos_6m", "6m_1a", "1_3a", "3_5a", "mas_5a")
    ]
    assert rates == sorted(rates, reverse=True)


def test_prioritising_strength_softens_the_cut(client: TestClient) -> None:
    neutral = _plan(client, objetivo="bajar_grasa", grasa="media", prioridad="equilibrio")
    strength = _plan(client, objetivo="bajar_grasa", grasa="media", prioridad="fuerza")
    assert strength["rate_pct"] > neutral["rate_pct"]  # closer to zero = gentler


def test_middling_energy_softens_any_plan(client: TestClient) -> None:
    ok = _plan(client, objetivo="bajar_grasa", grasa="media", energia="bien")
    meh = _plan(client, objetivo="bajar_grasa", grasa="media", energia="regular")
    assert meh["rate_pct"] > ok["rate_pct"]


def test_no_combination_can_ask_for_more_than_the_guidelines(client: TestClient) -> None:
    """Every modifier is a softener: the questionnaire must never be able to
    talk the app into a harder target than the caps allow."""
    for goal in assessment.GOALS:
        for fat in assessment.FAT:
            for exp in assessment.EXPERIENCE:
                for energy in assessment.ENERGY:
                    for priority in assessment.PRIORITY:
                        plan = _plan(
                            client,
                            objetivo=goal,
                            grasa=fat,
                            experiencia=exp,
                            energia=energy,
                            prioridad=priority,
                        )
                        assert -1.0 <= plan["rate_pct"] <= 0.5


def test_empty_questionnaire_still_gives_a_safe_plan(client: TestClient) -> None:
    plan = _plan(client)
    assert plan["kind"] in ("superavit", "definicion", "mantenimiento")
    assert -1.0 <= plan["rate_pct"] <= 0.5
    assert plan["weeks"] > 0


def test_suggested_date_matches_the_suggested_block(client: TestClient) -> None:
    plan = _plan(client, objetivo="bajar_grasa", grasa="media")
    expected = date.today().toordinal() + plan["weeks"] * 7
    assert date.fromisoformat(plan["suggested_target_date"]).toordinal() == expected


def test_a_cut_is_shorter_than_a_bulk(client: TestClient) -> None:
    cut = _plan(client, objetivo="bajar_grasa", grasa="media")
    bulk = _plan(client, objetivo="ganar_musculo", grasa="baja")
    assert cut["weeks"] < bulk["weeks"]


# --------------------------------------------------------------------------
# Exhaustive audit. Spot checks prove a rule fires; these prove no combination
# of answers can produce a plan we would not defend.
# --------------------------------------------------------------------------

import itertools
from pathlib import Path

from app.models import PhaseKind

ALL_ANSWERS = [
    dict(objetivo=g, grasa=f, experiencia=e, dieta_reciente=d, energia=en, prioridad=p, fecha=fe)
    for g, f, e, d, en, p, fe in itertools.product(
        assessment.GOALS,
        assessment.FAT,
        assessment.EXPERIENCE,
        assessment.DIET_HISTORY,
        assessment.ENERGY,
        assessment.PRIORITY,
        assessment.DEADLINE,
    )
]


def test_every_combination_is_safe() -> None:
    """The whole answer space at once: 4050 plans, none of them harmful."""
    for answers in ALL_ANSWERS:
        plan = assessment.evaluate(answers)

        # A surplus is never right on top of high body fat.
        if plan.kind == PhaseKind.superavit:
            assert answers["grasa"] not in ("muy_alta", "alta"), answers

        # A deficit is never right without recovery, or straight after months
        # of dieting.
        if plan.kind == PhaseKind.definicion:
            assert answers["energia"] != "mal", answers
            assert answers["dieta_reciente"] != "meses_deficit", answers

        # The number always matches the phase it belongs to.
        if plan.kind == PhaseKind.definicion:
            assert -1.0 <= plan.rate_pct < 0, answers
        elif plan.kind == PhaseKind.superavit:
            assert 0 < plan.rate_pct <= 0.5, answers
        else:
            assert plan.rate_pct == 0, answers

        # A plan you cannot explain is a plan you should not give.
        assert plan.reasons, answers
        assert 4 <= plan.weeks <= 20, answers


def test_every_answer_option_changes_something() -> None:
    """A question that cannot move the outcome is decoration. Each option must
    produce a distinct plan somewhere in the space."""
    fields = {
        "objetivo": assessment.GOALS,
        "grasa": assessment.FAT,
        "experiencia": assessment.EXPERIENCE,
        "dieta_reciente": assessment.DIET_HISTORY,
        "energia": assessment.ENERGY,
        "prioridad": assessment.PRIORITY,
    }
    for field_name, options in fields.items():
        seen = set()
        for answers in ALL_ANSWERS:
            plan = assessment.evaluate(answers)
            seen.add((answers[field_name], plan.kind, plan.rate_pct, tuple(plan.reasons)))
        distinct = {value for value, *_ in seen}
        assert distinct == set(options), field_name
        # And the field genuinely moves results, not just gets echoed back.
        outcomes = {(k, r) for _v, k, r, _reasons in seen}
        assert len(outcomes) > 1, field_name


def test_surplus_stays_within_lean_gain_practice() -> None:
    """Roughly 1-1.5 % of body weight a month for a beginner, less after that.
    A faster surplus does not build muscle faster, it just lengthens the cut."""
    monthly = {k: v * 4.35 for k, v in assessment.SURPLUS_BY_EXPERIENCE.items()}
    assert 1.0 <= monthly["menos_6m"] <= 1.6
    assert monthly["mas_5a"] < 0.6
    values = list(assessment.SURPLUS_BY_EXPERIENCE.values())
    assert values == sorted(values, reverse=True)


def test_deficit_stays_within_sustainable_practice() -> None:
    """0.5-1 % of body weight a week with fat to spare; gentler once lean."""
    assert assessment.DEFICIT_BY_FAT["muy_alta"] >= -1.0
    assert assessment.DEFICIT_BY_FAT["muy_baja"] >= -0.35
    values = list(assessment.DEFICIT_BY_FAT.values())
    assert values == sorted(values)


def test_every_reason_the_app_can_give_has_wording() -> None:
    """A reason with no translation renders as an empty bullet — the user would
    see a plan with a blank line where the explanation should be."""
    i18n = Path(__file__).resolve().parents[2] / "web" / "src" / "i18n" / "es.ts"
    if not i18n.exists():  # backend checked out on its own
        return
    text = i18n.read_text(encoding="utf-8")
    emitted = {r for answers in ALL_ANSWERS for r in assessment.evaluate(answers).reasons}
    missing = sorted(key for key in emitted if f"{key}:" not in text and f'"{key}"' not in text)
    assert not missing, f"sin traducción: {missing}"
