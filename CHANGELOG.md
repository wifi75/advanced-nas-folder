# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate qui.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/)
e il versionamento segue [Semantic Versioning](https://semver.org/lang/it/).

## [Non rilasciato]

### Da fare
Vedere [TODO.md](TODO.md).

## [0.3.0] - 2026-08-29

I mount NFS si gestiscono dall'interfaccia, in due lingue.

### Aggiunto
- **Interfaccia bilingue, italiano e inglese**: menu, testi, messaggi d'errore e
  titolo della scheda. L'italiano è la lingua di riferimento e il tipo delle chiavi
  fa fallire la compilazione se l'inglese ne dimentica una.
- **Tema chiaro, scuro o automatico.** L'automatico non è un terzo colore ma
  l'assenza di scelta: non marca nulla sulla radice e segue il sistema operativo.
- **Barra laterale per categorie** — Archivio, Accessi, Sistema — con pulsanti in
  vetro traslucido e una pastiglia colorata per voce. Le voci non ancora realizzate
  restano visibili ma disattivate, con la fase indicata.
- Lingua e tema si scelgono anche dalla pagina di accesso.
- **Risoluzione sicura dei percorsi** (`services/percorsi.py`): il percorso finale si
  costruisce dalla radice e si verifica che non ne sia uscito. Il controllo è fatto
  sul percorso *risolto*, così un collegamento simbolico che punta fuori viene
  bloccato.
- **Permessi per sottocartella** (`services/acl.py`): vince la regola con il prefisso
  più lungo, quindi una sottocartella può essere più restrittiva di quella che la
  contiene. Il confronto è per componenti, non per stringhe.
- **Endpoint dei mount**: elenco, scoperta delle condivisioni di un NAS, creazione,
  modifica, avvio, arresto ed eliminazione. Tutti riservati agli amministratori.
- Client verso l'agent (`services/agent_client.py`), unico punto di contatto fra
  l'API e il processo privilegiato.
- **Interfaccia dei mount**: elenco con stato richiesto *e* effettivo affiancati,
  creazione con scoperta delle condivisioni dal NAS invece che percorso digitato a
  mano, montaggio, smontaggio, rilettura dello stato ed eliminazione con conferma.
- 41 test su percorsi e permessi, 25 sugli endpoint. Suite complessiva a **150 test**.

### Corretto
- Cambiando lingua il titolo della scheda restava nella precedente: veniva impostato
  solo alla navigazione, e cambiare lingua non cambia rotta.
- Il comando `typecheck` non intercettava errori che il `build` trovava, dando falsa
  sicurezza. Ora usa lo stesso controllo.
- La cartella `.claude/` era finita nel repository: rimossa, con la regola di ignore
  in `.git/info/exclude` e non in `.gitignore`, che viene pubblicato.

## [0.2.0] - 2026-08-29

Fase 1 — autenticazione e agent privilegiato, entrambi verificati eseguendoli:
l'agent contro un NAS Synology reale, l'accesso dall'API e dal browser.

### Aggiunto
- **Agent privilegiato `anf-agent`**: socket Unix `0660`, protocollo JSON con
  insieme chiuso di verbi, validatori con whitelist, generazione di unit systemd,
  scoperta delle condivisioni NFS e lettura dello stato reale dei montaggi.
  Nessuna dipendenza esterna: usa solo la libreria standard.
- Autenticazione: Argon2id, token JWT, guardia sulle rotte, utente `admin` creato
  al primo avvio con avviso sulla password iniziale.
- Configurazione applicativa (`app/core/config.py`) letta da ambiente e `.env`,
  con validazione dei percorsi assoluti.
- Motore e sessioni SQLite (`app/core/database.py`) con i PRAGMA riapplicati a ogni
  connessione: `journal_mode=WAL`, `foreign_keys=ON`, `busy_timeout`.
- Modelli del database: `User`, `Mount`, `Share`, `AccessRule`, `ShareLink`,
  `Transfer`, `VHost`, `Setting`.
- Endpoint `/api/v1/health` e `/api/v1/health/ready`, quest'ultimo verifica davvero
  la raggiungibilità del database.
- **Suite di test: 84 test.** La parte più consistente copre i validatori
  dell'agent, cioè la barriera su cui poggia la sicurezza dell'intero progetto:
  slug con `..`, comandi iniettati nell'indirizzo del server, opzioni fuori
  whitelist, percorsi con risalita, verbi inventati. Più hash delle password,
  token manomessi, scaduti o firmati con un'altra chiave, e il flusso di accesso.
- Configurazione ruff unica in `ruff.toml` nella radice, così anche `agent/` e
  `tests/` rientrano negli stessi controlli del backend.
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
- `setuptools` non riusciva a determinare i pacchetti da installare con `alembic/` e
  `.venv/` accanto ad `app/`: ora sono dichiarati esplicitamente.
- Lo stato di un mount non innescava l'automount e riportava sempre "non montato";
  e `findmnt` filtrato sul tipo `nfs` nascondeva i percorsi sotto automount, che
  compaiono prima come `autofs`. Entrambi trovati eseguendo, non leggendo.

### Nota
Il codice usa la sintassi PEP 758 (`except A, B:` senza parentesi), valida solo da
**Python 3.14**, coerentemente con `requires-python`.

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
