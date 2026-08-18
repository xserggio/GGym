# Deploy

Bare-metal deployment (no Docker) matching the VPS's existing pattern: a
`systemd` service running uvicorn on `127.0.0.1:8100`, served by the existing
nginx under **`/gym/`** — open, protected by the app's own JWT login.

Server layout (`/opt/gym`):

```
/opt/gym/api        backend source (venv installs it editable)
/opt/gym/web/dist   built frontend
/opt/gym/venv       python venv
/opt/gym/data       gym.db (SQLite/WAL)
/opt/gym/.env       production env (GYM_JWT_SECRET generated on first deploy)
/opt/gym/deploy     service unit, nginx include, backup script
```

## Deploy / update

From the repo root:

```bash
cd web && npm run build && cd ..
GYM_SSH_HOST=your-server GYM_SSH_PASSWORD='***' \
    ./.venv/Scripts/python deploy/deploy.py
```

The script uploads the code + dist, creates/updates the venv, runs Alembic
migrations, (re)starts `gym.service`, and inserts an `include` for
`nginx-gym.conf` into the dashboard site — backing it up and running `nginx -t`
before reload (restores on failure). Re-run it to ship updates.

## First-time only: users + seed

No public signup (spec §2). Create the two profiles and seed the catalogue +
routine on the server:

```bash
cd /opt/gym/api
set -a && . /opt/gym/.env && set +a
/opt/gym/venv/bin/python -m app.cli create-user --username marta --name "Marta"
/opt/gym/venv/bin/python -m app.cli create-user --username diego --name "Diego"
/opt/gym/venv/bin/python -m seed
```

Then open `https://<your-server>/gym/`.

## Backups

`deploy/backup.sh` takes a consistent SQLite snapshot and copies it offsite with
rclone (falls back to keeping the last 30 locally if `RCLONE_REMOTE` is unset).
Configure an rclone remote once, then add a cron entry:

```bash
rclone config                       # create a remote, e.g. "gymbackup"
crontab -e
# 0 4 * * * RCLONE_REMOTE=gymbackup:gym /opt/gym/deploy/backup.sh >> /var/log/gym-backup.log 2>&1
```

## Service

```bash
systemctl status gym
journalctl -u gym -f
```
