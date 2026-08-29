# Piano tecnico

Documento di riferimento dell'architettura. Le decisioni qui dentro sono state prese
prima di scrivere codice e non vanno cambiate senza aggiornare anche `memory.md`.

---

## I due nodi che decidono il progetto

Tutto il resto è conseguenza di come si risolvono questi due problemi.

### Nodo 1 — montare filesystem richiede root

Un'applicazione web esposta a Internet non può girare da root. La soluzione è la
separazione dei privilegi in due processi:

```
Pannello ──▶ anf-api ──JSON tipizzato──▶ anf-agent ──▶ unit systemd ──▶ mount
            (utente anf)   socket unix      (root)        + configtest
```

- `anf-api` non esegue mai operazioni di sistema
- `anf-agent` ascolta **solo** su un socket Unix locale, permessi `0660`,
  proprietario `root`, gruppo dell'applicazione
- il protocollo ha un insieme chiuso di verbi:
  `mount.create`, `mount.start`, `mount.stop`, `mount.remove`, `mount.status`,
  `nfs.discover`, `vhost.apply`, `vhost.remove`
- l'agent **non costruisce mai una riga di shell**: riceve campi tipizzati e li
  sostituisce in un template

Validazioni obbligatorie lato agent:

| Campo | Regola |
|---|---|
| Server | indirizzo IP o hostname valido |
| Export | percorso assoluto, normalizzato, senza `..` |
| Mountpoint | forzato sotto `ANF_MOUNT_ROOT`, slug `[a-z0-9-]+` |
| Opzioni | esclusivamente da whitelist |

### Nodo 2 — chi manda i byte

Streamare file di grandi dimensioni attraverso Python satura i worker e degrada tutto
il pannello. La consegna va delegata al web server:

1. il client chiede il file all'API
2. l'API verifica autenticazione e permessi
3. l'API risponde **vuota**, con un header che indica il file da servire
4. il web server legge il file dal mount e lo invia

| Web server | Header | Requisito |
|---|---|---|
| Apache | `X-Sendfile` | `libapache2-mod-xsendfile` |
| Nginx | `X-Accel-Redirect` | `internal` location |

Il vantaggio decisivo è che **il resume arriva gratis**: `Range`, `If-Range`, `ETag` e
le risposte `206` sono gestite nativamente dal web server. Farle passare da Python
significherebbe riscriverle peggio.

Una sola voce di configurazione, `ANF_DOWNLOAD_BACKEND`, seleziona il modo; `stream` è
previsto solo per lo sviluppo locale.

---

## Perché unit systemd e non `/etc/fstab`

`/etc/fstab` è un file unico condiviso da tutto il sistema. Una riga sbagliata scritta
da un pannello web può impedire l'avvio del server. Le unit systemd invece sono un
file per mount: si aggiungono e si rimuovono singolarmente, e una unit non valida
resta isolata.

Opzioni predefinite, validate sul campo:

```
ro,noatime,vers=3,proto=tcp,soft,timeo=150,retrans=3,nolock,
_netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30,x-systemd.idle-timeout=600
```

| Opzione | Perché |
|---|---|
| `nofail` + `x-systemd.automount` | il server si avvia anche a NAS spento, e monta alla prima richiesta |
| `soft`, `timeo=150`, `retrans=3` | a NAS irraggiungibile il web server riceve un errore invece di restare appeso |
| `x-systemd.idle-timeout=600` | smonta da fermo: un riavvio del NAS non lascia handle stale |
| `nolock` | mount in sola lettura, nessun bisogno di `rpc-statd`/`rpcbind` |
| `vers=3` | molti NAS espongono solo NFSv2/v3; va verificato con `rpcinfo -p <nas>` |

> Se `mount` restituisce `Protocol not supported`, quasi sempre è perché la
> configurazione chiede NFSv4 ma il NAS espone solo la v3.

---

## Modello dei dati

| Entità | Ruolo |
|---|---|
| `User` | account, ruolo, ambito, permessi granulari |
| `Mount` | condivisione NFS: server, export, mountpoint, opzioni, stato richiesto ed effettivo |
| `Share` | cartella pubblicata a partire da un mount, con sottopercorso |
| `AccessRule` | regola di accesso per prefisso di percorso dentro uno share |
| `ShareLink` | link con token, scadenza, password opzionale, limite di download |
| `Transfer` | download o upload, per la dashboard di monitoraggio |
| `VHost` | pubblicazione sul web server: hostname, percorso, share collegato |
| `Setting` | configurazione modificabile dal pannello, non da file |

---

## Sicurezza

- Password con **Argon2**; token di condivisione casuali a 256 bit, salvati come hash
- Autenticazione con JWT a vita breve più refresh token revocabile
- Ogni accesso a un file passa dal controllo ACL: **il mount non deve mai essere
  raggiungibile direttamente dal web server**, altrimenti ogni permesso è aggirabile
- Ogni modifica alla configurazione del web server è preceduta da `apache2ctl
  configtest` / `nginx -t` e seguita da ripristino automatico in caso di errore
- Dietro un reverse proxy servono `mod_remoteip` e `X-Forwarded-For`, altrimenti tutti
  i client risultano avere l'indirizzo del proxy
- Nel repository non finisce alcun dato reale: indirizzi, domini e nomi delle
  condivisioni vivono in `.env` e nel database

---

## Stack

Versioni stabili verificate il 29 agosto 2026.

| Componente | Scelta | Versione |
|---|---|---|
| Backend | FastAPI | 0.141.1 |
| Frontend | Vue 3 + TypeScript | 3.5.33 |
| Build | Vite | 8.0.9 |
| Database | PostgreSQL | 18.6 |
| Node (solo CI) | LTS | 24.18.1 |
| Agent | Python standard library | — |

L'agent privilegiato **non usa dipendenze esterne**, di proposito: è il processo che
gira da root, e ogni libreria in più è superficie di attacco in più.

Ubuntu 24.04 distribuisce PostgreSQL 16; per la 18 serve il repository PGDG.
L'installer gestisce entrambi i casi.

### Il frontend non si compila sul server

GitHub Actions costruisce `dist/` e lo allega alla release. Il server non installa mai
Node né `node_modules`: l'installazione resta leggera e non consuma spazio disco.

---

## Perimetro funzionale

Advanced NAS Folder sostituisce FileBrowser, quindi ne eredita l'intero perimetro:
navigazione e viste multiple, operazioni sui file, upload riprendibile, download di
archivi, editor di codice, anteprime, ricerca, condivisioni, multiutente con permessi
granulari, temi, multilingua, API con token.

E aggiunge quello che FileBrowser non fa: gestione dei mount NFS, permessi per
sottocartella, gestione dei vhost, monitoraggio dei download in tempo reale.

**Non replicato per scelta:** la shell integrata e i comandi personalizzati. Su un
pannello raggiungibile da Internet sono esecuzione di codice remoto per definizione.

---

## Avanzamento dei download lato visitatore

Due livelli, dichiarati esplicitamente perché dipendono dal browser:

- **Chrome / Edge**: scrittura diretta su disco a blocchi tramite File System Access
  API, avanzamento reale, pausa e ripresa, stato conservato per riprendere anche dopo
  la chiusura della pagina.
- **Firefox / Safari**: quell'API non è disponibile. Si ricade sul download nativo del
  browser, che riprende comunque grazie al supporto Range del server, ma l'avanzamento
  lo mostra il browser e non la pagina.

Non è un limite dell'implementazione: è ciò che i browser espongono oggi.
