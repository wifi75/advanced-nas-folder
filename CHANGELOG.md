# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate qui.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/)
e il versionamento segue [Semantic Versioning](https://semver.org/lang/it/).

## [Non rilasciato]

### Aggiunto
- Configurazione applicativa (`app/core/config.py`) letta da ambiente e `.env`,
  con validazione dei percorsi assoluti.
- Motore e sessioni SQLite (`app/core/database.py`) con i PRAGMA riapplicati a ogni
  connessione: `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout`.
- Modelli del database: `User`, `Mount`, `Share`, `AccessRule`, `ShareLink`,
  `Transfer`, `VHost`, `Setting`.
- Endpoint `/api/v1/health` e `/api/v1/health/ready`, quest'ultimo verifica davvero
  la raggiungibilità del database.
- Prima migrazione Alembic con supporto asincrono e `render_as_batch`, necessario
  perché SQLite non sa modificare una colonna con `ALTER`.
- Scheletro frontend: Vue 3, TypeScript, Vite, Pinia, Vue Router. Client HTTP con
  messaggi d'errore comprensibili, tema chiaro/scuro a tre stati, piede di pagina
  con versione e attribuzione letti dall'API.

### Cambiato
- Python 3.14 richiesto, installato dal PPA `deadsnakes` accanto all'interprete di
  sistema e non al suo posto.
- Versioni delle dipendenze fissate interrogando PyPI e npm anziché a memoria:
  correzioni fino a versioni maggiori intere (TypeScript 5→7, Vue Router 4→5,
  Pinia 3→4, mypy 1→2, pytest 8→9).
- **Database: SQLite in modalità WAL al posto di PostgreSQL.** Il profilo d'uso del
  pannello (pochi utenti, scritture rare, letture frequenti) è esattamente quello per
  cui SQLite è progettato. Elimina un servizio da installare, configurare e mantenere,
  e rende l'installazione molto più leggera.

### Corretto
- `pyproject.toml` indicava `readme = "../README.md"`: setuptools rifiuta i percorsi
  fuori dalla cartella del pacchetto e l'installazione falliva. Campo rimosso.
- TypeScript riportato alla 6.0.3: `typescript-eslint` stabile non supporta la 7, che
  ha solo build alpha. Rimosso `baseUrl`, deprecato nella 6 e rimosso nella 7.
- Client HTTP: con `exactOptionalPropertyTypes` attivo, `body: undefined` non equivale
  a omettere la proprietà. La richiesta viene ora costruita in modo condizionale.

### Da fare
Vedere [TODO.md](TODO.md) per il piano completo delle fasi.

## [0.1.0] - 2026-08-29

Fase 0 — fondamenta del progetto.

### Aggiunto
- Struttura del repository: `backend/`, `agent/`, `frontend/`, `deploy/`, `docs/`.
- Licenza MIT.
- Documentazione di progetto: [README.md](README.md), [docs/PIANO.md](docs/PIANO.md),
  [TODO.md](TODO.md), `memory.md`.
- Wiki operativa: [abilitare la scrittura NFS su Synology](docs/synology-nfs-scrittura.md).
- `.env.example` con tutte le voci di configurazione previste.
- `.gitignore` che esclude segreti, `.env`, dipendenze e dati locali.

### Deciso
- Separazione dei privilegi fra `anf-api` (non privilegiato) e `anf-agent` (root),
  con comandi tipizzati su socket Unix — mai stringhe di shell.
- Generazione di unit systemd `.mount`/`.automount` invece di righe in `/etc/fstab`.
- Consegna dei download delegata al web server (`X-Sendfile` su Apache,
  `X-Accel-Redirect` su Nginx) per ottenere il resume in modo nativo.
- Scrittura sui mount disattivata di default, con avviso di rischio.
- La shell integrata di FileBrowser **non** viene replicata, per sicurezza.
