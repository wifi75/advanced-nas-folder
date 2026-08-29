# Enabling NFS write access on Synology

🇮🇹 [Versione italiana](synology-nfs-scrittura.md)

Advanced NAS Folder creates every mount **read only**. That is deliberate: a panel
reachable from the internet that can write to the NAS is a very different risk from one
that can only read.

If you need to upload files from the panel, write access must be enabled **on both
sides**. Enabling it only in the panel is not enough: the NAS will keep refusing
writes, and the panel will tell you so, showing *requested: read and write — actual:
read only*.

---

## 1. On the NAS (DSM)

1. **Control Panel → Shared Folder**
2. Select the folder and click **Edit**
3. **NFS Permissions** tab
4. Select the server's rule and click **Edit** (or **Create** if there is none)

Set:

| Field | Value | Note |
|---|---|---|
| **Hostname or IP** | the server's address | never `*`: always restrict to a single host |
| **Privilege** | `Read/Write` | this is what unlocks writing |
| **Squash** | see below | **the most important choice** |
| **Security** | `sys` | |
| Allow connections from non-privileged ports | ✅ | needed for non-root mounts |
| Allow users to access mounted subfolders | ✅ | needed when mounting a subfolder |

Click **Save** on both windows.

### Squash: the field people get wrong

*Squash* decides **who owns the files** the server writes to the NAS. Getting it wrong
produces no error: the files are created, but with an owner that leaves you unable to
manage them from File Station or over SMB.

| Setting | Effect |
|---|---|
| `No mapping` | files keep the server's UID. Correct **only if** UIDs match between server and NAS — almost never the case. |
| `Map all users to admin` | every file is owned by `admin`. Convenient and manageable from DSM, but the server effectively gains admin privileges on the share. |
| `Map all users to guest` | files are owned by `guest`. Safer, but on some setups `guest` has no write permission in the folder and writes fail. |

**Recommendation:** start with `Map all users to admin`, check that uploading works and
that the files look right in File Station. If you want stronger isolation, switch to
`guest` and check again — first making sure `guest` has write permission in the
folder's **Permissions** tab.

---

## 2. In the panel

1. Open the mount under **Mounts → Edit**
2. Turn on **Allow writing**
3. Confirm the risk warning
4. The panel remounts the share and re-reads the actual state

If after remounting the actual state is still `read only`, the NAS rule was not
applied: check that the address in the NFS rule matches the server's exactly.

---

## Checking from the command line

On the server, to see how the share is really mounted:

```bash
findmnt -t nfs -o TARGET,SOURCE,OPTIONS
```

Look for `ro` or `rw` at the start of the options. For a concrete write test:

```bash
touch /srv/nas/<mount-name>/.write-test && rm /srv/nas/<mount-name>/.write-test && echo "write OK"
```

To see which shares the NAS exports and to which hosts:

```bash
showmount -e <nas-address>
```

---

## If the mount fails with `Protocol not supported`

This is not a permission problem but a protocol version one: the configuration is
asking for NFSv4 while the NAS only offers v3. Check which versions are available:

```bash
rpcinfo -p <nas-address> | grep nfs
```

If only versions `2` and `3` appear, set `vers=3` in the mount options — or enable
NFSv4.1 under **Control Panel → File Services → NFS** in DSM.

For a read-only mount on a local network, v3 is perfectly fine: the only practical
advantage of v4.1 in this scenario is not depending on `rpcbind`/`rpc-statd`, and that
is already achieved with the `nolock` option.
