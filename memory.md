# Memoria di progetto — Advanced NAS Folder

Contesto che serve a riprendere il lavoro senza rileggere tutto il codice.
Aggiornare quando cambia una decisione, non a ogni commit.

---

## Cos'è

Pannello self-hosted per montare condivisioni NFS, pubblicare cartelle con permessi
per sottocartella e gestire file. Sostituisce FileBrowser e `mod_autoindex`.

- Repository pubblico: `wifi75/advanced-nas-folder`
- Licenza MIT
- Versione corrente: 0.27.4

## Stato alla v0.27.4 — 30 agosto 2026

**In produzione su `folder.iu3cyv.eu`** (server 192.168.1.106) dal 30 agosto 2026.
**431 test**, gate verde su ruff, mypy `strict`, ESLint, vue-tsc e build.

Il ciclo di rilascio passa dalle release GitHub: `update.sh` scarica **l'ultima
release**, non il branch. Un commit pushato ma senza release non arriva sul server,
e `update.sh` dice comunque «completato» — verificare sempre la versione con
`/api/v1/health`. Fra la creazione della release e la disponibilità pubblica del
pacchetto passano **una o due decine di secondi** di propagazione GitHub: prima si
prende un 404.

### Cosa è stato aggiunto dopo la v0.6.6

- **Indirizzi corti** (`sito/documenti`), solo su Apache, tramite `RedirectMatch`.
- **Sistema fotografico**: miniature prodotte dal server con Pillow, dati di scatto
  EXIF, ingrandimento e trascinamento, presentazione, raggruppamento per mese di
  scatto, fotogrammi dei video con `ffmpeg`.
- **Pubblicazione riorganizzata** in schede, secondo il modello scelto da Tiziano
  (albero nel menu, un solo riquadro per pubblicazione). Nome nell'indirizzo,
  origine e nomi da nascondere sono tutti modificabili.
- **Accesso alle cartelle protette** con nome utente e password, su una schermata
  con tinta propria (`--tinta-accesso`), distinta da quella del pannello.
- **Permessi per singola persona** usabili davvero: l'utente si sceglie da un
  elenco a selezione multipla e la cartella si percorre invece di scriverla.
- **Menu di chi non amministra**: solo «Le mie cartelle», dall'endpoint
  `GET /shares/mie`, che applica `acl.valuta` alla radice di ogni pubblicazione.
  Le rotte di amministrazione sono chiuse anche per indirizzo diretto.

### Trappole trovate sul campo, da non ripetere

- **Due blocchi CSS con lo stesso selettore** nello stesso foglio, lontani fra
  loro, si annullano in silenzio. È già successo due volte in
  `views/ArchivioView.vue`, che ne ha ancora diversi: nessun linter lo segnala.
- **`mod_rewrite` e `CustomLog` non sono ereditati** dai VirtualHost; `mod_alias`
  (`Alias`, `RedirectMatch`) invece sì.
- **`pytest | tail` maschera l'esito**: usare sempre `controlla.ps1`, che si ferma
  al primo passo fallito. Due commit rotti sono arrivati su GitHub così.
- **Uso prima della definizione in `<script setup>`**: compila, i tipi passano, la
  pagina muore bianca. La regola ESLint `no-use-before-define` è attiva e ne ha
  trovati dodici latenti.
- **Il service worker serviva la versione vecchia a una scheda già aperta.** Dalla
  v0.26.2 il pannello controlla e si ricarica da solo; per arrivarci da una
  versione precedente serve ancora una ricarica forzata.

### Sul server, dati di prova

Utenti `mario` e `gino` non amministratori, con permessi su `foto`. La password di
`gino` è stata reimpostata a `Prova12345` per provare il menu con i suoi occhi.

## Ambiente di sviluppo

`avvia-dev.ps1` avvia backend e frontend e stampa gli indirizzi. Senza argomenti
ascoltano su **tutte le interfacce**, per provare il pannello da telefono o tablet;
con `-SoloLocale` solo su `127.0.0.1`. Vite richiede `allowedHosts` per accettare
richieste che arrivano da un indirizzo IP: senza, risponde «host non consentito».

## Convenzioni della documentazione

Ogni documento rivolto a chi usa o installa il progetto esiste in **due lingue**:
il file italiano senza suffisso, l'inglese con `.en.md`, e in cima a entrambi il
collegamento all'altra versione. Vale anche per i documenti interni
(`PIANO.md`, `VERSIONI.md`, `agent/README.md`), tradotti dalla v0.6.0.

## Convenzioni dell'interfaccia

- **Ogni testo passa da `frontend/src/i18n/`.** L'italiano è la lingua di riferimento;
  l'inglese la rispecchia chiave per chiave e il tipo fa fallire la compilazione se
  ne manca una. Nessuna stringa va scritta direttamente nei componenti.
- **Nessun colore direttamente nei componenti**: tutto passa dalle variabili in
  `assets/main.css`, definite per il tema chiaro e ridefinite in *due* blocchi scuri
  (`prefers-color-scheme` e `[data-tema='scuro']`).
- Il menu è raggruppato per categoria. Dalla v0.27.0 **dipende da chi guarda**: un
  amministratore vede l'albero delle condivisioni e le pagine di sistema, chiunque
  altro solo «Le mie cartelle». Le voci di sistema non vanno mostrate a chi non
  amministra: l'API le rifiuta comunque, e mostrarle produce solo errori.
- **Le schede annidate hanno ciascuna il proprio parametro** nell'indirizzo
  (`scheda`, `sezione`). Con un parametro solo si scavalcano, e cliccare una scheda
  interna butta fuori dalla sezione.
- `npm run typecheck` usa `vue-tsc --build`: la variante `--noEmit` non controllava i
  progetti referenziati e lasciava passare errori che il build trovava.
- **Il pannello vive sotto `/pannello/`**, in sviluppo come in produzione: la `base`
  di Vite e il router lo dichiarano. Tenerlo alla radice in sviluppo farebbe
  funzionare in locale percorsi che poi si rompono installati.
- Il service worker è spento in sviluppo di proposito, e la sua registrazione **non è
  verificabile nel browser incorporato**, che la blocca anche per un service worker
  di una riga: va confermata su un browser vero.

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

**Il monitoraggio dichiara ciò che non sa.** Il registro sa che un download è stato
autorizzato, quando, per quale file e da quale indirizzo; **non sa** quanti byte siano
arrivati, perché la consegna è delegata al web server. Quel numero arriva dal suo
access log, se `ANF_ACCESS_LOG` è configurato, e finché non arriva resta vuoto: un
numero inventato sarebbe peggio di uno assente.

**`X-Forwarded-For` letto solo dai proxy fidati** (`ANF_TRUSTED_PROXIES`): quella
intestazione la può scrivere chiunque.

**Lo stato della ripresa di un caricamento è il file parziale stesso**, non una riga
in un database: la sua dimensione dice quanti byte sono arrivati. Sta nella cartella
di destinazione, nascosto, così il completamento è una rinomina atomica invece di una
seconda copia sulla rete.

**Apertura in linea solo per i tipi mostrabili** (immagini, video, audio, PDF, testo).
HTML e SVG restano allegati: serviti con il loro tipo reale sarebbero codice altrui
eseguito nel contesto del pannello.

**Scrittura disattivata di default.** Ogni mount nasce in sola lettura. La scrittura è
un interruttore esplicito con avviso, e richiede anche la regola corrispondente lato
NAS: il pannello mostra sempre stato richiesto *e* stato effettivo.

## Fuori perimetro per scelta

Shell integrata e comandi personalizzati di FileBrowser: esecuzione di codice remoto
su un pannello esposto a Internet.

## Vincoli noti dell'ambiente di destinazione

- Dietro un reverse proxy con TLS: il proxy va elencato in `ANF_TRUSTED_PROXIES`,
  altrimenti il monitoraggio vede un solo indirizzo per tutti.
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
