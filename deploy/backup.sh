#!/usr/bin/env bash
# Consistent SQLite snapshot (checkpoints WAL) + offsite copy. The training
# history is irrecoverable if lost (spec §2). Cron example:
#   0 4 * * * RCLONE_REMOTE=gymbackup:gym /opt/gym/deploy/backup.sh >> /var/log/gym-backup.log 2>&1
set -euo pipefail

DB=/opt/gym/data/gym.db
STAMP=$(date +%Y%m%d-%H%M%S)
TMP="/tmp/gym-${STAMP}.db"

sqlite3 "$DB" ".backup '${TMP}'"
gzip -f "$TMP"
ARCHIVE="${TMP}.gz"

REMOTE="${RCLONE_REMOTE:-}"
if [ -n "$REMOTE" ]; then
    rclone copy "$ARCHIVE" "$REMOTE"
    rm -f "$ARCHIVE"
    echo "$(date -Is) backed up to ${REMOTE}"
else
    # No remote configured yet: keep the last 30 locally.
    mkdir -p /opt/gym/backups
    mv "$ARCHIVE" /opt/gym/backups/
    ls -1t /opt/gym/backups/*.gz 2>/dev/null | tail -n +31 | xargs -r rm -f
    echo "$(date -Is) backed up locally (set RCLONE_REMOTE for offsite)"
fi
