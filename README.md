# Advanced NAS Folder

🇬🇧 [English version](README.en.md)

[![Release](https://img.shields.io/github/v/release/wifi75/advanced-nas-folder?label=Release&color=2B7489&logo=github)](https://github.com/wifi75/advanced-nas-folder/releases/latest)
[![Controlli](https://img.shields.io/github/actions/workflow/status/wifi75/advanced-nas-folder/controlli.yml?branch=main&label=Controlli&logo=githubactions&logoColor=white)](https://github.com/wifi75/advanced-nas-folder/actions/workflows/controlli.yml)
[![Test](https://img.shields.io/badge/Test-431-6E9F18?logo=pytest&logoColor=white)](tests)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%2B%20systemd-FCC624?logo=linux&logoColor=black)](https://systemd.io)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%200.141-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Frontend](https://img.shields.io/badge/Frontend-Vue%203.5-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Build-Vite%208.2-646CFF?logo=vite&logoColor=white)](https://vite.dev)
[![Lingue](https://img.shields.io/badge/Interfaccia-italiano%20%7C%20english-C8467C)](frontend/src/i18n)
[![PWA](https://img.shields.io/badge/App-installabile%20(PWA)-5A0FC8?logo=pwa&logoColor=white)](https://web.dev/explore/progressive-web-apps)
[![Database](https://img.shields.io/badge/DB-SQLite%20(WAL)-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/wal.html)
[![Storage](https://img.shields.io/badge/Storage-NFS%20v3%20%7C%20v4-EE0000?logo=redhat&logoColor=white)](https://linux-nfs.org)
[![Immagini](https://img.shields.io/badge/Miniature-Pillow%2012.3-4B8BBE?logo=python&logoColor=white)](https://python-pillow.github.io)
[![Video](https://img.shields.io/badge/Video-ffmpeg-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org)
[![Web server](https://img.shields.io/badge/Web%20server-Apache%20%7C%20Nginx-D22128?logo=apache&logoColor=white)](https://httpd.apache.org)
[![Sicurezza](https://img.shields.io/badge/Privilegi-agent%20root%20isolato-4B0082)](docs/PIANO.md#nodo-1--montare-filesystem-richiede-root)
[![License](https://img.shields.io/badge/License-MIT-3DA639?logo=opensourceinitiative&logoColor=white)](LICENSE)
[![SemVer](https://img.shields.io/badge/SemVer-2.0.0-3F4551)](https://semver.org/lang/it/)
[![Changelog](https://img.shields.io/badge/Changelog-Keep%20a%20Changelog-E05735)](CHANGELOG.md)
[![Mantenuto](https://img.shields.io/badge/Mantenuto-s%C3%AC%20(2026)-2EA44F)](https://github.com/wifi75/advanced-nas-folder/commits/main)

Pannello self-hosted che **monta condivisioni NFS**, **pubblica cartelle con permessi
per sottocartella** e sostituisce integralmente FileBrowser — senza che tu debba mai
modificare a mano un file di configurazione del server.

> **Stato: in esercizio su un server reale dalla v0.6.9.** Monta condivisioni NFS,
> pubblica cartelle con permessi fino al singolo utente, scarica e carica file con
> ripresa, cerca, mostra anteprime e registra i trasferimenti. La prima installazione
> vera ha fatto emergere una serie di errori che nessun test poteva cogliere —
> permessi di cartelle create da systemd, percorsi risolti dalla cartella corrente —
> corretti nelle 0.6.7-0.6.9. Vedere [TODO.md](TODO.md).

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
registrati, o link temporaneo con scadenza e limite di download. Oltre alle regole,
**permessi per singola persona**: una cartella la può vedere un solo utente, e un
diniego esplicito toglie un ramo a qualcuno lasciandolo aperto agli altri. Chi non
amministra trova nel menu solo le cartelle che può davvero aprire.

**Gestione file** — navigazione, operazioni su file e cartelle, caricamento
drag&drop **riprendibile** (anche di cartelle intere), download di una cartella come
archivio ZIP, selezione multipla, ricerca ricorsiva, anteprime di immagini, video,
audio e PDF, editor di testo, checksum SHA-256. Multiutente con ambiti e permessi
granulari.

**Download** — la consegna dei file è delegata al web server (`X-Sendfile` su Apache,
`X-Accel-Redirect` su Nginx): Python non tocca mai il contenuto, e il *resume* delle
richieste interrotte funziona in modo nativo. Un cruscotto dal vivo mostra file,
indirizzo reale del client ed esito.

> I **byte davvero trasferiti** li conosce solo il web server, che è quello che invia
> i file: compaiono nel cruscotto se ne è indicato l'access log, e restano vuoti
> altrimenti. Una percentuale in tempo reale richiederebbe di far passare i byte da
> Python, cioè rinunciare alla ripresa nativa: non vale lo scambio.

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

Guida completa: **[docs/INSTALL.md](docs/INSTALL.md)**

Scaricare, controllare, eseguire — passi separati, perché lo script gira da root.
Da una cartella tua, **non** da `/var/www`, dove l'installer ci si mette da solo:

```bash
cd /root
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh
sha256sum install.sh
sudo bash install.sh
```

Aggiungi `--dry-run` per vedere esattamente cosa farebbe, senza applicare nulla.

L'installer mostra cosa ha trovato sulla macchina — web server, porte occupate e da
quale servizio — e chiede quale porta usare e una conferma finale. Con
`curl … | sudo bash` non chiede nulla e decide da solo, perché lì non ha un terminale
da cui leggere.

### Aggiornare e disinstallare

`update.sh` è già installato nella cartella dell'applicazione:

```bash
cd /var/www/advanced-nas-folder && sudo bash update.sh
```

Lo script si ricopia da solo altrove prima di partire, perché è proprio quella la
cartella che riscrive: bash legge lo script mentre lo esegue, e sostituirlo a metà
corsa interromperebbe l'aggiornamento in un punto qualunque.

`update.sh` mette la nuova versione accanto a quella in uso e scambia le due cartelle
solo dopo che la nuova ha risposto: se qualcosa non va, la precedente torna in
servizio da sola. `uninstall.sh` rimuove servizi e programma **lasciando i dati**;
per togliere anche database e configurazione serve `--tutto`.

## Struttura del progetto

```
backend/     API FastAPI: configurazione, modelli, endpoint, migrazioni Alembic
agent/       processo privilegiato, senza dipendenze esterne (solo libreria standard)
frontend/    interfaccia Vue 3 + TypeScript, compilata dalla CI
deploy/      unit systemd, modelli di configurazione per il web server, installer
docs/        piano tecnico, versioni delle dipendenze, guide operative
tests/       test di API e agent, eseguiti dalla CI a ogni push
```

## Avvio in sviluppo

Servono Python 3.14 e Node 24. Preparazione, una volta sola:

```bash
cd backend && python3.14 -m venv .venv && .venv/bin/pip install -e ".[dev]" && cd ../frontend && npm install
```

Copia `.env.example` in `.env`, imposta `ANF_ENV=development` e genera la chiave con
`openssl rand -hex 32`. In sviluppo le tabelle si creano da sole e viene creato
l'utente **`admin`** con password **`Admin1234`**, segnalata dal pannello finché resta
quella.

### Su Windows

Uno script avvia entrambi i servizi e stampa gli indirizzi:

```bash
.\avvia-dev.ps1
```

Apre backend e frontend come schede della stessa finestra di Windows Terminal, o in
due finestre separate se non è installato.

### A mano

```bash
cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8100 --reload
```

In un secondo terminale il frontend, che inoltra `/api` alla porta 8100:

```bash
cd frontend && npm run dev -- --host
```

### Provare da un altro dispositivo

Con `--host` (e con `avvia-dev.ps1` senza argomenti) i servizi ascoltano su tutte le
interfacce: il pannello si raggiunge da telefono o tablet all'indirizzo della macchina
in rete, per esempio `http://192.168.1.50:5195/pannello/`.

Il pannello vive sotto `/pannello/` anche in sviluppo, perché è lì che il web server
lo serve in produzione: tenerlo alla radice in sviluppo farebbe funzionare in locale
percorsi che poi non funzionano installati.

> **Attenzione:** così il pannello è raggiungibile da chiunque sia nella stessa rete,
> e le credenziali iniziali sono `admin`/`Admin1234`. Usa `-SoloLocale`
> (oppure `--host 127.0.0.1`) quando non ti serve.

## Comandi utili

| Comando | Cosa fa |
|---|---|
| `.venv/bin/ruff check .` | analisi statica di backend, agent e test |
| `.venv/bin/ruff format .` | formattazione |
| `.venv/bin/pytest` | i test, dalla radice del progetto |
| `cd backend && .venv/bin/mypy app` | controllo dei tipi, modalità `strict` |
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

- [Guida all'uso](docs/GUIDA.md) — come si usa, dal primo accesso ai link di condivisione
- [Installazione](docs/INSTALL.md) — guida completa e risoluzione dei problemi
- [Piano tecnico](docs/PIANO.md) — architettura, modello dei dati, scelte motivate
- [Versioni delle dipendenze](docs/VERSIONI.md) — stato attuale e come verificarle
- [Agent privilegiato](agent/README.md) — protocollo e regole di sicurezza
- [Abilitare la scrittura NFS su Synology](docs/synology-nfs-scrittura.md)
- [TODO.md](TODO.md) — stato di ogni fase, e i limiti dichiarati per scelta
- [CHANGELOG.md](CHANGELOG.md) — cosa è cambiato e perché

## Licenza

[MIT](LICENSE) — Copyright © 2026 Tiziano Cassone

---

Ideato e sviluppato da Tiziano Cassone
