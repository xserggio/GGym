"""The Inicio dashboard reports measured work only: no invented calories when
there is no body weight, and no streak counters (spec §7.2)."""
from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models import BodyWeight, Session, SetLog, TreadmillSession, UserState
from app.models.base import utcnow
from app.models.enums import SessionStatus
from app.services import treadmill


def _train(user_id: str, day_id: str, exercise_id: str, minutes: int = 45) -> None:
    ended = utcnow()
    with SessionLocal() as db:
        session = Session(
            user_id=user_id,
            routine_day_id=day_id,
            status=SessionStatus.completed,
            started_at=ended - timedelta(minutes=minutes),
            ended_at=ended,
        )
        db.add(session)
        db.flush()
        for _ in range(3):
            db.add(
                SetLog(
                    session_id=session.id,
                    exercise_id=exercise_id,
                    set_number=1,
                    weight_kg=60,
                    reps=10,
                )
            )
        db.commit()


def test_empty_week_reports_zeroes_not_nulls(client: TestClient) -> None:
    body = client.get("/me/home").json()
    assert body["week_sessions"] == 0
    assert body["week_sets"] == 0
    assert body["week_volume_kg"] == 0
    assert body["next_position"] == 1
    assert body["next_exercises"] > 0


def test_week_totals_count_only_logged_work(client: TestClient, ctx: dict) -> None:
    _train(ctx["user_id"], ctx["routine_day_id"], ctx["exercise_id"])
    body = client.get("/me/home").json()
    assert body["week_sessions"] == 1
    assert body["week_sets"] == 3
    assert body["week_volume_kg"] == 60 * 10 * 3
    assert body["week_strength_seconds"] == 45 * 60


def test_calories_are_omitted_without_a_body_weight(client: TestClient, ctx: dict) -> None:
    _train(ctx["user_id"], ctx["routine_day_id"], ctx["exercise_id"])
    assert client.get("/me/home").json()["week_kcal"] is None


def test_calories_use_the_recorded_weight(client: TestClient, ctx: dict) -> None:
    _train(ctx["user_id"], ctx["routine_day_id"], ctx["exercise_id"], minutes=60)
    with SessionLocal() as db:
        db.add(
            BodyWeight(
                user_id=ctx["user_id"], measured_on=utcnow().date(), weight_kg=80
            )
        )
        db.commit()
    # 5.0 MET x 80 kg x 1 h = 400 kcal, no treadmill yet.
    assert client.get("/me/home").json()["week_kcal"] == 400


def test_treadmill_history_and_weekly_total(client: TestClient, ctx: dict) -> None:
    with SessionLocal() as db:
        db.add(
            TreadmillSession(
                user_id=ctx["user_id"],
                started_at=utcnow() - timedelta(hours=1),
                ended_at=utcnow(),
                duration_s=1200,
            )
        )
        db.add(
            BodyWeight(
                user_id=ctx["user_id"], measured_on=utcnow().date(), weight_kg=80
            )
        )
        db.commit()

    body = client.get("/me/treadmill").json()
    assert body["week_seconds"] == 1200
    assert len(body["entries"]) == 1
    # 20 min x 0.053 x 80 kg = 84.8 -> 85
    assert body["entries"][0]["kcal"] == 85
    assert body["week_kcal"] == 85
    assert client.get("/me/home").json()["week_treadmill_seconds"] == 1200


def test_treadmill_kcal_needs_a_weight(client: TestClient, ctx: dict) -> None:
    with SessionLocal() as db:
        db.add(
            TreadmillSession(
                user_id=ctx["user_id"], started_at=utcnow(), duration_s=600
            )
        )
        db.commit()
    body = client.get("/me/treadmill").json()
    assert body["entries"][0]["kcal"] is None
    assert body["week_kcal"] is None


def test_old_work_falls_out_of_the_window(client: TestClient, ctx: dict) -> None:
    with SessionLocal() as db:
        old = utcnow() - timedelta(days=9)
        db.add(
            Session(
                user_id=ctx["user_id"],
                routine_day_id=ctx["routine_day_id"],
                status=SessionStatus.completed,
                started_at=old - timedelta(minutes=40),
                ended_at=old,
            )
        )
        db.commit()
    body = client.get("/me/home").json()
    assert body["week_sessions"] == 0
    # ...but it is still the last session overall.
    assert body["last_session_at"] is not None


def test_kcal_formula_matches_the_spec() -> None:
    """min x 0.053 x kg (spec §5.5)."""
    assert treadmill.kcal_for(30 * 60, 70) == round(30 * 0.053 * 70)
    assert treadmill.kcal_for(600, None) is None


def test_period_widens_the_window(client: TestClient, ctx: dict) -> None:
    """Work older than 7 days is invisible by default but counts in 30d/all."""
    with SessionLocal() as db:
        old = utcnow() - timedelta(days=20)
        session = Session(
            user_id=ctx["user_id"],
            routine_day_id=ctx["routine_day_id"],
            status=SessionStatus.completed,
            started_at=old - timedelta(minutes=30),
            ended_at=old,
        )
        db.add(session)
        db.flush()
        db.add(
            SetLog(
                session_id=session.id,
                exercise_id=ctx["exercise_id"],
                set_number=1,
                weight_kg=50,
                reps=10,
                # Volume is windowed on when the set was logged, not on the
                # session date, so backdate it too or it counts as today's.
                created_at=old,
            )
        )
        db.commit()

    assert client.get("/me/home", params={"period": "7d"}).json()["week_sessions"] == 0
    assert client.get("/me/home", params={"period": "30d"}).json()["week_sessions"] == 1
    assert client.get("/me/home", params={"period": "all"}).json()["week_sets"] == 1
    # The balance chart follows the same window.
    assert client.get("/me/home", params={"period": "7d"}).json()["volume"] == []
    assert len(client.get("/me/home", params={"period": "all"}).json()["volume"]) == 1


def test_unknown_period_is_rejected(client: TestClient) -> None:
    assert client.get("/me/home", params={"period": "decade"}).status_code == 422


def test_milestones_cover_weight_time_and_treadmill(client: TestClient, ctx: dict) -> None:
    _train(ctx["user_id"], ctx["routine_day_id"], ctx["exercise_id"], minutes=50)
    with SessionLocal() as db:
        db.add(
            TreadmillSession(
                user_id=ctx["user_id"], started_at=utcnow(), duration_s=1800
            )
        )
        db.commit()

    kinds = {m["kind"]: m for m in client.get("/me/home").json()["milestones"]}
    assert kinds["heaviest_set"]["value"] == 60
    assert kinds["heaviest_set"]["unit"] == "kg"
    assert "Press banca" in kinds["heaviest_set"]["detail"]
    assert kinds["longest_session"]["value"] == 50
    assert kinds["best_session_volume"]["value"] == 60 * 10 * 3
    assert kinds["longest_run"]["value"] == 30


def test_milestones_are_empty_without_data(client: TestClient) -> None:
    assert client.get("/me/home").json()["milestones"] == []


def test_activity_includes_rest_days_as_gaps(client: TestClient, ctx: dict) -> None:
    """The gaps are the point: a chart of only trained days hides the misses."""
    _train(ctx["user_id"], ctx["routine_day_id"], ctx["exercise_id"])
    activity = client.get("/me/home", params={"period": "7d"}).json()["activity"]
    assert len(activity) == 7
    trained = [p for p in activity if p["sessions"] > 0]
    assert len(trained) == 1
    assert trained[0]["volume_kg"] == 60 * 10 * 3
    assert trained[0]["bucket"] == activity[-1]["bucket"]  # today, last bucket
    assert sum(p["sessions"] for p in activity) == 1


def test_activity_buckets_by_month_for_long_windows(client: TestClient, ctx: dict) -> None:
    _train(ctx["user_id"], ctx["routine_day_id"], ctx["exercise_id"])
    activity = client.get("/me/home", params={"period": "365d"}).json()["activity"]
    assert len(activity) == 13  # 12 months back plus the current one
    assert all(p["bucket"].endswith("-01") for p in activity)
    assert sum(p["sessions"] for p in activity) == 1


def test_reset_user_clears_history_and_restores_the_routine(ctx: dict) -> None:
    """A factory reset must leave a seeded-looking account, not an empty one."""
    from app.cli.__main__ import main as cli_main
    from app.models import Routine, User
    from sqlalchemy import select

    _train(ctx["user_id"], ctx["routine_day_id"], ctx["exercise_id"])
    with SessionLocal() as db:
        user = db.get(User, ctx["user_id"])
        db.add(BodyWeight(user_id=user.id, measured_on=utcnow().date(), weight_kg=80))
        db.commit()
        username = user.username

    assert cli_main(["reset-user", "--username", username, "--yes"]) == 0

    with SessionLocal() as db:
        assert db.scalars(select(Session).where(Session.user_id == ctx["user_id"])).all() == []
        assert db.scalars(select(BodyWeight).where(BodyWeight.user_id == ctx["user_id"])).all() == []
        routines = db.scalars(
            select(Routine).where(Routine.user_id == ctx["user_id"])
        ).all()
        # The pristine snapshot plus one fresh active copy derived from it.
        assert len(routines) == 2
        active = [r for r in routines if r.active]
        assert len(active) == 1 and not active[0].is_original
        state = db.get(UserState, ctx["user_id"])
        assert state.next_position == 1 and state.last_session_at is None
        assert state.routine_id == active[0].id


def test_previous_window_is_the_comparison(client: TestClient, ctx: dict) -> None:
    """Progress is measured against your own recent form, not a made-up target."""
    with SessionLocal() as db:
        old = utcnow() - timedelta(days=9)  # inside the previous 7-day window
        session = Session(
            user_id=ctx["user_id"],
            routine_day_id=ctx["routine_day_id"],
            status=SessionStatus.completed,
            started_at=old - timedelta(minutes=30),
            ended_at=old,
        )
        db.add(session)
        db.flush()
        db.add(
            SetLog(
                session_id=session.id,
                exercise_id=ctx["exercise_id"],
                set_number=1,
                weight_kg=40,
                reps=10,
                created_at=old,
            )
        )
        db.commit()
    _train(ctx["user_id"], ctx["routine_day_id"], ctx["exercise_id"])  # this week

    body = client.get("/me/home", params={"period": "7d"}).json()
    assert body["week_sessions"] == 1
    assert body["prev_sessions"] == 1
    assert body["prev_volume_kg"] == 40 * 10
    assert body["week_volume_kg"] == 60 * 10 * 3


def test_no_comparison_for_all_time(client: TestClient) -> None:
    body = client.get("/me/home", params={"period": "all"}).json()
    assert body["prev_sessions"] is None
    assert body["prev_volume_kg"] is None
