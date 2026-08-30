# Technical plan

The architecture reference. The decisions in here were made before writing any
code, and should not be changed without updating `memory.md` as well.

*[Versione italiana](PIANO.md)*

---

## The two problems that shape the project

Everything else follows from how these two are solved.

### Problem 1 — mounting filesystems requires root

A web application exposed to the Internet cannot run as root. The answer is
privilege separation across two processes:

```
Panel ──▶ anf-api ──typed JSON──▶ anf-agent ──▶ systemd units ──▶ mount
         (user anf)  unix socket    (root)        + configtest
```

- `anf-api` never performs a system operation
- `anf-agent` listens **only** on a local Unix socket, mode `0660`, owned by
  `root`, group of the application
- the protocol has a closed set of verbs: `mount.create`, `mount.start`,
  `mount.stop`, `mount.remove`, `mount.status`, `nfs.discover`, `vhost.write`,
  `vhost.remove`, `fstab.list`, `fstab.disable`
- the agent **never builds a shell line**: it receives typed fields and
  substitutes them into a template

Validations the agent must perform:

| Field | Rule |
|---|---|
| Server | valid IP address or hostname |
| Export | absolute path, normalised, no `..` |
| Mount point | forced under `ANF_MOUNT_ROOT`, slug `[a-z0-9-]+` |
| Options | allow-list only |

### Problem 2 — who sends the bytes

Streaming large files through Python saturates the workers and degrades the
whole panel. Delivery has to be delegated to the web server:

1. the client asks the API for the file
2. the API checks authentication and permissions
3. the API answers **empty**, with a header naming the file to serve
4. the web server reads the file from the mount and sends it

| Web server | Header | Requirement |
|---|---|---|
| Apache | `X-Sendfile` | `libapache2-mod-xsendfile` |
| Nginx | `X-Accel-Redirect` | `internal` location |

The decisive advantage is that **resuming comes for free**: `Range`,
`If-Range`, `ETag` and `206` responses are handled natively by the web server.
Routing them through Python would mean rewriting them worse.

A single configuration entry, `ANF_DOWNLOAD_BACKEND`, selects the mode;
`stream` exists only for local development.

---

## Why systemd units and not `/etc/fstab`

`/etc/fstab` is one file shared by the whole system. A wrong line written by a
web panel can stop the server from booting. systemd units are one file per
mount instead: they are added and removed individually, and an invalid unit
stays isolated.

Default options, validated in the field:

```
ro,noatime,vers=3,proto=tcp,soft,timeo=150,retrans=3,nolock,
_netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30,x-systemd.idle-timeout=600
```

| Option | Why |
|---|---|
| `nofail` + `x-systemd.automount` | the server boots even with the NAS off, and mounts on first request |
| `soft`, `timeo=150`, `retrans=3` | with an unreachable NAS the web server gets an error instead of hanging |
| `x-systemd.idle-timeout=600` | unmounts when idle: a NAS reboot leaves no stale handles |
| `nolock` | read-only mount, no need for `rpc-statd`/`rpcbind` |
| `vers=3` | many NAS boxes only expose NFSv2/v3; check with `rpcinfo -p <nas>` |

> If `mount` returns `Protocol not supported`, it is almost always because the
> configuration asks for NFSv4 while the NAS only exposes v3.

---

## Data model

| Entity | Role |
|---|---|
| `User` | account, role, scope, granular permissions |
| `Mount` | NFS share: server, export, mount point, options, requested and effective state |
| `Share` | folder published from a mount, with a subpath |
| `AccessRule` | access rule for a path prefix inside a share |
| `ShareLink` | link with token, expiry, optional password, download limit |
| `Transfer` | download or upload, for the monitoring dashboard |
| `VHost` | publication on the web server: host name, path prefix |
| `Setting` | configuration editable from the panel, not from a file |

---

## Security

- Passwords with **Argon2**; share tokens are 256 random bits, stored hashed
- Authentication with a short-lived JWT plus a revocable refresh token
- Every file access goes through the ACL check: **the mount must never be
  reachable directly from the web server**, otherwise every permission can be
  bypassed
- Every change to the web server configuration is preceded by `apache2ctl
  configtest` / `nginx -t` and followed by automatic rollback on failure
- Behind a reverse proxy, `X-Forwarded-For` is read only from proxies listed as
  trusted; otherwise every client would appear to have the proxy's address
- No real data ends up in the repository: addresses, domains and share names
  live in `.env` and in the database

---

## Stack

Stable versions verified on 29 August 2026.

| Component | Choice | Version |
|---|---|---|
| Backend | FastAPI | 0.141.1 |
| Frontend | Vue 3 + TypeScript | 3.5.33 |
| Build | Vite | 8.0.9 |
| Database | SQLite (WAL mode) | standard library |
| Node (CI only) | LTS | 24.18.1 |
| Agent | Python standard library | — |

**Why SQLite and not PostgreSQL.** The panel has few users and rare writes:
creating a mount, saving a rule, recording a transfer. Reads are frequent,
concurrent writes practically absent — the exact case SQLite is designed for,
and FileBrowser itself uses an embedded database. In exchange, a whole service
disappears from what has to be installed, configured, updated and secured.
**WAL** mode is mandatory: it allows reads during a write, and without it the
panel would stall on every save.

The file lives in `/var/lib/anf/`, owned by the `anf` user, and is included in
the installer's backup.

The privileged agent **uses no external dependencies**, deliberately: it is the
process that runs as root, and every extra library is extra attack surface.

### The frontend is not built on the server

GitHub Actions builds `dist/` and attaches it to the release. The server never
installs Node or `node_modules`: the installation stays light and consumes no
disk space.

---

## Functional scope

Advanced NAS Folder replaces FileBrowser, so it inherits its whole scope:
browsing and multiple views, file operations, resumable upload, archive
download, code editor, previews, search, sharing, multi-user with granular
permissions, themes, multiple languages, API with tokens.

And it adds what FileBrowser does not do: NFS mount management, per-subfolder
permissions, vhost management, live download monitoring.

**Deliberately not replicated:** the built-in shell and custom commands. On a
panel reachable from the Internet those are remote code execution by
definition.

---

## Download progress on the visitor's side

Two levels, stated explicitly because they depend on the browser:

- **Chrome / Edge**: direct chunked writes to disk via the File System Access
  API, real progress, pause and resume, state kept so a download can resume
  even after the page is closed.
- **Firefox / Safari**: that API is not available. It falls back to the
  browser's native download, which still resumes thanks to the server's Range
  support, but progress is shown by the browser rather than by the page.

This is not an implementation limit: it is what browsers expose today.
