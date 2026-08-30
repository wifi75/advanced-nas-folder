# User guide

How to use Advanced NAS Folder, from the point of view of someone working
inside it. For installation see [INSTALL.en.md](INSTALL.en.md).

*[Versione italiana](GUIDA.md)*

---

## In short

The panel does three things, in this order:

1. it **mounts** the NAS folders on the server, without touching config files;
2. it **publishes** those folders, deciding who can see them;
3. it **serves** the files to whoever is allowed to download them.

The three are deliberately separate: a mounted share is reachable by nobody
until it is published, and a publication says nothing about *how* the NAS is
attached.

---

## First sign-in

The installation creates a single user, `admin`, with password `Admin1234`. The
panel says so at every sign-in until it is changed: **Users → your own name →
change password**, or from the sign-in page.

While that password is still the initial one, the panel should not be exposed
to the Internet.

---

## Mounting a NAS folder

**NFS shares → New share.**

You give the NAS address and the panel asks the NAS itself which folders it
exports: you pick from a list instead of typing a path from memory.

Three things worth knowing:

- **Read-only is the default.** Granting write access is a separate choice, and
  it has to be made on the NAS too: the panel can *ask* for it, but if the NAS
  export rule doesn't grant it the mount stays read-only. When that happens the
  panel says so, instead of letting you find out at the first upload. How to
  configure it on a Synology: [synology-nfs-scrittura.en.md](synology-nfs-scrittura.en.md).
- **Mount-on-demand is on.** The folder is mounted when someone uses it and
  unmounted after a while with nobody touching it. A NAS switched off at night
  therefore doesn't hang the server.
- **If you already have mounts in `/etc/fstab`**, the panel finds them and
  offers to import them. After importing *and checking* them, you can comment
  out the old line from the same screen — but not before: while both are active
  the system tries to mount the same path twice.

---

## Publishing a folder

**Publications → New publication.**

A publication is a NAS folder made reachable at a panel address, under a short
name: `/archivio` becomes `https://your-domain/pannello/archivio/archivio`.

### Who can see it

**Visibility** is chosen in plain words, not technical terms:

| Choice | Who gets in |
|---|---|
| Anyone, even without signing in | everyone, including people with no account |
| Anyone who knows the password | whoever has that folder's password |
| All signed-in users | anyone with an account on the panel |
| Only authorised users | only people with an explicit permission on that path |
| Nobody | nobody, **not even administrators** |

Visibility can be changed **per subfolder**: the most specific rule always
wins. A public folder can contain a private one, and the other way round.

### Who can do what

Next to the rules there are **per-user permissions**: "only Mario sees this
folder". Here too the longest prefix wins, and a *Denied* permission beats the
folder rule — that is how you take one branch away from one person while it
stays open to everyone else.

### Checking before your users do

The same page has **Check an access**: you type a path, pick a user (or leave
it empty to try an anonymous visitor), and the panel answers saying **which
rule decided**. It is how you notice a wrong permission before somebody else
does.

---

## Browsing, downloading, uploading

From **Publications → Browse**, or directly at the publication's address.

- **Downloading** a file: the *Download* button. If the download is
  interrupted, the browser resumes it from where it stopped — it doesn't start
  over.
- **Downloading a whole folder**: *Download folder*, which produces a ZIP as it
  sends it. The browser shows no percentage, because the total size isn't known
  in advance.
- **Downloading several things at once**: tick the boxes and use *Download
  together*.
- **Uploading**: drop files on the dashed area, or pick a whole folder. Uploads
  go in chunks: if interrupted they resume from where they stopped, even the
  next day.
- **Searching**: the box at the top searches names, including subfolders.
  Results show the full path.
- **Preview**: click a file's name. Images, video, audio, PDF and text open in
  the panel; text can also be edited where you have write permission. From
  there you can compute the **SHA-256 checksum**, to verify a file arrived
  identical.

Editing buttons appear only where you can actually write.

---

## Sharing with people who have no account

**Publications → Folder rules → Share links.**

You pick the folder and, optionally, an expiry, a maximum number of downloads
and a password. The link that comes out is what you send: whoever opens it sees
only that folder, with no menu and no way to go up.

Two important things:

- **the token is shown once.** Only its fingerprint is stored, so it cannot be
  retrieved later: copy it right away;
- **revoking does not delete.** The link stops working but stays in the list
  with the number of times it was used, which is exactly what you want to know
  after revoking it.

A link never crosses two limits: it doesn't lead outside the folder it was
created for, and it doesn't open a path marked *Nobody*.

---

## Users

**Users → New user.**

Permissions here are **general** — what a person may do anywhere: download,
upload, create folders, rename, modify, delete, create links. *Where* they may
do it is decided per publication. The two are separate because they answer
different questions.

**Scope** is a boundary: a user scoped to `foto` never leaves that folder,
whatever permissions they are given.

The panel prevents making itself unmanageable: you cannot remove your own
privileges, and the last administrator can be neither demoted nor deleted.

---

## Seeing what happens

**Transfers** shows what was downloaded and uploaded, by whom and from which
address, updating live.

An honest note about the numbers: the **bytes actually transferred** are known
only to the web server, because it is the one sending the files. They appear
here only if its access log is set in `.env` (`ANF_ACCESS_LOG`). Until then
they stay empty — an invented number would be worse than a missing one.

If the panel sits behind a reverse proxy, real addresses arrive only if that
proxy is listed in `ANF_TRUSTED_PROXIES`: `X-Forwarded-For` can be written by
anyone, and always trusting it would let every visitor declare whatever address
they like.

---

## Settings

**Settings** lets you change the panel's name, subtitle and logo, and decide
whether to list files starting with a dot.

The same page shows **disk space**, including the disk the panel itself lives
on: that's the one people forget, and if it fills up the panel stops working
even with a half-empty NAS.

---

## Installing the panel on a phone

The panel is an installable application: open it in the phone's browser and the
menu offers *Add to Home Screen*. From there it opens like an app, full screen.

Updates don't apply themselves: a notice appears and you decide. Reloading the
code while someone is configuring a mount is worse than staying one version
behind for a few minutes.

---

## If something goes wrong

| Symptom | Where to look |
|---|---|
| A folder won't open | Publications → *Check an access*: it says which rule decided |
| Downloads come back empty | `XSendFilePath` (Apache) or the `internal` location (Nginx) is missing: regenerate the vhost from **Web server** |
| A mount won't start | NFS shares: the real state and the system error are there |
| The NAS refuses writes | that's a NAS rule, not a panel one: [synology-nfs-scrittura.en.md](synology-nfs-scrittura.en.md) |
| Transfers show no bytes | `ANF_ACCESS_LOG` is missing from `.env` |

Service logs:

```bash
journalctl -u anf-api -f
journalctl -u anf-agent -f
```
