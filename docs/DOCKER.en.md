# Docker installation

🇮🇹 [Versione italiana](DOCKER.md)

Guide to running **anf-api** in a container, as an alternative to the native
systemd service.

---

## What gets containerized, and what doesn't

Only `anf-api`. The privileged agent (`anf-agent`) and the web server
(Apache/Nginx) **stay native services on the host**, not containerized.

This isn't a temporary shortcut: it's the same privilege separation described
in [PIANO.en.md](PIANO.en.md#problem-1--mounting-filesystems-requires-root). The
agent runs as root and generates `.mount`/`.automount` systemd units on the
host — an isolated unit can't damage the rest of the system if it's wrong, a
mount done inside a privileged container can. Moving the agent into a
container would require giving it full access to the host's systemd
(`--privileged` or the D-Bus socket), which protects nothing more than a
native service and only adds a layer of indirection. The web server stays
native for the same reason as Node 2 of the technical plan: it delivers files
with `X-Sendfile` / `X-Accel-Redirect` by reading directly from the host
filesystem, and needs to see the same NFS mount the agent sees.

## Prerequisites

**The native installation must still be done first.** It creates the `anf`
system user, the `anf-agent` service, the web server and the folders
(`/var/lib/anf`, `/srv/nas`, `/run/anf`) — see [INSTALL.en.md](INSTALL.en.md).
Docker replaces **only** the `anf-api` systemd service, not the installer.

| Needed | Why |
|---|---|
| Native installation already done | agent, web server and folders already exist |
| Docker Engine with the Compose plugin | `docker compose version` must respond |

## Installation

Find the UID and GID of the user the installer created:

```bash
id anf
```

Copy the example and fill it in with the values found and the actual paths of
your setup (normally the same as the defaults, unless changed during the
native install):

```bash
cd /var/www/advanced-nas-folder/deploy/docker
cp .env.example .env
nano .env
```

Stop the native service — the container will use the same port:

```bash
sudo systemctl disable --now anf-api
```

Build and start:

```bash
docker compose up -d --build
```

Verify:

```bash
docker compose logs -f anf-api
curl -fsS http://127.0.0.1:$(grep -oP '^ANF_PORT=\K\d+' ../../.env)/api/v1/health
```

The container reads the application configuration from the same root `.env`
used by the native installation — no duplicated secrets.

## Updating

`docker compose build` builds the image from the source code **already on
disk**, in `/var/www/advanced-nas-folder/backend`: on its own it does not
download a newer version of the project. `--pull` only refreshes the Python
base image, not the code — an easy mistake to make, one this guide itself
made the first time it was written.

The code is updated with the same `update.sh` used by the native install,
which as of this version detects on its own that `anf-api` runs in Docker
(because its systemd service is disabled) and does not try to restart it —
it only manages `anf-agent` and syncs the files:

```bash
cd /var/www/advanced-nas-folder && sudo bash update.sh
```

At the end it prints the command to rebuild the container with the code
that just arrived:

```bash
cd deploy/docker && docker compose build --pull && docker compose up -d
```

Database migrations still run on their own at every container start
(`docker-entrypoint.sh`), on top of the ones `update.sh` already applied:
idempotent, running them twice does no harm.

## Why the port stays on `127.0.0.1` only

The process inside the container has to listen on `0.0.0.0`, because in its
own network namespace `127.0.0.1` wouldn't be reachable from the host. The
same security property as the native installation — unreachable from outside
the machine — is guaranteed here by the port mapping in
`docker-compose.yml` (`127.0.0.1:PORT:PORT`), not by the process's internal
bind address. Don't change that mapping to expose the panel directly: go
through the reverse proxy or web server, same as the native installation.

## If shares mounted after startup don't show up in the container

NFS mounts are managed by `systemd` on the host, even after the container has
started — the `automount` unit mounts on first access. The `/srv/nas` volume
is declared with `rslave` propagation specifically so they appear without
restarting anything. If mount propagation isn't shared on your system (rare,
systemd normally defaults to it), restart the container:

```bash
docker compose restart anf-api
```

## Going back to the native service

```bash
docker compose down
sudo systemctl enable --now anf-api
```

## Declared limits, not defects

- **No image for the agent.** See "What gets containerized, and what
  doesn't" above: it's a decision, not a missing piece.
- **No image for the web server.** Same reason: it needs to read files from
  the host filesystem for `X-Sendfile`/`X-Accel-Redirect`.
