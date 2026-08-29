# Advanced NAS Folder

[![Platform](https://img.shields.io/badge/Platform-Linux%20%2B%20systemd-FCC624?logo=linux&logoColor=black)](https://systemd.io)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%200.141-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Frontend](https://img.shields.io/badge/Frontend-Vue%203.5-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Build-Vite%208.2-646CFF?logo=vite&logoColor=white)](https://vite.dev)
[![Database](https://img.shields.io/badge/DB-SQLite%20(WAL)-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/wal.html)
[![Storage](https://img.shields.io/badge/Storage-NFS%20v3%20%7C%20v4-EE0000?logo=redhat&logoColor=white)](https://linux-nfs.org)
[![Web server](https://img.shields.io/badge/Web%20server-Apache%20%7C%20Nginx-D22128?logo=apache&logoColor=white)](https://httpd.apache.org)
[![Sicurezza](https://img.shields.io/badge/Privilegi-agent%20root%20isolato-4B0082)](docs/PIANO.md#nodo-1--montare-filesystem-richiede-root)
[![License](https://img.shields.io/badge/License-MIT-3DA639?logo=opensourceinitiative&logoColor=white)](LICENSE)

Pannello self-hosted che **monta condivisioni NFS**, **pubblica cartelle con permessi
per sottocartella** e sostituisce integralmente FileBrowser — senza che tu debba mai
modificare a mano un file di configurazione del server.

> **Stato: fase 1 in corso.** Autenticazione e agent privilegiato funzionanti e
> verificati contro un NAS reale. Mancano gli endpoint dei mount, l'interfaccia e
> l'installer. Vedere [TODO.md](TODO.md) per lo stato di ogni fase.

---

## Perché esiste

Pubblicare una cartella di un NAS sul web di solito significa: montarla a mano in
`/etc/fstab`, scrivere un `Alias` nella configurazione di Apache, e accontentarsi di
un elenco di file senza permessi né controllo. Se il mount cade, l'elenco diventa
silenziosamente vuoto e nessuno se ne accorge.

Advanced NAS Folder porta tutto questo dentro un pannello: scopri le condivisioni del
NAS, le monti con un clic, decidi chi vede cosa fino al livello della singola
sottocartella, e vedi in tempo reale chi sta scaricando.

## Funzionalità

**Mount NFS** — scoperta automatica delle condivisioni esportate dal NAS, montaggio e
smontaggio dal pannello, opzioni scelte da whitelist, stato *richiesto* e stato
*effettivo* sempre visibili. Non tocca mai `/etc/fstab`: genera unit systemd, una per
mount, così un errore resta isolato e non impedisce l'avvio del server.

**Pubblicazione e permessi** — cartelle pubblicate come *share*, con regole di accesso
per prefisso di percorso: pubblica, protetta da password, riservata a utenti
registrati, o link con scadenza e limite di download.

**Gestione file** — navigazione con viste elenco / griglia / galleria, upload
drag&drop riprendibile, download di cartelle come archivio, editor di testo e codice,
anteprime, ricerca, multiutente con ambiti e permessi granulari.

**Download** — la consegna dei file è delegata al web server (`X-Sendfile` su Apache,
`X-Accel-Redirect` su Nginx): Python non tocca mai il contenuto, e il *resume* delle
richieste interrotte funziona in modo nativo. Dashboard in tempo reale con file, IP
reale del client, percentuale e velocità.

## Sicurezza

Il pannello esegue operazioni privilegiate (montare filesystem, scrivere
configurazioni del web server) senza mai girare da root:

| Processo | Utente | Ruolo |
|---|---|---|
| `anf-api` | `anf`, non privilegiato | applicazione web, non tocca il sistema |
| `anf-agent` | `root` | esegue le operazioni privilegiate, ascolta solo su socket Unix locale |

Fra i due passano **comandi tipizzati**, mai stringhe di shell. L'agent valida ogni
richiesta: i mountpoint sono confinati sotto `ANF_MOUNT_ROOT`, le opzioni di mount
vengono da una whitelist, e ogni modifica alla configurazione del web server passa da
`apache2ctl configtest` (o `nginx -t`) **prima** del reload, con ripristino automatico
se il test fallisce.

Due scelte deliberate:

- **La scrittura sui mount è disattivata di default.** Va abilitata esplicitamente,
  con avviso di rischio, e richiede che sia consentita anche lato NAS
  ([guida](docs/synology-nfs-scrittura.md)).
- **La shell integrata e i comandi personalizzati di FileBrowser non sono
  replicati.** Su un pannello raggiungibile da Internet sono esecuzione di codice
  remoto per definizione.

## Requisiti

- Linux con systemd (sviluppato e testato su Ubuntu 24.04 LTS)
- Apache con `mod_xsendfile`, **oppure** Nginx
- Python 3.14 o superiore — su Ubuntu si installa dal PPA `deadsnakes`, **affiancato**
  all'interprete di sistema, che non viene toccato. Se ne occupa `install.sh`.
- Nessun server di database: i dati stanno in un file SQLite
- `nfs-common` per i mount NFS

Node.js **non** è richiesto sul server: il frontend viene compilato dalla CI e
distribuito già pronto nella release.

## Installazione

> **Non ancora disponibile.** `install.sh` arriva a fine fase 0. Fino ad allora si
> usa l'avvio in sviluppo descritto sotto.

Quando sarà pronto, l'installazione sarà in tre passi separati — scaricare,
controllare, eseguire — perché lo script gira da root e merita che tu possa leggerlo
prima:

```bash
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh
sha256sum install.sh
sudo bash install.sh
```

## Struttura del progetto

```
backend/     API FastAPI: configurazione, modelli, endpoint, migrazioni Alembic
agent/       processo privilegiato, senza dipendenze esterne (solo libreria standard)
frontend/    interfaccia Vue 3 + TypeScript, compilata dalla CI
deploy/      unit systemd, modelli di configurazione per il web server, installer
docs/        piano tecnico, versioni delle dipendenze, guide operative
```

## Avvio in sviluppo

Servono Python 3.14 e Node 24. Backend:

```bash
cd backend && python3.14 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```

Copia `.env.example` in `.env`, imposta `ANF_ENV=development` e genera la chiave con
`openssl rand -hex 32`. In sviluppo le tabelle si creano da sole e viene creato
l'utente **`admin`** con password **`admin`**, segnalata dal pannello finché resta
quella. Poi:

```bash
cd backend && .venv/bin/uvicorn app.main:app --port 8100 --reload
```

In un secondo terminale il frontend, che gira su `5173` e inoltra `/api` alla porta
8100:

```bash
cd frontend && npm install && npm run dev
```

## Comandi utili

| Comando | Cosa fa |
|---|---|
| `cd backend && .venv/bin/ruff check app/` | analisi statica del backend |
| `cd backend && .venv/bin/mypy app/` | controllo dei tipi, modalità `strict` |
| `cd backend && .venv/bin/alembic upgrade head` | applica le migrazioni |
| `cd backend && .venv/bin/alembic revision --autogenerate -m "…"` | nuova migrazione |
| `cd frontend && npm run typecheck` | controllo dei tipi del frontend |
| `cd frontend && npm run lint` | ESLint |
| `cd frontend && npm run build` | compila `dist/` |

## Configurazione

Tutte le voci sono documentate in [`.env.example`](.env.example). I segreti
(`ANF_SECRET_KEY`) vengono generati dall'installer e scritti solo in `.env`, con
permessi `0600`. Nel repository non è presente alcun dato reale: indirizzi, domini e
nomi delle condivisioni vivono in `.env` e nel database.

## Documentazione

- [Piano tecnico](docs/PIANO.md) — architettura, modello dei dati, scelte motivate
- [Versioni delle dipendenze](docs/VERSIONI.md) — stato attuale e come verificarle
- [Agent privilegiato](agent/README.md) — protocollo e regole di sicurezza
- [Abilitare la scrittura NFS su Synology](docs/synology-nfs-scrittura.md)
- [TODO.md](TODO.md) — stato di ogni fase
- [CHANGELOG.md](CHANGELOG.md) — cosa è cambiato e perché

## Licenza

[MIT](LICENSE) — Copyright © 2026 Tiziano Cassone

---

Ideato e sviluppato da Tiziano Cassone
