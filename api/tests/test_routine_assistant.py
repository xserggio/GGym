"""The routine assistant.

The bar here is not "does it produce findings" — anything can do that. It is
that a routine a competent coach would sign off on draws no complaints, that no
two findings contradict each other, and that nothing it applies can leave the
routine in a state worse than it found it.
"""
from __future__ import annotations

import itertools
from pathlib import Path

import pytest
from sqlalchemy import select

from app.db import SessionLocal
from app.models import (
    Exercise,
    ExercisePreference,
    RoutineDay,
    RoutineDayExercise,
    Session,
    SetLog,
    User,
)
from app.models.enums import SessionStatus
from app.services import (
    muscles,
    routine_apply,
    routine_restructure,
    routine_review,
)


def _user_id(db) -> str:
    return db.scalar(select(User).where(User.username == "tester")).id


BASE = {
    "dias": 5,
    "tiempo": "60",
    "objetivo": "equilibrio",
    "evitar": "nada",
    "prioridad": [],
}


# --- the seeded routine is a good routine --------------------------------


def test_seeded_routine_draws_no_serious_complaints() -> None:
    """The routine shipped with the app was written by hand and is sound. An
    assistant that finds problems everywhere in it is miscalibrated, and would
    teach the user to ignore it."""
    with SessionLocal() as db:
        result = routine_review.review(db, _user_id(db), BASE)
    kinds = [f.kind for f in result.findings]
    # Calves and abs really are light in the seed; nothing else should fire.
    volume_complaints = {
        f.detail.get("muscle") for f in result.findings if f.kind == "volumen_bajo"
    }
    assert volume_complaints <= {"gemelo", "core"}, kinds
    assert "molestia" not in kinds
    assert "sesion_larga" not in kinds


def test_indirect_work_prevents_false_alarms() -> None:
    """Three direct triceps sets look alarming until you count the eleven sets of
    pressing that also train them. Counting patterns alone would give bad advice
    that sounds precise, which is worse than none."""
    with SessionLocal() as db:
        result = routine_review.review(db, _user_id(db), BASE)
    by_muscle = {v.muscle: v for v in result.volumes}
    assert by_muscle["triceps"].weekly_sets >= 10
    assert by_muscle["gluteo"].weekly_sets >= 10
    assert by_muscle["triceps"].band == "efectivo"
    assert by_muscle["gluteo"].band == "efectivo"


def test_rest_findings_only_when_the_routine_overrides_the_catalogue() -> None:
    """A cable fly resting 60s is what a cable fly needs. The app must not
    second-guess its own seed data."""
    with SessionLocal() as db:
        result = routine_review.review(db, _user_id(db), BASE)
        assert not [f for f in result.findings if f.kind == "descanso"]

        heavy = db.scalar(
            select(RoutineDayExercise)
            .join(Exercise, Exercise.id == RoutineDayExercise.exercise_id)
            .where(Exercise.default_rest_s >= 120)
        )
        heavy.rest_s = 45
        db.commit()
        again = routine_review.review(db, _user_id(db), BASE)
    assert [f for f in again.findings if f.kind == "descanso"]


# --- coherence: findings must not fight each other -----------------------


ANSWER_SPACE = [
    {
        "dias": dias,
        "tiempo": tiempo,
        "objetivo": objetivo,
        "evitar": evitar,
        "prioridad": prioridad,
    }
    for dias, tiempo, objetivo, evitar, prioridad in itertools.product(
        routine_review.DAYS_PER_WEEK,
        routine_review.TIME_BUDGET,
        routine_review.GOAL,
        routine_review.AVOID,
        ([], ["gluteo"], ["espalda"], ["brazos"], ["core", "gemelo"]),
    )
]


def test_no_answer_combination_produces_contradictory_advice() -> None:
    """Across every combination of answers: never raise and lower the same
    exercise, never trim a muscle another finding calls low, never touch one
    exercise twice."""
    with SessionLocal() as db:
        user_id = _user_id(db)
        for answers in ANSWER_SPACE:
            result = routine_review.review(db, user_id, answers)
            raised, lowered, touched = set(), set(), []
            low_muscles = {
                f.detail["muscle"]
                for f in result.findings
                if f.kind in ("volumen_bajo", "volumen_prioridad")
            }
            for finding in result.findings:
                action = finding.action
                if action is None or action.rde_id is None:
                    continue
                touched.append(action.rde_id)
                if action.kind == "subir_series":
                    raised.add(action.rde_id)
                if action.kind == "bajar_series":
                    lowered.add(action.rde_id)
            assert not (raised & lowered), answers
            # Two actions on one exercise are fine when they touch different
            # things (swap the bench for a machine *and* give it a set), but
            # never twice the same kind.
            per_kind = [
                (f.action.rde_id, f.action.kind)
                for f in result.findings
                if f.action and f.action.rde_id
            ]
            assert len(per_kind) == len(set(per_kind)), answers
            # Removing an exercise and tweaking it at once reads as nonsense.
            removing = {
                f.action.rde_id
                for f in result.findings
                if f.action and f.action.kind == "quitar"
            }
            assert not (removing & (raised | lowered)), answers
            # Nothing trimmed from a muscle we are asking her to train more.
            rows = {
                r.rde_id: r
                for d in routine_review.load_routine(db, user_id)
                for r in d.rows
            }
            for rde_id in lowered:
                trained = {
                    m
                    for m in low_muscles
                    if rows[rde_id].pattern in muscles.DIRECT_PATTERNS.get(m, ())
                }
                assert not trained, (answers, rde_id, trained)


def test_every_finding_names_something_specific() -> None:
    """'Your back volume is low' is not advice. Every finding must point at a
    session, and every actionable one at an exercise."""
    with SessionLocal() as db:
        user_id = _user_id(db)
        for answers in ANSWER_SPACE:
            for finding in routine_review.review(db, user_id, answers).findings:
                assert finding.severity in routine_review.SEVERITY_ORDER
                assert finding.id and finding.kind
                if finding.action and finding.action.kind != "reordenar":
                    assert finding.detail.get("exercise") or finding.detail.get(
                        "muscle"
                    ), finding


def test_injury_swaps_keep_the_movement_and_its_weight_class() -> None:
    """Something hurting is a reason to change the tool, not to delete the lift.
    Replacing a squat with a leg extension would trade one knee problem for a
    worse one and quietly remove a compound from the routine."""
    with SessionLocal() as db:
        user_id = _user_id(db)
        for avoid in ("rodilla", "hombro", "espalda_baja"):
            result = routine_review.review(db, user_id, {**BASE, "evitar": avoid})
            found = [f for f in result.findings if f.kind == "molestia"]
            assert found, avoid
            rows = {
                r.rde_id: r
                for d in routine_review.load_routine(db, user_id)
                for r in d.rows
            }
            for finding in found:
                original = rows[finding.action.rde_id]
                swap = db.get(Exercise, finding.action.exercise_id)
                assert swap.pattern == original.pattern
                assert swap.equipment in routine_review.GENTLER_EQUIPMENT
                is_isolation = swap.default_rest_s <= routine_review.ISOLATION_REST_S
                assert is_isolation == original.isolation


def test_swaps_carry_enough_to_be_inspected() -> None:
    """A swap the user cannot look at is one she has to take on trust. Every
    substitution must name both exercises by id so the screen can show them, and
    both kits so it can say what actually differs."""
    with SessionLocal() as db:
        user_id = _user_id(db)
        for avoid in ("rodilla", "hombro", "espalda_baja"):
            result = routine_review.review(db, user_id, {**BASE, "evitar": avoid})
            swaps = [
                f
                for f in result.findings
                if f.action and f.action.kind == "sustituir"
            ]
            assert swaps, avoid
            for finding in swaps:
                detail = finding.detail
                for key in (
                    "from_id",
                    "to_id",
                    "pattern",
                    "from_equipment",
                    "to_equipment",
                ):
                    assert detail.get(key), (avoid, key)
                assert detail["from_id"] != detail["to_id"]
                # Same movement, different tool: that is the whole promise.
                assert detail["from_equipment"] != detail["to_equipment"]
                assert db.get(Exercise, detail["to_id"]) is not None


def test_history_findings_stay_quiet_without_history() -> None:
    """An assistant that calls you stalled after two sessions has not earned the
    right to an opinion."""
    with SessionLocal() as db:
        result = routine_review.review(db, _user_id(db), BASE)
    behavioural = {"sustitucion", "nunca_registrado", "estancado", "frecuencia"}
    assert not [f for f in result.findings if f.kind in behavioural]


def test_recurrent_substitution_becomes_a_proposal() -> None:
    """A swap made again and again is the routine being wrong on paper."""
    with SessionLocal() as db:
        user_id = _user_id(db)
        day = db.scalar(select(RoutineDay).where(RoutineDay.position == 1))
        row = db.scalar(
            select(RoutineDayExercise).where(
                RoutineDayExercise.routine_day_id == day.id
            )
        )
        alt = db.scalar(
            select(Exercise).where(
                Exercise.pattern
                == db.get(Exercise, row.exercise_id).pattern,
                Exercise.id != row.exercise_id,
            )
        )
        db.add(
            ExercisePreference(
                user_id=user_id,
                planned_exercise_id=row.exercise_id,
                preferred_exercise_id=alt.id,
                substitution_count=routine_review.RECURRENT_SWAPS,
            )
        )
        # Real sessions have sets in them. Without logs every exercise would
        # look never-performed, which is a different (and louder) finding.
        planned = db.scalars(
            select(RoutineDayExercise).where(
                RoutineDayExercise.routine_day_id == day.id
            )
        ).all()
        for _ in range(routine_review.MIN_SESSIONS_FOR_HABITS):
            session = Session(
                user_id=user_id,
                routine_day_id=day.id,
                status=SessionStatus.completed,
            )
            db.add(session)
            db.flush()
            for planned_row in planned:
                db.add(
                    SetLog(
                        session_id=session.id,
                        exercise_id=planned_row.exercise_id,
                        set_number=1,
                        weight_kg=40,
                        reps=8,
                    )
                )
        db.commit()
        result = routine_review.review(db, user_id, BASE)
    swaps = [f for f in result.findings if f.kind == "sustitucion"]
    assert swaps and swaps[0].action.exercise_id == alt.id


# --- restructuring -------------------------------------------------------


def test_restructure_keeps_every_exercise() -> None:
    """Fewer days must not mean less training: the work is repacked, not thrown
    away."""
    with SessionLocal() as db:
        days = routine_review.load_routine(db, _user_id(db))
    original = {r.exercise_id for d in days for r in d.rows}
    for days_per_week in (2, 3, 4, 6):
        plan = routine_restructure.restructure(days, days_per_week, 90)
        assert plan is not None
        moved = {r.exercise_id for s in plan.sessions for r in s.rows}
        assert moved == original, days_per_week
        assert len(plan.sessions) == days_per_week


def test_restructure_preserves_volume_when_time_allows() -> None:
    """With room on the clock, not a single set is dropped."""
    with SessionLocal() as db:
        days = routine_review.load_routine(db, _user_id(db))
    plan = routine_restructure.restructure(days, 3, 120)
    assert plan is not None
    assert plan.sets_after == plan.sets_before
    assert not plan.trimmed
    assert plan.fits


def test_restructure_says_so_when_the_work_does_not_fit() -> None:
    """Two short sessions cannot hold five sessions' work. Saying it does is the
    one thing this must never do."""
    with SessionLocal() as db:
        days = routine_review.load_routine(db, _user_id(db))
    plan = routine_restructure.restructure(days, 2, 45)
    assert plan is not None
    assert not plan.fits


def test_restructure_trims_from_slack_never_below_the_floor() -> None:
    with SessionLocal() as db:
        days = routine_review.load_routine(db, _user_id(db))
    for days_per_week, budget in itertools.product((2, 3, 4, 6), (45, 60, 75, 90)):
        plan = routine_restructure.restructure(days, days_per_week, budget)
        assert plan is not None
        for session in plan.sessions:
            assert session.rows, (days_per_week, budget)
            for row in session.rows:
                assert row.sets >= routine_restructure.MIN_SETS
        assert plan.sets_after <= plan.sets_before


def test_restructure_puts_compounds_first() -> None:
    with SessionLocal() as db:
        days = routine_review.load_routine(db, _user_id(db))
    plan = routine_restructure.restructure(days, 3, 90)
    assert plan is not None
    for session in plan.sessions:
        seen_isolation = False
        for row in session.rows:
            if row.isolation:
                seen_isolation = True
            else:
                assert not seen_isolation, session.name


def test_restructure_declines_when_the_shape_already_matches() -> None:
    """Five sessions and five days: there is nothing to propose, and inventing a
    change would be noise."""
    with SessionLocal() as db:
        days = routine_review.load_routine(db, _user_id(db))
    assert routine_restructure.restructure(days, len(days), 60) is None


# --- applying ------------------------------------------------------------


def test_apply_snapshots_before_touching_anything(client) -> None:
    body = {"answers": BASE, "accepted": []}
    review = client.post("/me/routine/assistant/review", json=BASE).json()
    accepted = [
        f["id"] for f in review["findings"] if f["action_kind"] == "subir_series"
    ]
    assert accepted
    body["accepted"] = accepted

    before = client.get("/me/routine/profiles").json()
    resp = client.post("/me/routine/assistant/apply", json=body)
    assert resp.status_code == 200, resp.text
    assert resp.json()["changed"] == len(accepted)

    after = client.get("/me/routine/profiles").json()
    assert len(after) == len(before) + 1
    assert any("antes del asistente" in p["name"] for p in after)


def test_apply_only_does_what_was_ticked(client) -> None:
    """The request carries ids, not actions: a client cannot ask for a change
    the assistant did not propose."""
    review = client.post("/me/routine/assistant/review", json=BASE).json()
    ids = [f["id"] for f in review["findings"] if f["action_kind"]]
    resp = client.post(
        "/me/routine/assistant/apply",
        json={"answers": BASE, "accepted": [ids[0], "inventado:xyz"]},
    )
    assert resp.status_code == 200
    assert resp.json()["changed"] == 1


def test_preview_matches_what_apply_does(client) -> None:
    review = client.post("/me/routine/assistant/review", json=BASE).json()
    accepted = [f["id"] for f in review["findings"] if f["action_kind"]]
    body = {"answers": BASE, "accepted": accepted}
    preview = client.post("/me/routine/assistant/preview", json=body).json()
    applied = client.post("/me/routine/assistant/apply", json=body).json()
    assert len(preview) == applied["changed"]
    for change in preview:
        assert change["before"] != change["after"]


def test_applying_repeatedly_converges(client) -> None:
    """Accepting the same advice over and over must reach a routine the
    assistant is happy with, and stop. A rule that nibbles a set at a time would
    never settle, and one that oscillates would undo its own work."""
    seen_totals = []
    for _ in range(6):
        review = client.post("/me/routine/assistant/review", json=BASE).json()
        accepted = [f["id"] for f in review["findings"] if f["action_kind"]]
        if not accepted:
            break
        client.post(
            "/me/routine/assistant/apply",
            json={"answers": BASE, "accepted": accepted},
        )
        routine = client.get("/me/routine").json()
        total = sum(
            e["target_sets"] for d in routine["days"] for e in d["exercises"]
        )
        assert total not in seen_totals, "el asistente está oscilando"
        seen_totals.append(total)
    else:
        pytest.fail("no converge: sigue proponiendo cambios tras 6 rondas")


def test_low_volume_is_fixed_in_one_move(client) -> None:
    """The first suggestion should land the muscle in the band, not leave it
    exactly as short as it was."""
    review = client.post("/me/routine/assistant/review", json=BASE).json()
    lows = [f for f in review["findings"] if f["kind"] == "volumen_bajo"]
    assert lows
    for finding in lows:
        assert finding["detail"]["to"] - finding["detail"]["from"] >= 1


def test_apply_refuses_to_empty_a_session(client) -> None:
    with SessionLocal() as db:
        user_id = _user_id(db)
        day = db.scalar(select(RoutineDay).where(RoutineDay.position == 1))
        rows = db.scalars(
            select(RoutineDayExercise).where(
                RoutineDayExercise.routine_day_id == day.id
            )
        ).all()
        assert not routine_apply._would_empty(db, [])
        assert not routine_apply._would_empty(db, [rows[0].id])
        assert routine_apply._would_empty(db, [r.id for r in rows])


def test_restructure_endpoint_leaves_the_old_routine_intact(client) -> None:
    answers = {**BASE, "dias": 3, "tiempo": "90"}
    before = client.get("/me/routine").json()
    resp = client.post("/me/routine/assistant/restructure", json=answers)
    assert resp.status_code == 200, resp.text
    after = client.get("/me/routine").json()
    assert len(after["days"]) == 3
    profiles = client.get("/me/routine/profiles").json()
    # The previous routine is still there, just not active.
    assert any(p["name"] == before["name"] and not p["active"] for p in profiles)


# --- wording -------------------------------------------------------------


def test_every_finding_kind_has_wording() -> None:
    """A finding with no translation renders as a blank row: the user would see
    the app flag something and refuse to say what."""
    i18n = Path(__file__).resolve().parents[2] / "web" / "src" / "i18n" / "es.ts"
    if not i18n.exists():
        return
    text = i18n.read_text(encoding="utf-8")
    with SessionLocal() as db:
        user_id = _user_id(db)
        kinds = {
            f.kind
            for answers in ANSWER_SPACE
            for f in routine_review.review(db, user_id, answers).findings
        }
    missing = sorted(k for k in kinds if f"{k}:" not in text)
    assert not missing, f"sin traducción: {missing}"


def test_every_muscle_and_band_has_wording() -> None:
    i18n = Path(__file__).resolve().parents[2] / "web" / "src" / "i18n" / "es.ts"
    if not i18n.exists():
        return
    text = i18n.read_text(encoding="utf-8")
    missing = [m for m in muscles.MUSCLES if f"{m}:" not in text]
    assert not missing, f"músculos sin traducción: {missing}"
    for band in ("bajo", "justo", "efectivo", "alto"):
        assert f"{band}:" in text, band
