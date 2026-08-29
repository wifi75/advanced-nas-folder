# Advanced NAS Folder

🇮🇹 [Versione italiana](README.md)

[![Platform](https://img.shields.io/badge/Platform-Linux%20%2B%20systemd-FCC624?logo=linux&logoColor=black)](https://systemd.io)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%200.141-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Frontend](https://img.shields.io/badge/Frontend-Vue%203.5-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Build-Vite%208.2-646CFF?logo=vite&logoColor=white)](https://vite.dev)
[![Languages](https://img.shields.io/badge/Interface-italiano%20%7C%20english-C8467C)](frontend/src/i18n)
[![Database](https://img.shields.io/badge/DB-SQLite%20(WAL)-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/wal.html)
[![Storage](https://img.shields.io/badge/Storage-NFS%20v3%20%7C%20v4-EE0000?logo=redhat&logoColor=white)](https://linux-nfs.org)
[![Web server](https://img.shields.io/badge/Web%20server-Apache%20%7C%20Nginx-D22128?logo=apache&logoColor=white)](https://httpd.apache.org)
[![Security](https://img.shields.io/badge/Privileges-isolated%20root%20agent-4B0082)](docs/PIANO.md)
[![License](https://img.shields.io/badge/License-MIT-3DA639?logo=opensourceinitiative&logoColor=white)](LICENSE)

Self-hosted panel that **mounts NFS shares**, **publishes folders with per-subfolder
permissions** and fully replaces FileBrowser — without ever editing a server
configuration file by hand.

> **Status: phase 1 complete, phase 2 in progress.** The panel mounts NFS shares from
> the interface, in Italian and English, with a light, dark or automatic theme.
> Folder publishing is still missing. See [TODO.md](TODO.md).

---

## Why it exists

Publishing a NAS folder on the web usually means: mounting it by hand in
`/etc/fstab`, writing an `Alias` in the Apache configuration, and settling for a file
listing with no permissions and no control. If the mount drops, the listing silently
becomes empty and nobody notices.

Advanced NAS Folder brings all of that into a panel: you discover the NAS shares,
mount them with one click, decide who sees what down to the individual subfolder, and
watch who is downloading in real time.

## Features

**NFS mounts** — automatic discovery of the shares the NAS exports, mounting and
unmounting from the panel, options taken from a whitelist, *requested* and *actual*
state always visible side by side. It never touches `/etc/fstab`: it generates systemd
units, one per mount, so a mistake stays isolated and cannot stop the server from
booting.

**Publishing and permissions** — folders published as *shares*, with access rules per
path prefix: public (anonymous), password protected, restricted to signed-in users, or
restricted to specific people. Per-user permissions decide **which user reaches which
folder**, or all of them; an explicit denial overrides the path rule, so you can take a
branch away from one person while it stays open to everyone else.

**File management** — list, grid and gallery views, resumable drag&drop uploads,
folder downloads as archives, a code editor, previews, search, multi-user with scopes
and granular permissions.

**Downloads** — file delivery is delegated to the web server (`X-Sendfile` on Apache,
`X-Accel-Redirect` on Nginx): Python never touches the content, and resuming
interrupted transfers works natively. Real-time dashboard with file, real client IP,
percentage and speed.

## Security

The panel performs privileged operations — mounting filesystems, writing web server
configuration — without ever running as root:

| Process | User | Role |
|---|---|---|
| `anf-api` | `anf`, unprivileged | the web application; never touches the system |
| `anf-agent` | `root` | performs privileged operations, listens only on a local Unix socket |

**Typed commands** travel between them, never shell strings. The agent validates every
request: mount points are confined under `ANF_MOUNT_ROOT`, mount options come from a
whitelist, and every web server configuration change goes through `apache2ctl
configtest` (or `nginx -t`) **before** the reload, rolling back automatically if the
check fails.

Two deliberate choices:

- **Writing to mounts is disabled by default.** It must be enabled explicitly, with a
  risk warning, and also requires the NAS to allow it
  ([guide](docs/synology-nfs-scrittura.en.md)).
- **FileBrowser's built-in shell and custom commands are not replicated.** On a panel
  reachable from the internet they are remote code execution by definition.

## Requirements

- Linux with systemd (developed and tested on Ubuntu 24.04 LTS)
- Apache with `mod_xsendfile`, **or** Nginx
- Python 3.14 or newer — on Ubuntu it installs from the `deadsnakes` PPA,
  **alongside** the system interpreter, which is left untouched. `install.sh` handles
  it.
- No database server: data lives in a SQLite file
- `nfs-common` for NFS mounts

Node.js is **not** required on the server: the frontend is built by CI and shipped
ready-made in the release.

## Installation

Full guide: **[docs/INSTALL.en.md](docs/INSTALL.en.md)**

Download, inspect, run — three separate steps, because the script runs as root:

```bash
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh
sha256sum install.sh
sudo bash install.sh
```

Add `--dry-run` to see exactly what it would do without applying anything.

## Project layout

```
backend/     FastAPI API: configuration, models, endpoints, Alembic migrations
agent/       privileged process, no external dependencies (standard library only)
frontend/    Vue 3 + TypeScript interface, built by CI
deploy/      systemd units, web server templates, installer
docs/        technical plan, dependency versions, operational guides
```

## Running in development

Python 3.14 and Node 24 are required. One-time setup:

```bash
cd backend && python3.14 -m venv .venv && .venv/bin/pip install -e ".[dev]" && cd ../frontend && npm install
```

Copy `.env.example` to `.env`, set `ANF_ENV=development` and generate the key with
`openssl rand -hex 32`. In development the tables create themselves and an **`admin`**
user with password **`admin`** is created, flagged by the panel until it changes.

On Windows a single script starts both services and prints the addresses:

```bash
.\avvia-dev.ps1
```

By hand:

```bash
cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

```bash
cd frontend && npm run dev -- --host
```

With `--host` the services listen on every interface, so you can try the panel from a
phone or tablet at the machine's network address.

> **Careful:** that makes the panel reachable by anyone on the same network, and in
> development the initial credentials are `admin`/`admin`.

## Useful commands

| Command | What it does |
|---|---|
| `cd backend && .venv/bin/ruff check app/` | backend static analysis |
| `cd backend && .venv/bin/mypy app/` | type checking, `strict` mode |
| `cd backend && .venv/bin/alembic upgrade head` | apply migrations |
| `pytest` (from the repository root) | run the test suite |
| `cd frontend && npm run typecheck` | frontend type checking |
| `cd frontend && npm run lint` | ESLint |
| `cd frontend && npm run build` | build `dist/` |

## Configuration

Every setting is documented in [`.env.example`](.env.example). Secrets
(`ANF_SECRET_KEY`) are generated by the installer and written only to `.env`, mode
`0600`. No real data lives in the repository: addresses, domains and share names live
in `.env` and in the database.

## Documentation

- [Installation](docs/INSTALL.en.md) — complete guide and troubleshooting
- [NFS write access on Synology](docs/synology-nfs-scrittura.en.md)
- [Technical plan](docs/PIANO.md) *(Italian)* — architecture, data model, rationale
- [Dependency versions](docs/VERSIONI.md) *(Italian)* — current state and how to check
- [Privileged agent](agent/README.md) *(Italian)* — protocol and security rules
- [TODO.md](TODO.md) · [CHANGELOG.md](CHANGELOG.md)

## License

[MIT](LICENSE) — Copyright © 2026 Tiziano Cassone

---

Designed and developed by Tiziano Cassone
