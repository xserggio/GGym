"""Phases measure the outcome, never the intake, and never overstate what the
weigh-ins support."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.models import BodyWeight, Phase



def _weigh(user_id: str, days_ago: int, kg: float) -> None:
    with SessionLocal() as db:
        db.add(
            BodyWeight(
                user_id=user_id,
                measured_on=date.today() - timedelta(days=days_ago),
                weight_kg=kg,
            )
        )
        db.commit()


def _enable(client: TestClient) -> None:
    assert client.patch("/me/phases", json={"enabled": True}).status_code == 200


def _start(client: TestClient, kind: str, rate: float | None = None) -> dict:
    resp = client.post("/me/phases", json={"kind": kind, "target_rate_pct": rate})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _backdate(user_id: str, days: int) -> None:
    """Phases always start today; tests need one that has been running."""
    with SessionLocal() as db:
        phase = db.scalar(select(Phase).where(Phase.user_id == user_id))
        phase.started_on = date.today() - timedelta(days=days)
        db.commit()


def test_feature_is_off_until_enabled(client: TestClient) -> None:
    body = client.get("/me/phases").json()
    assert body["enabled"] is False
    assert body["current"] is None
    # And it cannot be used while off.
    assert client.post("/me/phases", json={"kind": "definicion"}).status_code == 409


def test_rate_is_clamped_to_the_guidelines(client: TestClient) -> None:
    _enable(client)
    # −3 %/week is not a diet, it is a problem; the app caps it.
    body = _start(client, "definicion", -3.0)
    assert body["current"]["target_rate_pct"] == -1.0

    body = _start(client, "superavit", 5.0)
    assert body["current"]["target_rate_pct"] == 0.5


def test_default_rate_when_unspecified(client: TestClient) -> None:
    _enable(client)
    assert _start(client, "definicion")["current"]["target_rate_pct"] == -0.5
    assert _start(client, "superavit")["current"]["target_rate_pct"] == 0.25


def test_no_verdict_without_enough_weigh_ins(client: TestClient, ctx: dict) -> None:
    """Two mornings a few days apart is noise, not a trend."""
    _enable(client)
    _start(client, "definicion")
    _weigh(ctx["user_id"], 3, 70.0)
    _weigh(ctx["user_id"], 1, 69.4)
    status = client.get("/me/phases").json()["current"]["status"]
    assert status["actual_rate_pct"] is None
    assert status["verdict"] == "sin_datos"


def test_on_track_deficit(client: TestClient, ctx: dict) -> None:
    _enable(client)
    _start(client, "definicion", -0.5)
    _backdate(ctx["user_id"], 28)
    # 70 kg losing ~0.35 kg/week is almost exactly −0.5 %/week.
    for i, day in enumerate(range(28, -1, -7)):
        _weigh(ctx["user_id"], day, 70.0 - 0.35 * i)
    status = client.get("/me/phases").json()["current"]["status"]
    assert status["actual_rate_pct"] is not None
    assert abs(status["actual_rate_pct"] + 0.5) < 0.15
    assert status["verdict"] == "en_rumbo"


def test_losing_too_fast_is_flagged(client: TestClient, ctx: dict) -> None:
    _enable(client)
    _start(client, "definicion", -0.5)
    _backdate(ctx["user_id"], 28)
    for i, day in enumerate(range(28, -1, -7)):
        _weigh(ctx["user_id"], day, 70.0 - 1.2 * i)  # ~ −1.7 %/week
    assert client.get("/me/phases").json()["current"]["status"]["verdict"] == "demasiado_rapido"


def test_surplus_not_gaining_is_flagged_as_slow(client: TestClient, ctx: dict) -> None:
    _enable(client)
    _start(client, "superavit", 0.25)
    _backdate(ctx["user_id"], 28)
    for day in range(28, -1, -7):
        _weigh(ctx["user_id"], day, 70.0)  # flat
    assert client.get("/me/phases").json()["current"]["status"]["verdict"] == "demasiado_lento"


def test_long_deficit_is_called_out(client: TestClient, ctx: dict) -> None:
    _enable(client)
    _start(client, "definicion")
    _backdate(ctx["user_id"], 13 * 7)
    assert client.get("/me/phases").json()["current"]["status"]["duration"] == "larga"
    _backdate(ctx["user_id"], 17 * 7)
    assert client.get("/me/phases").json()["current"]["status"]["duration"] == "muy_larga"


def test_starting_a_phase_closes_the_previous_one(client: TestClient, ctx: dict) -> None:
    _enable(client)
    _start(client, "superavit")
    _backdate(ctx["user_id"], 30)
    body = _start(client, "definicion")
    assert body["current"]["kind"] == "definicion"
    assert len(body["history"]) == 1
    assert body["history"][0]["kind"] == "superavit"
    assert body["history"][0]["ended_on"] is not None


def test_disabling_closes_the_running_phase(client: TestClient) -> None:
    _enable(client)
    _start(client, "definicion")
    body = client.patch("/me/phases", json={"enabled": False}).json()
    assert body["enabled"] is False
    assert body["current"] is None


def test_deficit_holds_the_load_instead_of_adding_weight(
    client: TestClient, ctx: dict
) -> None:
    """The behaviour that matters: in a deficit the app stops telling you to add
    weight, because keeping it is the win."""
    from app.models import Session, SetLog
    from app.models.base import utcnow
    from app.models.enums import SessionStatus

    with SessionLocal() as db:
        session = Session(
            user_id=ctx["user_id"],
            routine_day_id=ctx["routine_day_id"],
            status=SessionStatus.completed,
            started_at=utcnow(),
            ended_at=utcnow(),
        )
        db.add(session)
        db.flush()
        for n in range(1, 4):  # every set at the top of the range
            db.add(
                SetLog(
                    session_id=session.id,
                    exercise_id=ctx["exercise_id"],
                    set_number=n,
                    weight_kg=60,
                    reps=8,
                )
            )
        db.commit()

    day_id = ctx["routine_day_id"]
    before = client.get(f"/me/day/{day_id}/suggestions").json()
    press = next(s for s in before if s["exercise_id"] == ctx["exercise_id"])
    assert press["all_at_rep_max"] is True
    assert press["suggested_weight_kg"] == 62.5  # normal progression

    _enable(client)
    _start(client, "definicion")
    after = client.get(f"/me/day/{day_id}/suggestions").json()
    press = next(s for s in after if s["exercise_id"] == ctx["exercise_id"])
    assert press["all_at_rep_max"] is True
    assert press["suggested_weight_kg"] == 60  # held, not pushed


def test_surplus_keeps_normal_progression(client: TestClient, ctx: dict) -> None:
    """Only a deficit holds the load: a surplus should still push weight."""
    from app.models import Session, SetLog
    from app.models.base import utcnow
    from app.models.enums import SessionStatus

    with SessionLocal() as db:
        session = Session(
            user_id=ctx["user_id"],
            routine_day_id=ctx["routine_day_id"],
            status=SessionStatus.completed,
            started_at=utcnow(),
            ended_at=utcnow(),
        )
        db.add(session)
        db.flush()
        for n in range(1, 4):
            db.add(
                SetLog(
                    session_id=session.id,
                    exercise_id=ctx["exercise_id"],
                    set_number=n,
                    weight_kg=60,
                    reps=8,
                )
            )
        db.commit()

    _enable(client)
    _start(client, "superavit")
    rows = client.get(f"/me/day/{ctx['routine_day_id']}/suggestions").json()
    press = next(s for s in rows if s["exercise_id"] == ctx["exercise_id"])
    assert press["suggested_weight_kg"] == 62.5


# --------------------------------------------------------------------------
# Advice: a rate from two questions, and an honest look at the target date.
# --------------------------------------------------------------------------

def _advice(client: TestClient, **body) -> dict:
    resp = client.post("/me/phases/advice", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_surplus_rate_falls_with_training_age(client: TestClient) -> None:
    """Muscle comes quickly at first and slowly later; the target follows."""
    _enable(client)
    rookie = _advice(client, kind="superavit", training_age="menos_1")
    mid = _advice(client, kind="superavit", training_age="1_3")
    veteran = _advice(client, kind="superavit", training_age="mas_3")
    assert rookie["recommended_rate_pct"] > mid["recommended_rate_pct"]
    assert mid["recommended_rate_pct"] > veteran["recommended_rate_pct"]
    assert rookie["rationale"] == "superavit_menos_1"


def test_deficit_rate_slows_as_you_get_leaner(client: TestClient) -> None:
    _enable(client)
    fat = _advice(client, kind="definicion", fat_level="alta")
    lean = _advice(client, kind="definicion", fat_level="baja")
    # Both negative; the leaner one is the gentler (closer to zero) target.
    assert fat["recommended_rate_pct"] < lean["recommended_rate_pct"] < 0


def test_recommendation_never_leaves_the_guidelines(client: TestClient) -> None:
    _enable(client)
    for kind in ("superavit", "definicion", "mantenimiento"):
        for age in ("menos_1", "1_3", "mas_3", None, "basura"):
            for fat in ("alta", "media", "baja", None, "basura"):
                rate = _advice(client, kind=kind, training_age=age, fat_level=fat)[
                    "recommended_rate_pct"
                ]
                limits = next(
                    l for l in client.get("/me/phases").json()["limits"] if l["kind"] == kind
                )
                assert min(limits["min_rate_pct"], limits["max_rate_pct"]) <= rate
                assert rate <= max(limits["min_rate_pct"], limits["max_rate_pct"])


def test_no_feasibility_without_a_weigh_in(client: TestClient) -> None:
    """The check is arithmetic on the current weight; with none, say nothing."""
    _enable(client)
    body = _advice(
        client,
        kind="definicion",
        target_weight_kg=60,
        target_date=str(date.today() + timedelta(days=60)),
    )
    assert body["current_weight_kg"] is None
    assert body["feasibility"] is None


def test_reachable_target_is_called_viable(client: TestClient, ctx: dict) -> None:
    _enable(client)
    _weigh(ctx["user_id"], 0, 70.0)
    # 2 kg in 12 weeks from 70 kg is about −0.24 %/week: comfortable.
    body = _advice(
        client,
        kind="definicion",
        target_weight_kg=68.0,
        target_date=str(date.today() + timedelta(weeks=12)),
    )
    assert body["feasibility"]["verdict"] == "viable"


def test_impossible_target_says_what_is_reachable(client: TestClient, ctx: dict) -> None:
    """The useful answer is not "no": it is the weight that fits the date, and
    the date that fits the weight."""
    _enable(client)
    _weigh(ctx["user_id"], 0, 70.0)
    body = _advice(
        client,
        kind="definicion",
        target_weight_kg=60.0,  # 10 kg in 6 weeks
        target_date=str(date.today() + timedelta(weeks=6)),
    )
    f = body["feasibility"]
    assert f["verdict"] == "muy_exigente"
    assert f["required_rate_pct"] < -2  # far past the −1 %/week cap
    assert 65 < f["reachable_weight_kg"] < 70  # what six weeks actually buys
    assert f["weeks_needed"] > 12  # how long it would really take


def test_target_pointing_the_wrong_way_is_flagged(client: TestClient, ctx: dict) -> None:
    _enable(client)
    _weigh(ctx["user_id"], 0, 70.0)
    body = _advice(
        client,
        kind="definicion",
        target_weight_kg=75.0,  # gaining, in a cut
        target_date=str(date.today() + timedelta(weeks=10)),
    )
    assert body["feasibility"]["verdict"] == "direccion_contraria"


def test_target_weight_is_kept_with_the_phase(client: TestClient) -> None:
    _enable(client)
    when = str(date.today() + timedelta(weeks=10))
    resp = client.post(
        "/me/phases",
        json={"kind": "definicion", "target_weight_kg": 65.0, "target_date": when},
    )
    assert resp.status_code == 200, resp.text
    current = resp.json()["current"]
    assert current["target_weight_kg"] == 65.0
    assert current["target_date"] == when
