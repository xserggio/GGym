#!/usr/bin/env python3
"""Deploy 'Registro de fuerza' to the VPS (bare-metal: systemd + nginx).

Serves the app under /gym/ behind the existing nginx, open (protected by the
app's own JWT login). SSH credentials come from the environment, never the repo:

    GYM_SSH_HOST=your-server GYM_SSH_PASSWORD=... \
        python deploy/deploy.py

Prerequisites: run `npm run build` in web/ first (this uploads web/dist).
Idempotent and safe to re-run. The nginx site is backed up and validated with
`nginx -t` before reload; on failure the backup is restored.
"""
from __future__ import annotations

import os
import posixpath
import sys
import time
from pathlib import Path

import paramiko

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/opt/gym"
NGINX_SITE = "/etc/nginx/sites-enabled/dashboard"
NGINX_INCLUDE = "/opt/gym/deploy/nginx-gym.conf"
NGINX_ANCHOR = "client_max_body_size 6g;"

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", "data", ".venv", "node_modules"}
EXCLUDE_SUFFIX = (".db", ".db-wal", ".db-shm", ".pyc")


def connect() -> paramiko.SSHClient:
    host = os.environ.get("GYM_SSH_HOST", "your-server")
    user = os.environ.get("GYM_SSH_USER", "root")
    password = os.environ.get("GYM_SSH_PASSWORD")
    if not password:
        sys.exit("error: set GYM_SSH_PASSWORD (and optionally GYM_SSH_HOST)")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=22, username=user, password=password, timeout=30)
    return client


def run(client: paramiko.SSHClient, cmd: str, check: bool = True) -> tuple[int, str]:
    _, out, err = client.exec_command(cmd, timeout=180)
    rc = out.channel.recv_exit_status()
    text = out.read().decode(errors="replace") + err.read().decode(errors="replace")
    if text.strip():
        print(text.strip())
    if check and rc != 0:
        raise RuntimeError(f"command failed ({rc}): {cmd}")
    return rc, text


def sftp_mkdirs(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts = remote_dir.strip("/").split("/")
    cur = ""
    for p in parts:
        cur += "/" + p
        try:
            sftp.stat(cur)
        except FileNotFoundError:
            sftp.mkdir(cur)


def upload_tree(sftp: paramiko.SFTPClient, local: Path, remote: str) -> int:
    count = 0
    sftp_mkdirs(sftp, remote)
    for entry in sorted(local.iterdir()):
        if entry.name in EXCLUDE_DIRS:
            continue
        rpath = posixpath.join(remote, entry.name)
        if entry.is_dir():
            count += upload_tree(sftp, entry, rpath)
        elif not entry.name.endswith(EXCLUDE_SUFFIX):
            sftp.put(str(entry), rpath)
            count += 1
    return count


def patch_nginx(client: paramiko.SSHClient, sftp: paramiko.SFTPClient) -> None:
    with sftp.open(NGINX_SITE, "r") as fh:
        content = fh.read().decode()
    if NGINX_INCLUDE in content:
        print("nginx: include already present")
    else:
        include_line = f"    include {NGINX_INCLUDE};"
        lines = content.splitlines()
        out: list[str] = []
        inserted = False
        for line in lines:
            out.append(line)
            if not inserted and NGINX_ANCHOR in line:
                out.append("")
                out.append(include_line)
                inserted = True
        if not inserted:
            raise RuntimeError(f"nginx anchor not found: {NGINX_ANCHOR!r}")
        backup = f"{NGINX_SITE}.bak-{int(time.time())}"
        run(client, f"cp {NGINX_SITE} {backup}")
        with sftp.open(NGINX_SITE, "w") as fh:
            fh.write("\n".join(out) + "\n")
        rc, _ = run(client, "nginx -t", check=False)
        if rc != 0:
            run(client, f"cp {backup} {NGINX_SITE}")
            raise RuntimeError("nginx -t failed; restored backup, no reload")
        print("nginx: include inserted, config valid")
    run(client, "systemctl reload nginx")


def main() -> int:
    dist = REPO / "web" / "dist"
    if not dist.exists():
        sys.exit("error: web/dist not found — run `npm run build` in web/ first")

    client = connect()
    sftp = client.open_sftp()

    print("== upload ==")
    sftp_mkdirs(sftp, REMOTE_ROOT)
    n = upload_tree(sftp, REPO / "api", f"{REMOTE_ROOT}/api")
    # Wipe the previous build so stale hashed assets don't accumulate.
    run(client, f"rm -rf {REMOTE_ROOT}/web/dist")
    n += upload_tree(sftp, dist, f"{REMOTE_ROOT}/web/dist")
    sftp_mkdirs(sftp, f"{REMOTE_ROOT}/deploy")
    for name in ("gym.service", "nginx-gym.conf", "backup.sh", ".env.example"):
        sftp.put(str(REPO / "deploy" / name), f"{REMOTE_ROOT}/deploy/{name}")
        n += 1
    print(f"uploaded {n} files")

    print("== backend (venv, deps, migrations, service) ==")
    run(client, f"mkdir -p {REMOTE_ROOT}/data")
    run(client, f"test -d {REMOTE_ROOT}/venv || python3 -m venv {REMOTE_ROOT}/venv")
    run(client, f"{REMOTE_ROOT}/venv/bin/pip install -q --upgrade pip")
    run(client, f"{REMOTE_ROOT}/venv/bin/pip install -q -e {REMOTE_ROOT}/api")
    run(
        client,
        f"test -f {REMOTE_ROOT}/.env || "
        f"(cp {REMOTE_ROOT}/deploy/.env.example {REMOTE_ROOT}/.env && "
        f"sed -i \"s/CHANGE_ME/$(openssl rand -hex 32)/\" {REMOTE_ROOT}/.env)",
    )
    run(
        client,
        f"cd {REMOTE_ROOT}/api && set -a && . {REMOTE_ROOT}/.env && set +a && "
        f"{REMOTE_ROOT}/venv/bin/alembic upgrade head",
    )
    run(client, f"cp {REMOTE_ROOT}/deploy/gym.service /etc/systemd/system/gym.service")
    run(client, "systemctl daemon-reload")
    run(client, "systemctl enable gym >/dev/null 2>&1 || true")
    run(client, "systemctl restart gym")
    run(client, "command -v sqlite3 >/dev/null || apt-get install -y -q sqlite3", check=False)
    run(client, f"chmod +x {REMOTE_ROOT}/deploy/backup.sh")

    print("== nginx ==")
    patch_nginx(client, sftp)

    print("== health ==")
    run(client, "sleep 1; curl -s -o /dev/null -w 'backend %{http_code}\\n' http://127.0.0.1:8100/health", check=False)

    sftp.close()
    client.close()
    print("\ndone. Next: create users + seed (see deploy/README.md).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
