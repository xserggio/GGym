"""SQLAlchemy models. Importing this package registers every table on
`Base.metadata`, which Alembic autogenerate relies on."""
from __future__ import annotations

from .base import Base
from .enums import Equipment, MovementPattern, SessionStatus
from .exercise import Exercise
from .preference import ExercisePreference
from .routine import Routine, RoutineDay, RoutineDayExercise
from .session import Session, SetLog
from .state import UserState
from .sync import SyncEvent
from .tracking import BodyWeight, TreadmillSession
from .user import User

__all__ = [
    "Base",
    "Equipment",
    "MovementPattern",
    "SessionStatus",
    "Exercise",
    "ExercisePreference",
    "Routine",
    "RoutineDay",
    "RoutineDayExercise",
    "Session",
    "SetLog",
    "UserState",
    "SyncEvent",
    "BodyWeight",
    "TreadmillSession",
    "User",
]
