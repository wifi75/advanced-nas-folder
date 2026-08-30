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

## The three steps, in this order

This is the part that most often is not clear, so it is worth saying before
everything else:

| | What it does | What it does **not** do |
|---|---|---|
| **1. NFS shares** | mounts a NAS folder **onto the server** | does not make it reachable by anyone |
| **2. Publications** | decides which folder is reachable from the web, under what name and by whom | does not copy or move anything |
| **3. Archive** | is where you browse and download what has been published | |

Without step 1, step 2 is not possible: a publication always starts from an
already mounted folder. And **a folder that is mounted but not published is
reachable by nobody**, not even an administrator: it only sits on the server.

The address to share is born at step 2, and the panel shows it in full next to
every publication, ready to copy.

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

A publication is a NAS folder made reachable at an address, under a short name
that you choose.

### The address to share

Every publication shows **two addresses**, each with a copy button. They lead to
the same place:

| | Example | When to use it |
|---|---|---|
| **Short** | `https://your-domain/documents` | to dictate or type by hand. Apache only |
| **Full** | `https://your-domain/pannello/archivio/documents` | always valid, Nginx included |

The short one is a redirect to the full one: it works wherever you write it, but
the browser then shows the long one in the address bar.

If the visibility is *Anyone, even without signing in*, the address works for
whoever receives it, with no account needed. If instead you want to give access
to **one person only**, without opening the folder to everyone, do not share this
address: use a **share link**, which expires and can be revoked.

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

### Looking at photos

Three ways of seeing the same folder, from the switcher at the top:

| | When it helps |
|---|---|
| **List** | files of any kind: name, size and date in columns |
| **Grid** | cards with a thumbnail, the name and the commands |
| **Gallery** | large thumbnails, to recognise photos at a glance |

The choice stays in your browser: it is a reading preference, not a property of
the folder, and does not change what others see.

**Thumbnails are produced by the server**, once per photo, and kept in
`/var/lib/anf/miniature` — not on the NAS. They are requested only when they
scroll into view: in a folder with hundreds of shots, generating them all on
open would mean waiting for images you will not look at.

If a photo is replaced by another with the same name the thumbnail is redone on
its own: it depends on the file's date and size too.

Opening a photo, you move to the others in the folder with the **arrows at the
sides**, the **keyboard arrows**, or by **swiping** on a phone. The header says
where you are: «3 of 12».

On a phone the gallery fits three photos per row and the preview takes the whole
screen: a window's margins would waste exactly the space needed to look at the
image.

### Photos grouped by month

In the **Thumbnails** view photos are grouped by **month taken**, newest first.
Those without a date go into a separate group at the end: a photo with no date
is not a January photo.

The date used is the one written by the camera, not the file's. The server
reads it **once** per photo and keeps it next to the thumbnail: the first time
a folder with hundreds of shots is opened takes a few seconds, the next times
do not.

In the other two views — list and grid — photos stay in alphabetical order, and
the dates are not even read.

### Looking closely at a photo

With an image open:

| | |
|---|---|
| **Mouse wheel** | zooms, up to eight times |
| **Drag** | pans inside the image when zoomed |
| **Double click** | back to the whole picture |
| **▶** | starts the slideshow |
| **Space bar** | starts and stops the slideshow |
| **⤢** | full screen, on a dark ground |
| **Turning the phone** | switches to full screen by itself, and back when upright |

The slideshow starts over at the end: one that stops by itself has to be
restarted every round.

> **The browser bar cannot be removed from a tab.** No web page can hide it:
> it is a browser rule, not a shortcoming of the panel. To do without it, add
> the panel to the Home screen — *share ▸ «Add to Home Screen»* — and from
> there it opens like an app, with no bars.

### Shot data

Under the image, **Shot data** opens what the camera wrote into the file: when
it was taken, with which body and lens, exposure time, aperture, ISO, focal
length, and — when present — a link to the spot on the map.

The panel only **reads** it: changing it would mean rewriting someone else's
original just to show a screen.

If the panel does not appear, that photo has no shot data: edited or exported
images often lose it, and that is normal.

> The **shot date** is not the file date. On a NAS the latter is almost always
> the date the photo was *copied*, not the date it was taken.

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
