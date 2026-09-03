# Memoria di progetto — Advanced NAS Folder

Contesto che serve a riprendere il lavoro senza rileggere tutto il codice.
Aggiornare quando cambia una decisione, non a ogni commit.

---

## Cos'è

Pannello self-hosted per montare condivisioni NFS, pubblicare cartelle con permessi
per sottocartella e gestire file. Sostituisce FileBrowser e `mod_autoindex`.

- Repository pubblico: `wifi75/advanced-nas-folder`
- Licenza MIT
- Versione corrente: 0.28.11

## Risolto — mount NFS bloccato su LXC: creato `docker-2` come VM vera

`docker-vps` (192.168.1.224) resta un container LXC non privilegiato su
Proxmox VE — confermato che NFS/SMB-CIFS sono lì disabilitati con
l'etichetta "privileged only", non sbloccabili senza rendere il container
privilegiato (isolamento minore dall'host). Invece di convertirlo, creato
un **secondo server**, `docker-2` (192.168.1.233), come **VM KVM vera**
su Proxmox (Ubuntu 24.04, non Debian) — stesso schema Docker+Portainer,
ma senza il limite del kernel: `systemd-detect-virt` risponde `kvm`, e un
mount NFS reale funziona (dopo aver aggiunto l'IP alla lista permessi NFS
del NAS — un passo lato NAS, non lato progetto). Vedi la voce "Stato alla
v0.28.11" appena sotto per i dettagli di come è stata creata.

`docker-vps` resta comunque su, funzionante per tutto tranne il mount
NFS — non è stato smantellato, solo affiancato da `docker-2` che ora è la
macchina di riferimento per il lavoro che richiede NFS.

## Stato alla v0.28.11 — 3 settembre 2026

Creando `docker-2` da zero (Ubuntu 24.04, non Debian) trovato un altro
bug reale in `install.sh`: con `--web nginx` scelto esplicitamente
(necessario quando nessun web server è già installato — l'unico caso in
cui serve passare `--web` invece di lasciare `auto`), lo script non
installava mai il pacchetto. Il ramo che lo fa (`apt-get install nginx`)
gira solo quando `WEB=auto`; con `--web` esplicito quel ramo intero viene
saltato. L'installazione proseguiva convinta che nginx ci fosse già, e
falliva tardi — alla configurazione del vhost — con un errore poco
chiaro ("sites-available/anf.conf: No such file or directory") invece di
installarlo o di dirlo subito. Corretto: ora installa il web server
scelto se manca, in entrambi i casi (`auto` ed esplicito).

**Lezione confermata ancora una volta**: `docker-vps` aveva già nginx
preinstallato quando vi si è girato `install.sh` la prima volta in questa
sessione, per questo questo bug è rimasto invisibile fino a un'installazione
su una macchina davvero vergine.

`docker-2` è ora la seconda installazione Docker+Portainer completa e
funzionante di questo progetto, stesso schema di `docker-vps`: agent e
web server nativi, `anf-api` in Docker gestito da uno stack Portainer "da
repository Git" con `refs/heads/main` (aggiornamento con un click, senza
SSH). UID:GID identici (999:1000) fra i due server, per puro caso ma
comodo. MOTD personalizzata su `docker-2` (script in
`/etc/update-motd.d/99-docker2-info`, **non versionato nel progetto**:
è specifico di questa macchina, non fa parte del pacchetto di rilascio)
con IP, container Docker attivi e link a Portainer, colorata con icone.

## Stato alla v0.28.10 — 3 settembre 2026

Trovato un bug strutturale nel deploy Docker, non un accidente locale:
dopo che `anf-agent` si riavvia (anche solo per un `update.sh`), il
pannello nel container smette di raggiungere l'agent — "Agent non
raggiungibile su /run/anf/agent.sock" — pur con l'agent attivo e il socket
presente sull'host. Causa: `RuntimeDirectory=anf` nella unit fa cancellare
e ricreare `/run/anf` **ad ogni riavvio del servizio**, non solo al boot.
Il bind mount Docker verso quella cartella (`deploy/docker/docker-compose.yml`)
resta agganciato all'inode vecchio, ormai orfano — il container continua a
vedere una cartella vuota anche se sull'host `/run/anf` ha di nuovo il
socket. Serve ricreare il container per farlo riagganciare. Corretto con
`RuntimeDirectoryPreserve=yes` sulla unit: la cartella non viene più
ricreata tra un riavvio e l'altro del servizio, solo al riavvio della
macchina (quando comunque anche Docker riparte da zero e rimonta).

Nel diagnosticarlo, trovato un secondo bug indipendente ma nello stesso
punto: **`update.sh` non ha mai reinstallato le unit systemd** in
`/etc/systemd/system/` — sincronizzava solo la copia sorgente in
`deploy/systemd/`, e il commento nel codice descriveva già esattamente
questo problema ("systemd continua a usare la definizione vecchia") senza
che il codice sotto lo risolvesse davvero: faceva solo `daemon-reload`,
che rilegge quello che c'è già su disco, invariato. Qualunque correzione
a una unit rilasciata con un aggiornamento non aveva mai effetto finché
non si rieseguiva `install.sh` da capo — anche questa, come le altre
trappole di questa sessione, invisibile finché non si prova
l'aggiornamento per davvero.

**Lezione per [[wifi75-deploy-linux]]**: `RuntimeDirectory=` in una unit
systemd è sicuro per un servizio nativo isolato, ma **rischioso quando
un'altra cosa (un bind mount Docker, un altro processo) dipende dalla
persistenza di quella cartella tra un riavvio e l'altro del servizio** —
va quasi sempre accompagnato da `RuntimeDirectoryPreserve=yes` in quel
caso, altrimenti ogni riavvio rompe silenziosamente chi la usa dall'esterno.

## Stato alla v0.28.9 — 3 settembre 2026

Le due scorciatoie sotto "Condivisioni" nel menu laterale (`BarraLaterale.vue`)
erano link di solo testo, senza icona — l'utente le ha notate live
sull'installazione appena aggiornata e ha chiesto perché non avessero un
"pulsante grafico" come tutto il resto del menu. Portate allo stesso stile
a icona (`.voce` + `.pastiglia`) delle altre voci. Nel controllarle, trovata
anche un'etichetta sbagliata indipendente dallo stile: la chiave
`menu.tutteCondivisioni` mostrava il testo "Nuova condivisione"/"New share"
ma il link porta all'elenco di *tutte* le condivisioni esistenti
(`/condivisioni`), non alla creazione di una nuova — corretta in "Tutte le
condivisioni NFS"/"All NFS shares".

## Stato alla v0.28.8 — 3 settembre 2026

Secondo problema reale trovato con "Pull and redeploy" da Portainer (dopo
il fix `env_file` → volume della v0.28.7): "pull access denied for
advanced-nas-folder-api, repository does not exist". Portainer, prima di
ricreare il container, esegue `docker compose pull` — che cerca di
**scaricare** l'immagine da un registry. `advanced-nas-folder-api:local`
non è mai stata pubblicata da nessuna parte: si costruisce solo in locale
dal `Dockerfile` del progetto. Il tooltip nel form di Portainer indicava
già la soluzione: `pull_policy: build` nel servizio, che dice
esplicitamente "costruisci sempre, non scaricare mai" — aggiunto.

**Lezione per [[wifi75-deploy-linux]]**: un servizio Docker Compose con
`build:` ma senza un'immagine pubblicata su un registry va sempre marcato
`pull_policy: build`, non solo quando gira da CLI (`docker compose up`
senza `--pull` non ha questo problema) ma soprattutto quando un
orchestratore esterno (Portainer, ma anche CI/CD generici) fa un pull
esplicito prima del deploy — scenario che da riga di comando non si
presenta mai, quindi il bug è invisibile finché non si prova davvero il
flusso GitOps.

L'utente ha reagito con frustrazione visibile al susseguirsi di versioni
(v0.28.5 → v0.28.8 in un'ora) per completare un solo obiettivo
("aggiornare da Portainer"): ogni problema era scopribile solo provando
per davvero l'integrazione con Portainer, non dalla sola lettura del
codice — ma vale la pena, per la prossima volta che si integra con uno
strumento esterno non testabile in locale, avvisare in anticipo che
potrebbero servire più tentativi ravvicinati, invece di lasciare che la
sorpresa arrivi ad ogni nuovo errore.

## Stato alla v0.28.7 — 3 settembre 2026

Primo vero tentativo di deploy da Portainer (stack "da repository Git"):
falliva con "env file /var/www/advanced-nas-folder/.env not found",
nonostante il percorso fosse già assoluto (fix v0.28.5). **La v0.28.5 aveva
diagnosticato il sintomo giusto ma la causa sbagliata**: non è una
questione di percorso relativo vs assoluto, è che `env_file` nel compose
lo legge il *processo* che esegue `docker compose`, non il motore Docker —
e quando quel processo è Portainer, gira dentro il **suo** container, che
monta solo il socket Docker (verificato con `docker inspect portainer` —
solo `portainer_data` e `docker.sock`, niente dell'host). Nessun percorso
host, di nessun tipo, è visibile da lì.

Corretto sostituendo `env_file` con un **volume** di sola lettura verso lo
stesso file (`ANF_ENV_FILE`, stesso default): un volume lo risolve sempre
il demone Docker sull'host, mai il processo chiamante — funziona uguale da
CLI e da Portainer. `docker-entrypoint.sh` carica il file lui stesso
nell'ambiente (`set -a; . /run/secrets/anf.env; set +a`) prima di avviare
uvicorn.

**Lezione per [[wifi75-deploy-linux]]**: quando uno stack Docker deve
essere gestibile anche da un orchestratore che gira lui stesso in
container (Portainer, ma vale in generale), qualunque riferimento a un
file dell'host nel compose (`env_file`, bind mount di configurazione) va
verificato pensando a *chi* esegue davvero `docker compose` — non è
sempre l'host. I volumi sono sempre sicuri (li risolve il demone), i
meccanismi che leggono file lato client (`env_file`, `--env-file` da CLI)
non lo sono.

## Stato alla v0.28.6 — 3 settembre 2026

Applicata sul serio la v0.28.5 su `docker-vps` (192.168.1.224), primo test
reale di tutta la catena `update.sh`: si è fermato subito con "Manca
rsync" — `install.sh` non lo aveva mai installato, pur essendo un
requisito rigido di `update.sh`. Stessa lezione di v0.28.5: un comando
documentato ("cd RADICE && sudo bash update.sh") non era mai stato provato
per davvero prima d'ora su un'installazione reale di questo progetto.
Aggiunto `rsync` alla lista pacchetti di `install.sh`.

Dopo la correzione (rsync installato a mano su `docker-vps` per sbloccare
questo giro, poi anche nel codice per le prossime installazioni):
`update.sh` ha portato il codice nativo a 0.28.5 (rilevando da solo
`anf-api` in Docker, senza toccare quel servizio né la porta né nginx),
poi `docker compose build --pull && up -d` ha ricostruito il container con
l'`env_file` assoluto — verificato `healthy` e `"version":"0.28.5"` da
`/api/v1/health`. **La versione del container resterà "0.28.5" finché non
si ricostruisce di nuovo**: la v0.28.6 non tocca il backend, solo
`install.sh`, quindi non serve un altro rebuild per questo giro.

Resta da fare **dall'utente**, non da qui: configurare lo stack Portainer
"da repository Git" (valori già in `docs/DOCKER.md`/`.en.md`) — richiede
il login a Portainer, che non viene mai fatto da questa sessione.

## Stato alla v0.28.5 — 3 settembre 2026

`install.sh` non aveva mai copiato `update.sh`/`uninstall.sh`/
`README.en.md` dal pacchetto scaricato — solo `backend agent frontend
deploy docs` e quattro file specifici. La guida promette `update.sh` da
sempre, e su nessuna installazione reale c'era mai stato: scoperto solo
ora, aggiornando per la prima volta con `update.sh` invece di rieseguire
`install.sh`. Sintomo di una lezione più larga: **anche i comandi
documentati vanno provati per davvero**, non solo riletti nel codice —
per settimane nessuno aveva notato perché nessuno aveva mai eseguito
`update.sh` su un'installazione reale di questo progetto.

Richiesta esplicita dell'utente: l'aggiornamento del container deve poter
partire **direttamente da Portainer**, senza SSH. Questo richiede uno
stack "da repository Git" — Portainer clona il progetto da sé, in una
cartella che non è `/var/www/advanced-nas-folder` — il che rompeva
`env_file: ../../.env` in `docker-compose.yml` (percorso relativo, pensato
per essere lanciato dall'installazione nativa). Corretto in assoluto
(`/var/www/advanced-nas-folder/.env`, dove sta il `.env` coi segreti
reali), lasciando `build.context` relativo apposta: deve costruire dal
codice che Portainer ha appena clonato, non da quello dell'installazione
nativa. Documentata in `docs/DOCKER.md`/`.en.md` la configurazione esatta
dello stack (URL repo, riferimento, percorso compose, variabili
d'ambiente). Le due copie del codice — quella clonata da Portainer per
`anf-api`, quella dell'installazione nativa usata da `anf-agent` — restano
indipendenti: "Pull and redeploy" aggiorna solo la prima, `update.sh`
resta comunque necessario per la seconda.

Vale solo per `docker-vps` (192.168.1.224): unico server su cui si lavora
ora, per esplicita indicazione dell'utente. `folder.iu3cyv.eu` è fuori
scope, non toccato né pianificato in questo ciclo.

## Stato alla v0.28.4 — 3 settembre 2026

Corretto `update.sh`, che non sapeva che `anf-api` può girare in Docker
(v0.28.x, `docker-vps`): avrebbe provato a riavviare il servizio nativo
disabilitato, in conflitto di porta col container. Ora si accorge da solo
guardando se il servizio è abilitato, gestisce solo `anf-agent` quando è
in Docker, e ricorda il comando per ricostruire il container.
Corretta anche `docs/DOCKER.md`: la guida "Aggiornare" indicava
`docker compose build --pull`, che non riporta codice nuovo (aggiorna solo
l'immagine base di Python) — bug della documentazione, non solo di chi la
seguiva.

## Stato alla v0.28.3 — 3 settembre 2026

**Fase 4 della revisione grafica, completata — e con questa, tutto il
piano in quattro fasi è chiuso.** Vista pubblica di condivisione
(`ArchivioView.vue`) portata a un'identità a vetro (glassmorphism) propria,
separata dal ciano del pannello: nuovi token locali `--vetro-*-pub` su
`.archivio`, superfici rimaste piatte (header, barra strumenti, briciole,
errore, menu, finestre) portate allo stesso trattamento, `Caricamenti.vue`
e `AccessoCartella.vue` allineati. Aggiunta anche la pressione prolungata
per aprire il menu contestuale su touch (rinomina/sposta/elimina prima
raggiungibili solo col tasto destro del mouse).

**Limite dichiarato di questa sessione**: in questo ambiente di sviluppo
Windows non è stato possibile verificare righe/griglia/galleria con file
veri né il gesto di pressione prolungata — l'agent che monta i filesystem
NFS gira solo su Linux, e non c'è un touchscreen. Verificato solo ciò che
non richiede dati reali (stato di errore, barra strumenti) prima che
l'utente chiedesse di fermare le verifiche in autonomia e occuparsene lui
stesso.

## Stato alla v0.28.2 — 3 settembre 2026

**Fase 3 della revisione grafica, completata.** Corretto il bug
`data-theme`/`data-tema` in `AccessoCartella.vue` (la variante scura non
scattava mai). Consolidata la sagomatura bianca delle badge colorate in
`BarraLaterale.vue`, `GruppoCampi.vue`, `SelettoreLingua.vue` su
`var(--vetro-luce)` (già ritinto di ciano in v0.28.0), invece di tre copie
dello stesso valore hardcoded. Verificato — e lasciato com'è — che
`Anteprima.vue` non ha bisogno di riallineamento: il suo sfondo scuro
permanente è già vicino al nuovo `--sfondo`, ed è normale che un
visualizzatore di foto a schermo intero resti neutro.

**Resta solo la Fase 4** (pianificazione separata, non ancora iniziata):
la vista pubblica di condivisione (`ArchivioView.vue`) — identità e
layout da scegliere con l'utente, seguendo lo stesso processo (3-4
proposte pertinenti) usato per il pannello.

## Stato alla v0.28.1 — 3 settembre 2026

**Fase 2 della revisione grafica, completata — più leggera del previsto.**
Verificando da vicino `SharesView.vue`, `CondivisioneView.vue`,
`PubblicazioneView.vue`, `DettaglioShare.vue` (i target elencati nel piano
per il decluttering strutturale), sono risultate già ben organizzate con
schede a tab — non serviva la riorganizzazione prevista. Lezione: la stima
iniziale (fatta da un agente di ricerca su conteggio di righe/elementi)
sovrastimava il disordine reale; leggere il codice prima di agire ha
evitato lavoro non necessario. Trovato invece lavoro reale diverso: un
bottone ridondante, CSS morto da refactor incompleti in due file, e una
classe `.mono` usata ma mai definita in nessun posto raggiungibile (il
percorso NFS in `CondivisioneView.vue` non aveva mai avuto davvero il font
monospace). Font monospace unificato su `var(--font-mono)` in 9 file.

**Ancora da fare** (Fasi 3-4 del piano): `Anteprima.vue` ha colori scuri
hardcoded indipendenti dal tema, da riallineare al nuovo accento ciano; le
sagomature bianche copiate in più componenti (BarraLaterale, GruppoCampi,
SelettoreLingua, SelettoreTema) da portare al bagliore ciano; il bug in
`AccessoCartella.vue` (`data-theme` invece di `data-tema`, variante scura
mai raggiunta); poi la vista pubblica di condivisione (`ArchivioView.vue`),
identità separata da scegliere con l'utente.

## Stato alla v0.28.0 — 3 settembre 2026

**Fase 1 della revisione grafica del pannello, completata**: identità
"Dark Tech / Console" (accento ciano, verde acido, font mono per i dati,
angoli più netti, bagliore ciano sul vetro) e menu laterale riorganizzato
("Stato"/"Utenti" voci singole, scorciatoie separate dall'albero). Il
piano completo delle quattro fasi è descritto più sotto, in questa stessa
voce e nelle successive: non vive nel repository.

Verificato nel browser, non solo col gate: login con un database vuoto di
prova (mai toccato `dev.sqlite3`), tema chiaro e scuro. Trovato e corretto
un bug preesistente non legato alla nuova identità: `--fondo-pagina` non
era mai definita nel blocco `[data-tema='scuro']`, solo in quello di
`prefers-color-scheme` — chi sceglieva "Scuro" col sistema in chiaro
restava con la pagina illeggibile (testo chiaro su sfondo ancora chiaro).

**Ancora da fare** (Fasi 2-4 dello stesso piano, non iniziate):
decluttering strutturale di `SharesView.vue`, `CondivisioneView.vue`,
`PubblicazioneView.vue`/`DettaglioShare.vue`, `MountsView.vue`,
`WebServerView.vue`; poi `Anteprima.vue` (ha colori scuri hardcoded
indipendenti dal tema) e il consolidamento delle sagomature bianche
copiate in più componenti; poi la vista pubblica di condivisione
(`ArchivioView.vue`), identità separata da scegliere con l'utente quando
si arriva a quel punto.

## Stato alla v0.27.14 — 3 settembre 2026

Corretto: il menu del pannello poteva comparire a un visitatore esterno
(link di condivisione) se nello stesso browser era rimasta attiva una
sessione. `App.vue` decideva solo dall'autenticazione, non dal tipo di
rotta. Aggiunto `meta.senzaMenu` alle rotte `archivio` e `link`.

**In corso**: revisione grafica della vista pubblica di condivisione
(`ArchivioView.vue`, usata per `/archivio/:slug` e riusata anche per la
navigazione autenticata — 1636 righe, un solo componente per pubblico
esterno e amministrazione). Richiesta dell'utente, non ancora iniziata:
"pagina più chiara e fatta meglio, ottimizzata per smartphone". Ha anche
chiesto una revisione grafica dell'intero pannello di amministrazione,
motivo generico ("non sono soddisfatto"), da chiarire con lui prima di
scrivere codice.

## Stato alla v0.27.13 — 3 settembre 2026

Rivista la v0.27.12: togliere `container_name` lasciava Compose aggiungere
`-1` (suffisso di replica, inutile qui). Ripristinato `container_name`, ma
con l'identità del progetto già dentro (`advanced-nas-folder-anf-api`) invece
che un nome breve ambiguo — il meglio di entrambe le versioni precedenti.

## Stato alla v0.27.12 — 3 settembre 2026

Tolto anche `container_name: anf-api` esplicito dal compose Docker, per lo
stesso motivo del nome dello stack in v0.27.11: su un host con più
applicativi un nome breve fisso è ambiguo. Compose usa ora da solo
`<progetto>-<servizio>-<numero>`.

## Stato alla v0.27.11 — 3 settembre 2026

`anf-api` è ora davvero in produzione su Docker su `docker-vps`
(192.168.1.224), primo server a usare quella modalità: agent e Nginx
nativi, `anf-api` in container, verificato in Portainer. Lo stack Docker
Compose non aveva un nome esplicito e Compose lo deduceva dalla cartella
(`deploy/docker/` → stack "docker") — generico, si scontrerebbe con
qualunque altro progetto con la stessa convenzione sullo stesso host.
Aggiunto `name: advanced-nas-folder` nel compose.

## Stato alla v0.27.10 — 3 settembre 2026

Quinto problema della stessa sessione, il più insidioso: `install.sh`
diceva «Installazione completata» dopo un aggiornamento, ma il processo in
esecuzione restava quello vecchio (`enable --now` non riavvia un servizio
già attivo). Scoperto perché ho controllato `/api/v1/health` invece di
fidarmi dell'esito dichiarato — esattamente la disciplina che `memory.md`
raccomandava già per `update.sh` ("verificare sempre la versione con
/api/v1/health"), qui applicata anche a `install.sh`. Vedere «Trappole
trovate sul campo».

## Stato alla v0.27.9 — 3 settembre 2026

Quarto e ultimo problema della stessa sessione di installazione: aggiornando
un'installazione già attiva, `scegli_porta` trovava la porta occupata dal
servizio `anf-api` che stava per riavviare lui stesso, e ne sceglieva
un'altra per Nginx — disallineandolo da `.env` (lasciato intatto). Corretto
trattando "occupata solo da `anf-api.service`" come libera. Con questa,
`install.sh` è stato verificato end-to-end su un'installazione reale, non
solo riletto: prima installazione pulita e poi aggiornamento, entrambi senza
intervento a mano. Vedere «Trappole trovate sul campo».

## Stato alla v0.27.8 — 3 settembre 2026

Terzo problema nella stessa sessione di installazione su un server pulito
(Debian 13, Nginx): il sito "default" della distribuzione vinceva sempre su
`anf.conf`, pannello irraggiungibile con configurazione altrimenti valida.
`install.sh` ora lo rimuove da sé (solo se è ancora quello di serie). Non è
un limite di Debian: Ubuntu spedisce lo stesso pacchetto Nginx con lo stesso
sito abilitato — vedere «Trappole trovate sul campo».

## Stato alla v0.27.7 — 3 settembre 2026

Secondo bug trovato sullo stesso file installando davvero (non solo
rileggendo) su un server Debian pulito: la regex `{8,}` nella location degli
asset compilati non era tra virgolette, e il primo bug (`log_format`)
nascondeva questo finché non l'ho corretto. Lezione: dopo un fix a un file di
configurazione, testarlo per intero (`nginx -t` sul file reale), non solo
sulla parte appena cambiata — vedere «Trappole trovate sul campo».

## Stato alla v0.27.6 — 3 settembre 2026

Aggiunta l'installazione Docker per `anf-api` (v. voce sotto). Trovato e
corretto, installando su un secondo server (Debian 13, non Ubuntu) un bug
reale in `nginx.conf.tpl`: `log_format` dentro il blocco `server` fa fallire
sempre `nginx -t` su un'installazione pulita — vedere «Trappole trovate sul
campo» più sotto per il dettaglio, perché è del tipo che si ripresenta.

## Stato alla v0.27.5 — 3 settembre 2026

Solo documentazione: il codice e' quello della 0.27.4. Aggiunti ai README (IT/EN)
i badge SemVer, Keep a Changelog e Mantenuto, che il progetto seguiva gia' senza
dichiararlo in cima al README.

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

- **Uno script che gestisce servizi systemd per nome deve controllare se
  sono davvero gestiti così**, non darlo per scontato. `update.sh` provava
  a riavviare `anf-api` anche quando gira in Docker (disabilitato di
  proposito su quell'installazione) — conflitto di porta col container.
  Si accorge da solo con `systemctl is-enabled`, non serve un flag o una
  configurazione separata.
- **Due blocchi CSS con lo stesso selettore** nello stesso foglio, lontani fra
  loro, si annullano in silenzio. È già successo due volte in
  `views/ArchivioView.vue`, che ne ha ancora diversi: nessun linter lo segnala.
- **`mod_rewrite` e `CustomLog` non sono ereditati** dai VirtualHost; `mod_alias`
  (`Alias`, `RedirectMatch`) invece sì.
- **`log_format` di Nginx dentro il blocco `server` non è valido**: solo nel
  contesto `http`. `nginx.conf.tpl` lo aveva dentro `server` e `nginx -t`
  falliva sempre — su qualunque server pulito, non solo quello di prova.
  Corretto in v0.27.6 spostandolo fuori dal blocco: funziona perché Debian
  (e le distribuzioni derivate) include i file di `sites-enabled/` dentro il
  proprio blocco `http` in `nginx.conf`.
- **Una regex di location Nginx con `{` o `}` va tra virgolette**, altrimenti
  il parser la legge come apertura di blocco. `nginx.conf.tpl` aveva
  `{8,}` senza virgolette: mascherato dal bug precedente nella stessa
  release, emerso solo dopo averlo corretto (v0.27.7). Dopo un fix a un file
  di configurazione, va testato per intero, non solo sulla riga appena
  cambiata.
- **Il sito Nginx "default" di Debian/Ubuntu ha `listen 80 default_server`**,
  che vince sempre su `server_name _` non marcato come tale: `anf.conf`
  restava sintatticamente valido ma irraggiungibile (404 su tutto).
  `install.sh` lo rimuove da v0.27.8, solo se è ancora il sito di serie.
- **`libzstd-dev` mancante fa fallire l'avvio dell'API, non la compilazione
  di Python.** `./configure` salta `_zstd` in silenzio se la libreria non
  c'è; il primo errore visibile arriva solo all'avvio di `anf-api`
  (`ModuleNotFoundError: _zstd`, da `zipstream-ng`). Aggiunta alla lista dei
  pacchetti in `docs/INSTALL.md`.
- **Cercare una porta libera durante un aggiornamento trova se stessi.** Il
  servizio che si sta per riavviare occupa già la porta che gli si sta per
  riassegnare: `install.sh` la vedeva "occupata" e ne sceglieva un'altra per
  Nginx, disallineandolo da `.env` (lasciato intatto negli aggiornamenti).
  Corretto in v0.27.9: "occupata solo da `anf-api.service`" conta come
  libera, sia con `--porta` esplicita sia nella ricerca automatica.
- **`systemctl enable --now` su un servizio già attivo non lo riavvia.**
  `install.sh` lo usava per avviare agent e API: in un aggiornamento il
  codice nuovo arrivava sul disco ma il processo restava quello vecchio,
  e l'installer dichiarava comunque «completato». Corretto in v0.27.10 con
  `restart`, che funziona sia a freddo sia a caldo.
- **Un `docker-compose.yml` senza `name:` prende il nome dalla cartella di
  lancio**, non dal progetto. `deploy/docker/` dava stack "docker" in
  Portainer — collisione garantita con qualunque altro progetto che segua
  la stessa convenzione di cartella sullo stesso host. Aggiungere sempre
  `name:` esplicito ai compose di questo tipo di progetti.
- **`container_name` va bene fisso, ma con l'identità del progetto dentro.**
  Un nome breve (`anf-api`) è ambiguo su un host con più applicativi;
  lasciarlo del tutto implicito fa aggiungere a Compose un suffisso
  numerico di replica (`-1`) inutile per un servizio a istanza singola. La
  scelta giusta: `container_name: <progetto>-<servizio>`, esplicito e senza
  suffisso.
- **`deadsnakes` (Python 3.14 per `install.sh`) è specifico di Ubuntu**: su
  Debian non esiste affatto, e i repository apt di Debian stabile restano
  spesso una minor version indietro. Su Debian va compilato da sorgente con
  `make altinstall` (mai `make install`, che sovrascriverebbe `python3` di
  sistema) — comandi in `docs/INSTALL.md`, sezione «Su Debian». `install.sh`
  lo rileva comunque da solo se `python3.14` è già sul `PATH`: non serve
  modificarlo.
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

**Containerizzare l'agent o il web server.** Solo `anf-api` gira in Docker
(`docs/DOCKER.md`). L'agent resta un servizio nativo root perché genera unit
systemd sull'host: dargli accesso al systemd dell'host da dentro un container
(`--privileged` o socket D-Bus) non protegge nulla in più di un servizio
nativo, aggiunge solo indirezione. Il web server resta nativo perché deve
leggere i file dal filesystem dell'host per `X-Sendfile`/`X-Accel-Redirect`.

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
