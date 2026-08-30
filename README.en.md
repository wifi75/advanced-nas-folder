# Advanced NAS Folder

🇮🇹 [Versione italiana](README.md)

[![Release](https://img.shields.io/github/v/release/wifi75/advanced-nas-folder?label=Release&color=2B7489&logo=github)](https://github.com/wifi75/advanced-nas-folder/releases/latest)
[![Checks](https://img.shields.io/github/actions/workflow/status/wifi75/advanced-nas-folder/controlli.yml?branch=main&label=Checks&logo=githubactions&logoColor=white)](https://github.com/wifi75/advanced-nas-folder/actions/workflows/controlli.yml)
[![Tests](https://img.shields.io/badge/Tests-388-6E9F18?logo=pytest&logoColor=white)](tests)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2B%20systemd-FCC624?logo=linux&logoColor=black)](https://systemd.io)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%200.141-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Frontend](https://img.shields.io/badge/Frontend-Vue%203.5-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Build-Vite%208.2-646CFF?logo=vite&logoColor=white)](https://vite.dev)
[![Languages](https://img.shields.io/badge/Interface-italiano%20%7C%20english-C8467C)](frontend/src/i18n)
[![PWA](https://img.shields.io/badge/App-installable%20(PWA)-5A0FC8?logo=pwa&logoColor=white)](https://web.dev/explore/progressive-web-apps)
[![Database](https://img.shields.io/badge/DB-SQLite%20(WAL)-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/wal.html)
[![Storage](https://img.shields.io/badge/Storage-NFS%20v3%20%7C%20v4-EE0000?logo=redhat&logoColor=white)](https://linux-nfs.org)
[![Web server](https://img.shields.io/badge/Web%20server-Apache%20%7C%20Nginx-D22128?logo=apache&logoColor=white)](https://httpd.apache.org)
[![Security](https://img.shields.io/badge/Privileges-isolated%20root%20agent-4B0082)](docs/PIANO.en.md)
[![License](https://img.shields.io/badge/License-MIT-3DA639?logo=opensourceinitiative&logoColor=white)](LICENSE)

Self-hosted panel that **mounts NFS shares**, **publishes folders with per-subfolder
permissions** and fully replaces FileBrowser — without ever editing a server
configuration file by hand.

> **Status: running on a real server since v0.6.9.** It mounts NFS shares, publishes
> folders with per-user permissions, downloads and uploads files with resume,
> searches, shows previews and records transfers. The first real installation brought
> out a series of errors no test could have caught — permissions on directories
> created by systemd, paths resolved from the current directory — fixed in
> 0.6.7-0.6.9. See [TODO.md](TODO.md).

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

**File management** — browsing, file and folder operations, **resumable** drag&drop
uploads (whole folders included), downloading a folder as a ZIP archive, multiple
selection, recursive search, previews for images, video, audio and PDF, a text
editor, SHA-256 checksums. Multi-user with scopes and granular permissions.

**Downloads** — file delivery is delegated to the web server (`X-Sendfile` on Apache,
`X-Accel-Redirect` on Nginx): Python never touches the content, and resuming
interrupted transfers works natively. A live dashboard shows file, real client
address and outcome.

> The **bytes actually transferred** are known only to the web server, since it is
> the one sending the files: they appear in the dashboard if its access log is
> configured, and stay empty otherwise. A real-time percentage would require routing
> the bytes through Python, giving up native resume: not worth the trade.

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
cd /root
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh
sha256sum install.sh
sudo bash install.sh
```

Add `--dry-run` to see exactly what it would do without applying anything.

The installer shows what it found on the machine — web server, which ports are taken
and by what — and asks which port to use plus a final confirmation. With
`curl … | sudo bash` it asks nothing and decides on its own, because there it has no
terminal to read from.

### Updating and uninstalling

```bash
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/update.sh
sudo bash update.sh
```

`update.sh` puts the new version next to the running one and swaps the two folders
only after the new one has answered: if something goes wrong, the previous one comes
back on its own. `uninstall.sh` removes services and program **keeping the data**; to
remove the database and configuration too it needs `--tutto`.

## Project layout

```
backend/     FastAPI API: configuration, models, endpoints, Alembic migrations
agent/       privileged process, no external dependencies (standard library only)
frontend/    Vue 3 + TypeScript interface, built by CI
deploy/      systemd units, web server templates, installer
docs/        technical plan, dependency versions, operational guides
tests/       API and agent tests, run by CI on every push
```

## Running in development

Python 3.14 and Node 24 are required. One-time setup:

```bash
cd backend && python3.14 -m venv .venv && .venv/bin/pip install -e ".[dev]" && cd ../frontend && npm install
```

Copy `.env.example` to `.env`, set `ANF_ENV=development` and generate the key with
`openssl rand -hex 32`. In development the tables create themselves and an **`admin`**
user with password **`Admin1234`** is created, flagged by the panel until it changes.

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
phone or tablet at the machine's network address, for example
`http://192.168.1.50:5195/pannello/`.

The panel lives under `/pannello/` in development too, because that is where the web
server puts it in production: keeping it at the site root during development would
make paths work locally that break once installed.

> **Careful:** that makes the panel reachable by anyone on the same network, and in
> the initial credentials are `admin`/`Admin1234`.

## Useful commands

| Command | What it does |
|---|---|
| `.venv/bin/ruff check .` | static analysis of backend, agent and tests |
| `.venv/bin/ruff format .` | formatting |
| `.venv/bin/pytest` | the tests, from the project root |
| `cd backend && .venv/bin/mypy app` | type checking, `strict` mode |
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

- [User guide](docs/GUIDA.en.md) — how to use it, from first sign-in to share links
- [Installation](docs/INSTALL.en.md) — complete guide and troubleshooting
- [NFS write access on Synology](docs/synology-nfs-scrittura.en.md)
- [Technical plan](docs/PIANO.en.md) — architecture, data model, rationale
- [Dependency versions](docs/VERSIONI.en.md) — current state and how to check them
- [Privileged agent](agent/README.en.md) — protocol and security rules
- [TODO.md](TODO.md) — state of each phase, and the limits accepted on purpose
- [CHANGELOG.md](CHANGELOG.md) — what changed and why

## License

[MIT](LICENSE) — Copyright © 2026 Tiziano Cassone

---

Designed and developed by Tiziano Cassone
