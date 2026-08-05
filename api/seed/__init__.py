"""Seed the shared exercise catalogue and the initial routine from the canonical
JSON file (`routine.json`). Run from the `api/` directory:

    ../.venv/Scripts/python -m seed             # bundled routine.json, all users
    ../.venv/Scripts/python -m seed --user sergio

Idempotent: exercises are upserted by their stable slug id; a user keeps any
routine they already have. See `seed/load.py`.
"""
