# Installation

🇮🇹 [Versione italiana](INSTALL.md)

Complete guide to installing Advanced NAS Folder on a Linux server.

---

## Before you start

| Required | Why |
|---|---|
| **Linux with systemd** | mounts and services are systemd units |
| **Apache** *or* **Nginx** | they deliver files instead of the application |
| **Python 3.14 or newer** | the code uses syntax introduced in that version |
| **`nfs-common`** | to mount the shares |
| **root** access | the installer creates users, services and mount points |

On Apache you also need **`mod_xsendfile`**, without which downloads come back
empty: **the installer installs and enables it**, together with `mod_remoteip` and the
proxy modules. There is nothing to prepare by hand.

**Node.js is not needed on the server**: the frontend is built by CI and shipped
ready-made in the release.

Developed and verified on **Ubuntu 24.04 LTS**. On other distributions the installer
needs adapting: it uses `apt-get` and the `deadsnakes` PPA.

### The NAS

Check two things on the NAS before installing:

1. **The folder is exported to the server's address.** On Synology:
   *Control Panel → Shared Folder → Edit → NFS Permissions*.
2. **Which NFS version it offers.** Many NAS devices only offer v3, and asking for v4
   makes the mount fail with an unhelpful message (`Protocol not supported`). From the
   server:

   ```bash
   rpcinfo -p NAS_ADDRESS | grep nfs
   ```

   If only `2` and `3` show up, you will use NFSv3. The panel detects this on its own
   and disables the versions that are not available.

To enable **writing**, see the [dedicated guide](synology-nfs-scrittura.en.md): it
must be enabled both on the NAS and in the panel, and getting the *squash* setting
wrong makes uploaded files unmanageable from File Station.

---

## Installation

The installer is downloaded, inspected and run in **three separate steps**: it runs as
root, so it deserves to be read first.

```bash
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh
```

```bash
sha256sum install.sh
```

```bash
sudo bash install.sh
```

Messages appear in the system language. To force it: `--lang en` or `--lingua it`.

### Try it dry first

Recommended on a server that hosts other sites: it prints every command without
running any of them.

```bash
sudo bash install.sh --dry-run
```

### Options

| Option | What it does |
|---|---|
| `--dry-run` | shows what it would do, applying nothing |
| `--web apache` \| `nginx` | forces the web server instead of detecting it |
| `--port 8110` | internal API port. Without it, the first free one from 8100 is picked |
| `--lang en` \| `it` | message language |
| `--source /path` | installs from a local directory instead of the release |
| `--uninstall` | removes services and program |

---

### The port is not fixed

The API listens on a local port, behind the web server. With no instructions
the installer starts at **8100** and goes up until it finds a free one, saying
which it picked:

```
==> Looking for a free port for the API
  !  Port 8100 is already taken: using 8101 instead
```

On a machine already hosting other applications that is the normal case, not
an exception. With `--port` you pick a specific one instead: if that one is
taken the installer **stops** rather than moving on its own — whoever named it
had a reason, and finding the panel somewhere else would be worse than an
error.

The chosen number goes into `.env` (`ANF_PORT`) and into the web server
configuration, which stay consistent with each other.

---

## What the installer does, step by step

1. **Checks prerequisites**: root, Linux, systemd.
2. **Installs missing packages**: `curl`, `nfs-common`, `openssl`.
3. **Installs Python 3.14** from the `deadsnakes` PPA if missing. It is installed
   **alongside** the system interpreter, which is left untouched: moving `python3`
   would break the operating system and the other applications on the machine.
4. **Detects Apache or Nginx**, and on Apache enables `mod_xsendfile`, `mod_remoteip`
   and the proxy modules.
5. **Creates the `anf` system user**, with no login shell.
6. **Prepares the directories**:

   | Path | Contents |
   |---|---|
   | `/var/www/advanced-nas-folder` | program |
   | `/var/lib/anf` | SQLite database |
   | `/srv/nas` | mount points |
   | `/run/anf` | agent socket |

7. **Downloads the release** and unpacks it.
8. **Creates the Python environment** and installs dependencies.
9. **Generates `.env`** with random secrets, mode `0600`. If one exists, it is left
   untouched.
10. **Applies database migrations.**
11. **Installs the two systemd services.**
12. **Configures the web server** — and checks the configuration *before* reloading.
    If it is invalid, the previous one is restored and the installer stops: without
    that check, an error here would take down *every* site hosted on the machine, not
    just this one.
13. **Starts the services** and verifies that the API answers.

---

## After installing

### First sign-in

The panel answers at `/pannello` on the web server. On first start the **`admin`**
user is created with password **`admin`**, and the panel shows a prominent warning for
as long as it stays that way.

> **Change it before exposing the panel to the internet.**

### Real visitor addresses

If a reverse proxy terminating TLS sits in front of the server, then without
configuration every visitor appears to have the proxy's address, and download
monitoring cannot tell anyone apart.

In the file generated by the installer, add your proxies' addresses:

```bash
RemoteIPTrustedProxy 192.168.1.2
```

and in `.env`:

```bash
ANF_TRUSTED_PROXIES=127.0.0.1,192.168.1.2
```

### Checking that it works

```bash
systemctl status anf-agent anf-api
```

```bash
curl -fsS http://127.0.0.1:$(grep -oP '^ANF_PORT=\K\d+' /var/www/advanced-nas-folder/.env)/api/v1/health
```

---

## Extra host names, from the panel

The installer sets up the first vhost (`anf.conf`). To publish the panel on
another host name you don't need to go back to the server: the **Web server**
menu entry takes the name, shows a preview of the configuration and applies
it.

The generated file is named `anf-<hostname>.conf` and leaves the installer's
own file alone. Before being applied, the configuration is checked with
`apache2ctl configtest` or `nginx -t`: **if the check fails, the previous one
is put back** and the panel shows the error reported by the web server.

Deliberately out of scope: DNS, certificates and HTTPS listening. They live
upstream, typically on a reverse proxy, and generating configuration that
pretends to manage them would produce files that don't match the real setup.

## Upgrading

Run the installer again: it is idempotent and **touches neither `.env` nor the
database**.

```bash
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh && sudo bash install.sh
```

## Uninstalling

```bash
sudo bash install.sh --uninstall
```

Removes services, web server configuration and program. It does **not** touch the
database in `/var/lib/anf` or the mounts in `/srv/nas`: removing those is a deliberate
manual step.

---

## If something goes wrong

### The API does not answer

```bash
journalctl -u anf-api -n 50 --no-pager
```

Most common causes: a missing key in `.env`, or the database being unreachable because
`/var/lib/anf` is not owned by the `anf` user.

### The agent does not start

```bash
journalctl -u anf-agent -n 50 --no-pager
```

The agent **refuses to start unless it runs as root**: that is deliberate — it mounts
filesystems and must not degrade silently.

### The panel says the agent is unreachable

Check the socket and its permissions: it must be owned by `root`, group `anf`, mode
`0660`.

```bash
ls -la /run/anf/
```

### Mounting fails with `Protocol not supported`

This is not a permission problem but a version one: the configuration asks for NFSv4
and the NAS only offers v3. Check with `rpcinfo -p NAS_ADDRESS` and select version 3 in
the panel.

### The folder is read only even though you asked for write access

The NAS is denying it, and the panel says so explicitly. See the
[NFS write access guide](synology-nfs-scrittura.en.md).
