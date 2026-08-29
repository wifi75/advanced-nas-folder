# Memoria di progetto — Advanced NAS Folder

Contesto che serve a riprendere il lavoro senza rileggere tutto il codice.
Aggiornare quando cambia una decisione, non a ogni commit.

---

## Cos'è

Pannello self-hosted per montare condivisioni NFS, pubblicare cartelle con permessi
per sottocartella e gestire file. Sostituisce FileBrowser e `mod_autoindex`.

- Repository pubblico: `wifi75/advanced-nas-folder`
- Licenza MIT
- Versione corrente: 0.4.0

## Stato alla v0.4.0 — 29 agosto 2026

**Fatto e verificato eseguendo, non solo leggendo:**

- Backend FastAPI su Python 3.14 con configurazione, SQLite in WAL, otto modelli e
  prima migrazione Alembic (`upgrade`, `downgrade`, risalita, nessuna differenza
  residua).
- Autenticazione: Argon2id, JWT, guardia sulle rotte, utente `admin` creato al primo
  avvio con avviso sulla password iniziale.
- Frontend Vue 3 + TypeScript: accesso, tema chiaro/scuro, piede di pagina che legge
  versione e autore dall'API. Build, typecheck ed ESLint puliti.
- **Agent privilegiato completo**, provato contro un NAS Synology reale: scoperta
  condivisioni, creazione, montaggio, stato con prova di scrittura sul campo,
  smontaggio, rimozione. Tentativi di violazione (slug con `..`, opzioni fuori
  whitelist, comandi iniettati nell'indirizzo) tutti respinti.

- **Endpoint e interfaccia dei mount** completi: scoperta delle condivisioni del NAS,
  creazione, montaggio, stato, eliminazione. Verificato end-to-end su Linux, pannello
  → API → agent → NAS reale.
- **Interfaccia bilingue** italiano/inglese e tema chiaro/scuro/automatico.
- Fase 2 iniziata: risoluzione sicura dei percorsi e permessi per sottocartella.

- **`install.sh`** pronto: bilingue, idempotente, con `--dry-run` e `--uninstall`.
  Verificato con shellcheck e prova a vuoto su server reale.
- **Permessi per singolo utente**: quale utente accede a quale cartella, o a tutte.
- Documentazione per chi installa disponibile in italiano e in inglese.

**Sul server non è ancora stato pubblicato nulla.** L'installazione vera si fa alla
fine dello sviluppo.

**Da fare subito dopo:** endpoint e interfaccia per assegnare i permessi, PWA.
Vedere [TODO.md](TODO.md).

## Ambiente di sviluppo

`avvia-dev.ps1` avvia backend e frontend e stampa gli indirizzi. Senza argomenti
ascoltano su **tutte le interfacce**, per provare il pannello da telefono o tablet;
con `-SoloLocale` solo su `127.0.0.1`. Vite richiede `allowedHosts` per accettare
richieste che arrivano da un indirizzo IP: senza, risponde «host non consentito».

## Convenzioni della documentazione

Ogni documento rivolto a chi usa o installa il progetto esiste in **due lingue**:
il file italiano senza suffisso, l'inglese con `.en.md`, e in cima a entrambi il
collegamento all'altra versione. I documenti interni di sviluppo (`PIANO.md`,
`VERSIONI.md`, `agent/README.md`) sono per ora solo in italiano.

## Convenzioni dell'interfaccia

- **Ogni testo passa da `frontend/src/i18n/`.** L'italiano è la lingua di riferimento;
  l'inglese la rispecchia chiave per chiave e il tipo fa fallire la compilazione se
  ne manca una. Nessuna stringa va scritta direttamente nei componenti.
- **Nessun colore direttamente nei componenti**: tutto passa dalle variabili in
  `assets/main.css`, definite per il tema chiaro e ridefinite in *due* blocchi scuri
  (`prefers-color-scheme` e `[data-tema='scuro']`).
- Il menu è raggruppato per categoria; le voci non ancora realizzate restano visibili
  ma disattivate, con la fase indicata.
- `npm run typecheck` usa `vue-tsc --build`: la variante `--noEmit` non controllava i
  progetti referenziati e lasciava passare errori che il build trovava.

## Decisioni architetturali fissate

**Separazione dei privilegi.** `anf-api` gira come utente `anf` non privilegiato.
`anf-agent` gira da root e ascolta su socket Unix. Fra i due passano comandi JSON
tipizzati, **mai stringhe di shell**. Motivo: il repository è pubblico, quindi la
sicurezza non può dipendere dal fatto che nessuno legga il codice.

**Unit systemd, non fstab.** I mount vengono generati come `.mount` + `.automount` in
`/etc/systemd/system/`. Motivo: `/etc/fstab` è un file unico condiviso, un errore lì
impedisce l'avvio dell'intero server; una unit sbagliata resta isolata.

Opzioni di mount adottate come predefinite, validate sul campo:
`ro,noatime,vers=3,proto=tcp,soft,timeo=150,retrans=3,nolock,_netdev,nofail,x-systemd.automount,x-systemd.mount-timeout=30,x-systemd.idle-timeout=600`

- `nofail` + `x-systemd.automount`: il server parte anche a NAS spento e monta alla prima richiesta
- `soft` + timeout brevi: il web server riceve un errore invece di restare appeso
- `idle-timeout`: smonta da fermo, così un riavvio del NAS non lascia handle stale
- `nolock`: nessuna dipendenza da `rpc-statd`/`rpcbind`

**Consegna dei download delegata al web server.** L'API autorizza e risponde vuota con
`X-Sendfile` (Apache) o `X-Accel-Redirect` (Nginx). Motivo: streamare file da un
gigabyte in Python satura i worker, e il resume (Range/206) funziona già in modo
nativo nel web server. Misurato: 206 a ~207 MB/s.

**Scrittura disattivata di default.** Ogni mount nasce in sola lettura. La scrittura è
un interruttore esplicito con avviso, e richiede anche la regola corrispondente lato
NAS: il pannello mostra sempre stato richiesto *e* stato effettivo.

## Fuori perimetro per scelta

Shell integrata e comandi personalizzati di FileBrowser: esecuzione di codice remoto
su un pannello esposto a Internet.

## Vincoli noti dell'ambiente di destinazione

- Dietro un reverse proxy con TLS: serve `mod_remoteip` + `X-Forwarded-For`, altrimenti
  il monitoraggio dei download vede un solo IP per tutti.
- Il NAS di riferimento espone **solo NFSv2/v3**, non NFSv4: `vers=3` non è una scelta
  di ripiego ma un requisito verificato con `rpcinfo`.
- Il frontend non si compila sul server: `dist/` arriva già pronto dalla CI.

## Versioni

Regola: sempre le ultime stabili, verificate **interrogando i registri** PyPI e npm —
non da ricerca web, che è stata smentita di versioni maggiori. Vedere
[docs/VERSIONI.md](docs/VERSIONI.md).

Python **3.14** dal PPA `deadsnakes`, installato accanto alla 3.12 di sistema. Il
collegamento `python3` non va mai spostato: ci dipendono il sistema e le altre
applicazioni della macchina.

## Standard applicati

- Backend FastAPI, frontend Vue 3 + TypeScript + Vite
- **Database SQLite in modalità WAL**, non PostgreSQL: scelta esplicita di Tiziano.
  Deroga consapevole allo standard "niente SQLite in produzione", giustificata dal
  profilo d'uso (utenti pochi, scritture rare) e dal fatto che elimina un servizio
  da mantenere. Il file sta in `/var/lib/anf/`.
- Installazione sotto `/var/www/`, servizi systemd
- Versione e attribuzione da un'unica sorgente: `backend/app/core/version.py`
- Ogni pagina del frontend mostra a piè di pagina, su una riga:
  `vX.Y.Z — Ideato e sviluppato da Tiziano Cassone`
- `package.json` allineato ad `APP_VERSION` a ogni bump
