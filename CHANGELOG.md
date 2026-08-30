# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate qui.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/)
e il versionamento segue [Semantic Versioning](https://semver.org/lang/it/).

## [Non rilasciato]

### Corretto
- **Il README dichiarava cose non vere.** Il banner di stato diceva che mancava la
  consegna dei file, fatta dalla v0.6.0; le funzionalità elencavano viste a griglia e
  galleria, che non esistono; il cruscotto prometteva «percentuale e velocità», che con
  la consegna delegata al web server non sono ottenibili. Corretto in entrambe le
  lingue, e aggiunta la nota che spiega perché quella percentuale non c'è.
- I collegamenti ai documenti interni nel README inglese puntavano alle versioni
  italiane, tradotte nel frattempo.

### Aggiunto
- Badge di **release**, **stato dei controlli** e **numero di test** nei due README:
  i primi due sono dinamici e dicono la verità da soli.
- README: sezione su `update.sh` e `uninstall.sh`, che esistevano senza essere
  documentati, e i comandi dei test e della formattazione fra quelli utili.

### Da fare
Vedere [TODO.md](TODO.md).

## [0.6.0] - 2026-08-30

Il pannello fa tutto quello per cui era stato pensato: i file si scaricano, si
caricano, si cercano e si modificano; gli utenti si creano; i trasferimenti si
vedono mentre succedono.

### Aggiunto
- **Consegna dei file**: le cartelle pubblicate si sfogliano e i file si scaricano.
  Il download lo esegue il web server, non l'applicazione: Python autorizza e passa
  il file con `X-Sendfile` (Apache) o `X-Accel-Redirect` (Nginx). Così la ripresa di
  un trasferimento interrotto funziona da sola — `Range`, `If-Range` ed `ETag` sono
  già implementati là — e un file grande non tiene occupato un worker.
- L'elenco di una cartella **filtra ogni voce con il controllo degli accessi**: una
  sottocartella vietata sparisce dall'elenco anche quando quella che la contiene è
  aperta a tutti. Nasconderla solo nell'interfaccia non servirebbe, visto che
  l'elenco resta leggibile via API.
- I collegamenti di download portano un **gettone valido pochi minuti e solo per quel
  percorso**, invece della password: una navigazione del browser non può portare
  intestazioni, e la query string finisce nei log del web server.
- I file che il browser eseguirebbe (HTML, SVG, XML) vengono serviti come
  `application/octet-stream`: con il loro tipo reale girerebbero nel contesto del
  pannello.
- Vista di navigazione dell'archivio, raggiungibile **anche senza accedere** quando la
  cartella è pubblica, con percorso navigabile, dimensioni, date e richiesta della
  password dove serve. Dall'elenco delle pubblicazioni un pulsante «Sfoglia» apre la
  cartella corrispondente.
- **Link di condivisione**: un modo per far arrivare una cartella a chi non ha un
  account e non lo avrà. Il token stesso è l'autorizzazione, limitata a un ramo, a una
  scadenza e a un numero di scaricamenti, e revocabile in qualunque momento.
  Facoltativamente protetto da una password.
- Due limiti il token non li supera, perché non sarebbero eccezioni ma buchi: non
  porta mai fuori dal ramo per cui è stato creato, e non apre un percorso marcato
  *negato*. Se un link superasse un divieto esplicito, crearne uno sarebbe il modo per
  aggirarlo.
- Nel database resta solo l'impronta SHA-256 del token, che perciò viene mostrato una
  volta sola, subito dopo la creazione.
- La revoca non cancella la riga: quante volte è stato usato un collegamento poi
  revocato è esattamente ciò che si vuole sapere dopo averlo revocato.
- Pagina dedicata a chi riceve un link — spoglia di proposito, senza menu né accesso al
  pannello, perché mostra soltanto il ramo che il collegamento concede.
- **Pubblicazione sul web server dal pannello**: si indica un nome host, si guarda
  l'anteprima della configurazione e la si applica. Il file generato non tocca quello
  scritto dall'installer.
- La configurazione viene **provata prima di essere applicata** con `apache2ctl
  configtest` o `nginx -t`, e **se il test non passa quella precedente torna al suo
  posto**. Un pannello che può lasciare il web server incapace di ripartire prima o poi
  lo mette fuori uso. L'esito del test compare nel messaggio d'errore: è l'unica cosa
  che spiega cosa correggere.
- La configurazione generata contiene le direttive delicate che finora andavano
  ricordate a mano — `XSendFilePath` su Apache, una `location` marcata `internal` su
  Nginx. Se mancano, i download rispondono vuoti; se sono scritte male, i file del NAS
  diventano raggiungibili saltando i permessi.
- **Operazioni sui file**: nuova cartella, rinomina, sposta, copia ed elimina, dal
  pannello. I pulsanti compaiono solo dove si ha il permesso di scrittura, e il
  controllo vero lo rifà comunque il server a ogni chiamata.
- Non si sovrascrive mai per sbaglio: se la destinazione esiste l'operazione fallisce e
  lo dice. Una cartella con dentro qualcosa si elimina solo con una conferma esplicita:
  chi crede di cancellarne una vuota non deve perderne il contenuto.
- Spostare richiede la scrittura su origine **e** destinazione — chiederla solo sulla
  destinazione permetterebbe di svuotare una cartella su cui non si ha alcun diritto.
  Copiare richiede solo di poter leggere l'origine, perché non la cambia.
- I nomi vengono controllati contro quelli che il NAS accetterebbe ma che poi risultano
  inapribili da SMB o da Windows: barre, due punti, nomi di dispositivo, nomi che
  finiscono con uno spazio.
- La scrittura viene verificata provandoci, non fidandosi di ciò che il pannello ha
  chiesto: se la regola NFS sul NAS è in sola lettura, il mount lo è.
- **Caricamento dei file**, con trascinamento, avanzamento e ripresa. Il file viene
  inviato a blocchi: su una rete domestica un file da qualche gigabyte non arriva al
  primo tentativo, e ricominciare da capo a ogni interruzione renderebbe la funzione
  inutile.
- **Lo stato della ripresa è il file parziale stesso**, non una riga in un database:
  quanti byte sono arrivati lo dice la sua dimensione. Non c'è nulla da tenere
  allineato, e un caricamento interrotto ieri riprende oggi senza che nessuno se ne sia
  dovuto ricordare.
- Il file parziale è nascosto e non compare fra i file: un caricamento a metà non deve
  sembrare un file scaricabile. Il completamento è una rinomina atomica, quindi non
  esiste un istante in cui il file esiste ma è incompleto.
- Un blocco inviato alla posizione sbagliata viene rifiutato invece che scritto:
  scriverlo comunque produrrebbe un file corrotto che nessuno nota fino all'apertura.
- ESLint conosce ora i nomi globali del browser. Prima non li dichiarava, e per farlo
  tacere si scriveva `globalThis.document` al posto di `document`: quei giri sono stati
  tolti.
- **Gestione degli utenti**: creazione, permessi generali, ambito, attivazione ed
  eliminazione. Finora i permessi per utente erano una funzione teorica, perché l'unico
  account esistente era l'amministratore creato dall'installazione.
- Due protezioni impediscono di rendere il pannello ingestibile: **non ci si può
  chiudere fuori da soli** (togliersi i privilegi, disattivarsi o cancellarsi) e
  **l'ultimo amministratore non si tocca**, nemmeno da parte di un altro amministratore.
- Il cambio della propria password richiede quella attuale anche a chi ha già effettuato
  l'accesso: un token rubato non deve bastare a chiudere fuori il proprietario.
- I permessi generali (cosa può fare una persona) restano separati dai permessi per
  cartella (dove può farlo): rispondono a domande diverse, e mescolarli renderebbe
  illeggibili entrambi.
- **Ricerca** nei nomi dei file, ricorsiva a partire dalla cartella in cui ci si trova.
  I risultati mostrano il percorso completo, così non si perde il contesto, e passano dal
  controllo degli accessi voce per voce: una ricerca che mostrasse i nomi dentro una
  cartella vietata sarebbe un modo di leggerne il contenuto.
- Due tetti — ai risultati e alle cartelle visitate — non sono opzioni ma parte del
  progetto: su NFS ogni cartella è un giro di rete, e senza limiti una ricerca su
  centomila file terrebbe occupato un thread per minuti.
- **Scaricare una cartella intera come archivio ZIP**. L'archivio viene prodotto mentre
  lo si invia, non costruito prima su disco: una cartella del NAS può pesare più dello
  spazio libero della macchina. Il prezzo è che il browser non mostra la percentuale,
  perché la dimensione totale non è nota in anticipo.
- I file entrano nell'archivio **senza compressione**: su un NAS domestico il contenuto è
  quasi sempre già compresso, e comprimerlo di nuovo consuma processore per guadagnare
  qualche per mille.
- **Selezione multipla**: si scelgono più file e cartelle e si scaricano in un unico
  archivio. La barra della selezione è fissa in basso invece che nel flusso, perché
  comparendo fra le voci sposterebbe l'elenco alla prima scelta e la casella successiva
  finirebbe sotto il dito di chi sta selezionando.
- Ogni elemento della selezione viene **risolto contro la radice e ricontrollato**: la
  selezione arriva dal client, e fidarsi di ciò che dichiara significherebbe lasciargli
  decidere cosa scaricare.
- **Icone per tipo di file**, con una tinta per famiglia — immagini, video, audio,
  archivi, documenti, codice. Il colore fa da indice visivo quando l'elenco è lungo,
  molto più del nome dell'estensione.
- **La CI esegue i controlli a ogni push**: `ruff`, `mypy`, `pytest`, ESLint, `vue-tsc` e
  build. Prima girava solo la build della release, e un errore di tipo o un test rotto si
  scopriva al momento di rilasciare, cioè nel momento peggiore.
- **Anteprime**: immagini, video, audio, PDF e testo semplice si aprono nel pannello
  invece di essere scaricati. Il server concede l'apertura in linea **solo a questi
  tipi**: farlo per un tipo qualunque significherebbe farlo interpretare dal browser, e
  un file caricato da altri diventerebbe codice eseguito nel contesto del pannello.
  HTML e SVG restano allegati anche se l'anteprima li chiede.
- **Checksum SHA-256** calcolato su richiesta. Risponde a una domanda precisa: il file
  arrivato è identico a quello che c'era? Confrontare le dimensioni non basta — due file
  diversi possono pesare uguale. Viene letto a blocchi, perché caricarlo in memoria lo
  renderebbe impossibile proprio sui file per cui serve di più.
- **Import dei montaggi già presenti in `/etc/fstab`**: il pannello li legge, propone un
  identificatore e li prende in gestione. Ricopiarli a mano significa riscrivere server,
  percorsi e opzioni senza sbagliare, e poi accorgersi di aver dimenticato una riga.
- Commentare la riga di fstab è **un'azione separata e successiva**: finché entrambi sono
  attivi il sistema prova a montare due volte lo stesso percorso, ma disattivare prima di
  aver verificato il mount del pannello lascerebbe la cartella irraggiungibile.
- La riga non viene mai cancellata: viene commentata con un marcatore che dice chi l'ha
  spenta e quando, dopo una copia di sicurezza del file. Una riga sbagliata in `/etc/fstab`
  può impedire l'avvio della macchina.
- L'import parte sempre in **sola lettura**, anche quando la riga di fstab concedeva la
  scrittura: la scrittura si concede di proposito, non per eredità.
- **Registro dei trasferimenti e cruscotto dal vivo**: cosa è stato scaricato e caricato,
  da chi e da quale indirizzo, con aggiornamento in tempo reale.
- Il flusso dal vivo usa **SSE e non WebSocket**: qui i dati vanno in una sola direzione,
  e un WebSocket dietro Apache richiede `mod_proxy_wstunnel` e una configurazione in più
  che qualcuno dimenticherà. Una risposta che non finisce mai passa da qualunque proxy.
- **`X-Forwarded-For` viene letto solo dai proxy dichiarati fidati**: quell'intestazione la
  può scrivere chiunque, e fidarsene sempre permetterebbe a ogni visitatore di dichiarare
  l'indirizzo che preferisce.
- **Lettura dell'access log del web server** per i byte davvero trasferiti, con gestione
  della rotazione: senza, dopo la prima rotazione notturna il monitoraggio smetterebbe di
  aggiornarsi in silenzio. Finché quei byte non arrivano restano vuoti — un numero
  inventato sarebbe peggio di uno assente.
- **Impostazioni del pannello**: nome, sottotitolo e logo personalizzabili, e la scelta
  se elencare anche i file nascosti. Titolo e logo si leggono anche senza accedere,
  perché disegnano la pagina di accesso.
- **Spazio sui dischi**, comprese le condivisioni montate. Quello del disco del pannello
  sta accanto agli altri di proposito: è quello che ci si dimentica, e se si riempie il
  pannello smette di funzionare anche con il NAS mezzo vuoto.
- **Editor di testo** nell'anteprima, dove si ha il permesso di scrivere. Il salvataggio
  scrive un file accanto e poi lo rinomina al posto dell'originale: se la scrittura si
  interrompe a metà, il file di partenza è ancora quello di prima.
- **Caricamento di cartelle intere**, ricostruendo l'albero dall'altra parte.
- 196 test nuovi. Suite complessiva a **375 test**.

### Modificato
- In sviluppo la consegna passa da sola a `stream`: senza un web server davanti,
  `X-Sendfile` produce risposte vuote che sembrano un difetto del codice.
- `ruff` non analizza più le migrazioni di alembic: sono generate, e riformattarle le
  farebbe divergere da ciò che il comando rigenera.

## [0.5.0] - 2026-08-29

Le cartelle si pubblicano e si proteggono dall'interfaccia, e il pannello si
installa sul telefono.

### Aggiunto
- **Endpoint delle pubblicazioni**: elenco, creazione, modifica ed eliminazione delle
  cartelle pubblicate, con regole di visibilità per prefisso di percorso e permessi
  assegnati ai singoli utenti.
- **`prova-accesso`**: dice se un percorso è raggiungibile e **quale regola l'ha
  deciso**, con o senza utente. Configurare permessi a prefissi senza poterli
  verificare significa scoprire gli errori quando è troppo tardi.
- I prefissi vengono normalizzati prima di essere salvati: `foto`, `/foto` e `/foto/`
  sono la stessa regola, e una sola regola per percorso è ammessa — due
  renderebbero la decisione dipendente dall'ordine di lettura.
- L'assegnazione di un permesso è idempotente (`PUT`): riassegnare lo stesso percorso
  allo stesso utente ne cambia il livello invece di creare un secondo permesso che
  contraddirebbe il primo.
- 20 test sugli endpoint. Suite complessiva a **179 test**.
- **Interfaccia delle pubblicazioni**: elenco, creazione con identificatore proposto
  dal nome, regole per cartella, permessi per utente e **verifica dell'accesso nella
  stessa pagina**, che dice se una cartella è raggiungibile e quale regola lo decide.
  La voce «Pubblicazioni» del menu non è più in attesa.

- **Applicazione installabile (PWA)**: manifest, icone generate a partire dalla
  pastiglia delle condivisioni NFS — compresa la variante ritagliabile che i sistemi
  richiedono per l'icona in schermata home — e service worker con precache dei file
  del pannello.
  - Le chiamate all'API sono **sempre escluse dalla cache**: mostrare uno stato del
    sistema non più reale, su un pannello che monta filesystem, è peggio di un errore
    di rete.
  - L'aggiornamento **non si applica da solo**: compare un avviso e decide chi sta
    lavorando. Ricaricare il codice mentre qualcuno configura un mount è peggio che
    restare una versione indietro per qualche minuto.
  - Colore della barra del browser diverso per tema chiaro e scuro.

### Corretto
- **Il pannello è servito sotto `/pannello/`, ma il frontend era compilato come se
  stesse alla radice del sito**: in produzione i file non sarebbero stati trovati.
  Impostata la base e allineato il router.
- Un percorso con risalita passato alla verifica dell'accesso produceva un errore
  interno invece di una risposta comprensibile.
- Nella verifica, lasciare vuoto il campo utente per provare l'accesso **anonimo**
  inviava una stringa vuota anziché «nessun utente»: la verifica falliva, e l'errore
  veniva pure inghiottito lasciando la pagina muta. Ora l'anonimo funziona e gli
  errori si vedono.

### Da fare
Vedere [TODO.md](TODO.md).

## [0.4.0] - 2026-08-29

Il progetto diventa installabile su un server, e i permessi arrivano al singolo
utente.

### Aggiunto
- **`deploy/install.sh`**: installazione su server Linux, con messaggi in italiano e
  in inglese. Idempotente, con `--dry-run` per vedere cosa farebbe e `--uninstall`
  che lascia intatti dati e mount. Installa Python 3.14 *accanto* all'interprete di
  sistema, rileva Apache o Nginx, e prima di ricaricare il web server ne verifica la
  configurazione: se non è valida ripristina la precedente, così un errore qui non
  ferma gli altri siti ospitati sulla macchina.
- Modelli di configurazione per Apache e Nginx, da includere in un vhost esistente
  invece di sostituirlo.
- **Permessi per singolo utente** (`PermessoUtente`): stabilire quale utente accede a
  quale cartella, o a tutte. Un divieto esplicito batte la regola del percorso, così
  si può togliere a una persona un ramo che per gli altri resta aperto.
- Nuova visibilità `utenti_scelti`: il percorso è riservato a chi ha un permesso
  esplicito. Restano disponibili l'accesso anonimo (`pubblica`), la password e
  l'accesso a tutti gli utenti autenticati.
- Livelli di permesso: negato, lettura, scrittura.
- **Documentazione bilingue** per chi usa e installa il progetto: `README.en.md`,
  `docs/INSTALL.md` e la sua versione inglese, guida alla scrittura NFS su Synology
  nelle due lingue, con i collegamenti reciproci in cima a ogni documento.
- `docs/INSTALL.md`: prerequisiti, verifica del NAS prima di installare, cosa fa
  l'installer passo per passo, aggiornamento, disinstallazione e risoluzione dei
  problemi più frequenti.
- **`avvia-dev.ps1`**: avvia backend e frontend in sviluppo come schede della stessa
  finestra di Windows Terminal, con ripiego a finestre separate, e stampa gli
  indirizzi. Controlla prima che ambiente Python, dipendenze e `.env` esistano.

### Cambiato
- In sviluppo i servizi ascoltano su **tutte le interfacce**, così il pannello si può
  provare da telefono o tablet. Aggiunto `allowedHosts` perché Vite rifiuta gli Host
  che non conosce, come difesa dal rebinding DNS. Opzione `-SoloLocale` per tornare
  ad ascoltare solo su `127.0.0.1`.
- Il README non dichiara più che l'installer manca: ora esiste.

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
- La cartella di configurazione locale dell'editor era finita nel repository: rimossa,
  con la regola di ignore in `.git/info/exclude` e non in `.gitignore`, che viene
  pubblicato e conterrebbe a sua volta il nome della cartella.

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
