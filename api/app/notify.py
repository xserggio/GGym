"""Send any due training reminders. Driven by cron (spec §7.6).

A PWA cannot be trusted to fire a timer with the screen off, so the schedule
lives here. Safe to run often — sending is idempotent per user per day:

    */10 * * * * /opt/gym/venv/bin/python -m app.notify
"""
from __future__ import annotations

import logging

from .db import SessionLocal
from .services import notifications


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    with SessionLocal() as db:
        sent = notifications.run_due(db)
    if sent:
        logging.info("sent %d push notification(s)", sent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
