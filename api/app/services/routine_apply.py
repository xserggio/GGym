"""Turning accepted findings into edits, reversibly.

Two rules govern everything here.

The first is that nothing is applied that the user did not tick. The client
sends back only the ids it accepted; the actions themselves are recomputed from
the database, never taken from the request. A client cannot ask this module to
make a change the assistant did not propose, so a stale or tampered-with payload
can at worst re-apply an old suggestion, never invent a new one.

The second is that every run is undoable. Before the first edit the current
routine is copied to a dated profile, so going back is one tap in the profiles
screen rather than an act of memory. A restructure goes further and builds a new
profile outright, leaving the old routine untouched and simply not active.

Order matters: sets, reps and rests first, then swaps, then removals, then
reordering. Removing rows first would invalidate ids the later actions still
need, and reordering first would be undone by the removals.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from ..models import Exercise, Routine, RoutineDay, RoutineDayExercise
from . import routine_edit, routine_profiles, routine_restructure, routine_review

# Applied last, because they change the shape of what came before.
ORDER = {
    "subir_series": 0,
    "bajar_series": 0,
    "cambiar_reps": 0,
    "cambiar_descanso": 0,
    "sustituir": 1,
    "quitar": 2,
    "reordenar": 3,
}


@dataclass
class Change:
    """One line of the diff shown before anything is written."""

    kind: str
    day: str
    exercise: str
    before: str
    after: str


def _snapshot_name(today: date) -> str:
    return f"antes del asistente · {today.strftime('%d/%m/%Y')}"


def preview(
    db: OrmSession, user_id: str, answers: dict, accepted: list[str]
) -> list[Change]:
    """What applying those findings would do, in the user's terms. Runs the same
    review the apply will run, so the preview cannot drift from the result."""
    review = routine_review.review(db, user_id, answers)
    chosen = [f for f in review.findings if f.id in set(accepted) and f.action]
    days = {d.day_id: d for d in routine_review.load_routine(db, user_id)}
    rows = {r.rde_id: (r, d) for d in days.values() for r in d.rows}

    out: list[Change] = []
    for finding in chosen:
        action = finding.action
        assert action is not None
        if action.kind == "reordenar":
            day = days.get(action.day_id or "")
            out.append(
                Change(
                    kind=action.kind,
                    day=day.name if day else "",
                    exercise="",
                    before=", ".join(r.name for r in day.rows) if day else "",
                    after=", ".join(
                        rows[i][0].name for i in action.order if i in rows
                    ),
                )
            )
            continue
        found = rows.get(action.rde_id or "")
        if found is None:
            continue
        row, day = found
        if action.kind in ("subir_series", "bajar_series"):
            out.append(
                Change(action.kind, day.name, row.name, f"{row.sets} series", f"{action.sets} series")
            )
        elif action.kind == "cambiar_reps":
            out.append(
                Change(
                    action.kind,
                    day.name,
                    row.name,
                    f"{row.rep_min}-{row.rep_max} reps",
                    f"{action.rep_min}-{action.rep_max} reps",
                )
            )
        elif action.kind == "cambiar_descanso":
            out.append(
                Change(action.kind, day.name, row.name, f"{row.rest_s}s", f"{action.rest_s}s")
            )
        elif action.kind == "sustituir":
            out.append(
                Change(action.kind, day.name, row.name, row.name, action.exercise_name or "")
            )
        elif action.kind == "quitar":
            out.append(Change(action.kind, day.name, row.name, row.name, "—"))
    return out


def _would_empty(
    db: OrmSession, removals: list[str]
) -> bool:
    """A session with no exercises is not a session. Refuse the whole batch
    rather than silently keeping one row the user asked to remove."""
    by_day: dict[str, int] = {}
    for rde_id in removals:
        row = db.get(RoutineDayExercise, rde_id)
        if row is not None:
            by_day[row.routine_day_id] = by_day.get(row.routine_day_id, 0) + 1
    for day_id, count in by_day.items():
        total = len(
            db.scalars(
                select(RoutineDayExercise).where(
                    RoutineDayExercise.routine_day_id == day_id
                )
            ).all()
        )
        if total - count <= 0:
            return True
    return False


def apply(
    db: OrmSession, user_id: str, answers: dict, accepted: list[str], today: date
) -> tuple[int, str | None]:
    """Apply the accepted findings. Returns (changes made, snapshot name)."""
    review = routine_review.review(db, user_id, answers)
    chosen = [f for f in review.findings if f.id in set(accepted) and f.action]
    if not chosen:
        return 0, None

    removals = [f.action.rde_id for f in chosen if f.action and f.action.kind == "quitar"]
    if _would_empty(db, [r for r in removals if r]):
        from fastapi import HTTPException, status

        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "those removals would leave a session empty",
        )

    routine_id = routine_edit.active_routine_id(db, user_id)
    source = db.get(Routine, routine_id)
    assert source is not None
    snapshot = _snapshot_name(today)
    routine_profiles.copy_routine(db, source, snapshot)

    chosen.sort(key=lambda f: ORDER.get(f.action.kind if f.action else "", 9))
    done = 0
    for finding in chosen:
        action = finding.action
        assert action is not None
        if action.kind in ("subir_series", "bajar_series"):
            row = db.get(RoutineDayExercise, action.rde_id)
            if row is not None and action.sets:
                row.target_sets = action.sets
                done += 1
        elif action.kind == "cambiar_reps":
            row = db.get(RoutineDayExercise, action.rde_id)
            if row is not None and action.rep_min and action.rep_max:
                row.rep_min, row.rep_max = action.rep_min, action.rep_max
                done += 1
        elif action.kind == "cambiar_descanso":
            row = db.get(RoutineDayExercise, action.rde_id)
            if row is not None:
                row.rest_s = action.rest_s
                done += 1
        elif action.kind == "sustituir":
            row = db.get(RoutineDayExercise, action.rde_id)
            if row is not None and db.get(Exercise, action.exercise_id) is not None:
                row.exercise_id = action.exercise_id
                done += 1
        elif action.kind == "quitar":
            if db.get(RoutineDayExercise, action.rde_id) is not None:
                routine_edit.remove_exercise(db, user_id, action.rde_id)
                done += 1
        elif action.kind == "reordenar":
            present = [
                i
                for i in action.order
                if db.get(RoutineDayExercise, i) is not None
            ]
            if action.day_id and present:
                routine_edit.reorder_exercises(db, user_id, action.day_id, present)
                done += 1
    db.flush()
    return done, snapshot


def apply_restructure(
    db: OrmSession, user_id: str, answers: dict, today: date
) -> str:
    """Build the redistributed routine as a *new* profile and activate it.

    Nothing is edited in place: the routine she has stays exactly as it is, just
    no longer active. That makes going back a matter of switching profile, which
    is the safest possible undo for a change this large.
    """
    from fastapi import HTTPException, status

    days = routine_review.load_routine(db, user_id)
    days_per_week = int(answers.get("dias") or 4)
    budget = int(answers.get("tiempo") or 60)
    plan = routine_restructure.restructure(days, days_per_week, budget)
    if plan is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "the routine already has that shape"
        )

    name = f"Rutina {days_per_week} días · {today.strftime('%d/%m/%Y')}"
    routine = Routine(user_id=user_id, name=name, active=False)
    db.add(routine)
    db.flush()
    for position, session in enumerate(plan.sessions, start=1):
        day = RoutineDay(
            routine_id=routine.id,
            position=position,
            name=session.name,
            suggested_dow=None,
        )
        db.add(day)
        db.flush()
        for index, row in enumerate(session.rows):
            db.add(
                RoutineDayExercise(
                    routine_day_id=day.id,
                    exercise_id=row.exercise_id,
                    order_index=index,
                    target_sets=row.sets,
                    rep_min=row.rep_min,
                    rep_max=row.rep_max,
                    rest_s=row.rest_s,
                )
            )
    db.flush()
    routine_profiles.activate(db, user_id, routine.id)
    return name
