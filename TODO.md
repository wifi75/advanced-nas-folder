# TODO — Advanced NAS Folder

Piano di sviluppo per fasi. Ogni fase produce qualcosa di installabile e usabile;
nessuna dipende da quelle successive.

---

## Fase 0 — Fondamenta `in corso`

- [x] Struttura del repository
- [x] Licenza MIT
- [x] README, piano tecnico, wiki NFS Synology
- [x] `.env.example` e `.gitignore`
- [x] Versioni verificate interrogando PyPI e npm — vedere [docs/VERSIONI.md](docs/VERSIONI.md)
- [x] Python 3.14 come requisito, installato accanto all'interprete di sistema
- [x] Scheletro backend FastAPI: configurazione, database, endpoint di health
- [x] Modelli del database: User, Mount, Share, AccessRule, ShareLink, Transfer,
      VHost, Setting — verificati creando davvero le tabelle su Python 3.14
- [x] Prima migrazione Alembic — verificata con `upgrade`, `downgrade` completo,
      risalita e `alembic check` senza differenze residue
- [x] Scheletro frontend Vue 3 + TypeScript + Vite — build, typecheck ed eslint
      puliti, pagine verificate nel browser in tema chiaro e scuro
- [x] Suite di test: 84 test su validatori dell'agent, sicurezza e accesso
- [x] Configurazione ruff unica in `ruff.toml`, valida anche per `agent/` e `tests/`
- [x] `install.sh` — bilingue, idempotente, con `--dry-run` e `--uninstall`.
      Verificato con shellcheck e prova a vuoto su server reale; installazione
      vera non ancora eseguita
- [x] Workflow CI: build di `dist/` e allegato alla release
- [x] **CI**: `ruff`, `mypy`, `pytest`, ESLint, `vue-tsc` e build a ogni push

## Fase 1 — Mount NFS dal pannello `in corso`

- [x] Autenticazione: login, token JWT, hash Argon2, sessioni
- [x] `anf-agent`: protocollo tipizzato su socket Unix, senza dipendenze esterne
- [x] Validatori: mountpoint confinati, whitelist delle opzioni
- [x] Generazione unit `.mount` / `.automount` da template
- [x] Scoperta delle condivisioni esportate dal NAS
- [x] Montaggio, smontaggio, stato *richiesto* vs *effettivo*, con prova di
      scrittura sul campo
- [x] API: endpoint dei mount collegati all'agent — elenco, scoperta, creazione,
      modifica, avvio, arresto, eliminazione
- [x] Interruttore scrittura, disattivato di default, con avviso quando il NAS la nega
- [x] Interfaccia: elenco mount, scoperta, creazione, avvio e arresto
- [x] Verifica end-to-end su Linux: pannello → API → agent → NAS reale
- [x] **Migrazione dei mount preesistenti da `/etc/fstab`**, con disattivazione
      della riga separata e copia di sicurezza

## Fase 2 — Pubblicazione e permessi `in corso`

- [x] Modello `Share`: cartella pubblicata a partire da un mount
- [x] `AccessRule` per prefisso di percorso, con risoluzione sicura dei percorsi
- [x] Visibilità del percorso: pubblica (anonima), password, utenti registrati,
      solo utenti autorizzati, negata
- [x] **Permessi per singolo utente**: quale utente accede a quale cartella, o a
      tutte. Divieto esplicito che batte la regola del percorso
- [x] **Endpoint delle pubblicazioni**: elenco, creazione, modifica, eliminazione,
      regole di visibilità per prefisso, permessi per utente
- [x] **Verifica dell'accesso** (`prova-accesso`): dice se un percorso è
      raggiungibile e *quale regola l'ha deciso*, anche in forma anonima
- [x] **Interfaccia delle pubblicazioni e dei permessi**: elenco, creazione, regole
      per cartella, permessi per utente e verifica dell'accesso nella stessa pagina
- [x] **Link di condivisione** con scadenza, limite di download e revoca, gestiti
      dentro la pubblicazione a cui appartengono
- [x] **Consegna dei file**: elenco della cartella filtrato voce per voce dal
      controllo degli accessi, e download delegato al web server con
      `X-Sendfile` o `X-Accel-Redirect`
- [x] Verifica del resume (Range, `If-Range`, ETag, 206)
- [ ] Barra di avanzamento del download lato utente *(il browser mostra già la
      propria; una barra nel pannello richiede di non delegare la consegna, e
      perderebbe la ripresa nativa — vedere la nota in fondo)*
- [x] **Gestione vhost dal pannello**, con anteprima, `configtest` e ripristino
      automatico della configurazione precedente
- [ ] Rimozione dell'alias pubblico preesistente *(si fa sul server, alla
      pubblicazione)*

## Fase 3 — Gestione file completa

- [x] **Icone per tipo di file**, una tinta per famiglia
- [ ] Viste a griglia e galleria
- [x] **Selezione multipla** con archivio dei soli elementi scelti
- [ ] Menu contestuale
- [x] **Crea, rinomina, sposta, copia, elimina, nuova cartella**, con conferma
      esplicita per le cartelle non vuote e permesso di scrittura richiesto su
      origine e destinazione
- [x] **Caricamento con trascinamento e avanzamento**, a blocchi e riprendibile
- [x] **Caricamento di cartelle intere**, ricostruendo l'albero
- [x] **Cartella come archivio ZIP**, prodotto mentre lo si invia

- [x] **Ricerca** nei nomi, ricorsiva e filtrata dai permessi
- [x] **Gestione utenti**: creazione, permessi generali, ambito per utente,
      attivazione e cambio della propria password

## Fase 4 — Monitoraggio e contenuti

- [x] **Lettura in tempo reale dell'access log**, con gestione della rotazione
- [x] **IP reali dietro il reverse proxy** (`X-Forwarded-For` dai soli proxy fidati)
- [x] **Cruscotto dei trasferimenti dal vivo** via SSE: file, indirizzo, byte, esito
- [ ] Avanzamento lato visitatore con pausa e ripresa *(vedi nota sui limiti)*
- [x] **Editor di testo**, con scrittura atomica
- [ ] Evidenziazione della sintassi nell'editor
- [x] **Anteprime**: immagini, video, audio, PDF e testo semplice
- [x] **Checksum SHA-256** calcolato su richiesta e mostrato nell'anteprima

## Fase 5 — Rifinitura

- [x] Tema chiaro, scuro o automatico *(anticipato su richiesta)*
- [x] Multilingua italiano e inglese *(anticipato su richiesta)*
- [x] **Marchio**: titolo, sottotitolo e logo personalizzabili
- [x] **Spazio sui dischi** e scelta se mostrare i file nascosti
- [x] **`update.sh` e `uninstall.sh`**
- [x] **Guida all'uso**, bilingue
- [ ] *(opzionale)* Integrazione API HAProxy per creare i sottodomini end-to-end

---

## Chiesto e non ancora fatto

Richieste del 2026-08-29 rimaste aperte alla chiusura della v0.3.0:

- [x] **Documentazione bilingue, parte rivolta a chi usa il progetto**: `README.en.md`,
      `docs/INSTALL.md` e `.en.md`, guida NFS Synology nelle due lingue, con i
      collegamenti fra le versioni.
- [x] **Documenti interni tradotti**: `docs/PIANO.en.md`, `docs/VERSIONI.en.md`
      e `agent/README.en.md`.
- [x] **PWA**: manifest, icone (comprese quelle ritagliabili), service worker con
      precache e API sempre escluse dalla cache, avviso di aggiornamento.
- [ ] **Da confermare su un browser vero**: la registrazione del service worker non
      è verificabile nel browser incorporato dello strumento di sviluppo, che la
      blocca — verificato che fallisca anche con un service worker di una riga.
      Tutto il resto (manifest, icone, contenuto della precache, esclusione
      dell'API, colori della barra) è stato controllato sul build.
- [ ] **Pubblicazione sul server.** Era la scelta di farla a sviluppo concluso, e
      con la v0.6.0 lo è. Il comando documentato nel README funziona: verificato
      scaricando `install.sh` e il pacchetto dalla release, checksum confermato e
      `dist/` compilato dalla CI presente. Da eseguire con `--dry-run` prima, poi
      per davvero. **Prima di pubblicare** vedere la voce sui test dell'agent
      qui sotto: vhost e fstab non sono mai stati provati su Linux.

## Emerso durante i rilasci

- [ ] **Test end-to-end dell'agent su Linux.** I test sono unitari e coprono
      validatori, generazione dei vhost e lettura di fstab; il ciclo dei mount è stato
      provato a mano contro un NAS reale, ma **vhost e fstab non sono mai stati
      eseguiti su Linux**, perché sulla macchina di sviluppo Windows i socket Unix
      non esistono. È la prima cosa da verificare al momento della pubblicazione.
- [x] Riferimenti a strumenti di terze parti nei piè di firma dei commit: rimossi
      riscrivendo la cronologia. Verificato che l'API di GitHub riporti un solo
      contributore.

## Limiti dichiarati, non difetti

- **L'avanzamento reale di un download non è visibile al pannello.** La consegna è
  delegata al web server, e da quel momento l'applicazione è uscita di scena. Il
  numero dei byte arriva dal suo access log a trasferimento concluso. Mostrare una
  percentuale richiederebbe di far passare i byte da Python, cioè rinunciare alla
  ripresa nativa e saturare i worker: non vale lo scambio.
- **Lo ZIP di una cartella non ha una percentuale**, perché viene prodotto mentre lo si
  invia e la dimensione totale non è nota in anticipo. L'alternativa sarebbe costruirlo
  prima su disco, e una cartella del NAS può pesare più dello spazio libero.
- **Due download dello stesso file dallo stesso indirizzo nello stesso istante** non si
  distinguono nel registro: l'access log non contiene un identificativo del
  trasferimento. È accettabile per un contatore.

## Non in programma, per scelta

- **Shell integrata e comandi personalizzati.** Esecuzione di codice remoto su un
  pannello esposto a Internet. Per amministrare il server c'è SSH.