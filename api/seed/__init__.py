"""Seed data: shared exercise catalogue and the initial routine (spec §8).

Run from the `api/` directory:

    ../.venv/Scripts/python -m seed            # catalogue + a routine per user
    ../.venv/Scripts/python -m seed --user marta

Idempotent: exercises are keyed by name, routines are skipped for users that
already have one.
"""
