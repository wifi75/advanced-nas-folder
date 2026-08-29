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
- [ ] CI: eseguire anche `ruff`, `mypy` e `pytest` a ogni push, non solo il build

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
- [ ] Migrazione dei mount preesistenti da `/etc/fstab`

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
- [ ] Link di condivisione con scadenza, limite di download e revoca
- [ ] Download delegato: `X-Sendfile` e `X-Accel-Redirect`
- [ ] Verifica del resume (Range, `If-Range`, ETag, 206)
- [ ] Gestione vhost dal pannello, con `configtest` e ripristino automatico
- [ ] Rimozione dell'alias pubblico preesistente

## Fase 3 — Gestione file completa

- [ ] Navigazione, viste elenco / griglia / galleria, icone per tipo
- [ ] Menu contestuale, selezione multipla
- [ ] Crea, rinomina, sposta, copia, elimina, nuova cartella
- [ ] Upload drag&drop con avanzamento, upload di cartelle
- [ ] Upload a blocchi riprendibile
- [ ] Download multiplo e cartella come archivio
- [ ] Ricerca
- [ ] Multiutente: ambito per utente, permessi granulari, regole allow/deny

## Fase 4 — Monitoraggio e contenuti

- [ ] Lettura in tempo reale dell'access log del web server
- [ ] `mod_remoteip` + `X-Forwarded-For` per gli IP reali dietro il reverse proxy
- [ ] Dashboard download live via WebSocket: file, IP, percentuale, velocità
- [ ] Avanzamento lato visitatore con pausa e ripresa
- [ ] Editor di testo e codice con evidenziazione sintassi
- [ ] Anteprime: immagini, video, audio, PDF, epub
- [ ] Checksum SHA-256 calcolato e mostrato

## Fase 5 — Rifinitura

- [x] Tema chiaro, scuro o automatico *(anticipato su richiesta)*
- [x] Multilingua italiano e inglese *(anticipato su richiesta)*
- [ ] Branding, titolo e logo personalizzabili
- [ ] Spazio disco nella barra laterale, nascondere i file nascosti
- [ ] `update.sh` e `uninstall.sh`
- [ ] Documentazione utente completa
- [ ] *(opzionale)* Integrazione API HAProxy per creare i sottodomini end-to-end

---

## Chiesto e non ancora fatto

Richieste del 2026-08-29 rimaste aperte alla chiusura della v0.3.0:

- [x] **Documentazione bilingue, parte rivolta a chi usa il progetto**: `README.en.md`,
      `docs/INSTALL.md` e `.en.md`, guida NFS Synology nelle due lingue, con i
      collegamenti fra le versioni.
- [ ] **Documenti interni ancora solo in italiano**: `docs/PIANO.md`,
      `docs/VERSIONI.md` e `agent/README.md`. Sono documenti di sviluppo, non
      di installazione: tradurli ha meno urgenza ma resta da fare.
- [ ] **PWA**: pannello installabile sul telefono, icona in schermata home.
- [ ] **Pubblicazione sul server, alla fine dello sviluppo.** Sul server non è
      ancora stato pubblicato nulla. Dalla v0.4.0 il comando documentato nel
      README funziona davvero: verificato scaricando `install.sh` e il pacchetto
      dalla release, checksum confermato e `dist/` compilato dalla CI presente.
      Da eseguire con `--dry-run` prima, poi per davvero.

## Emerso durante i rilasci

- [ ] **Test end-to-end dell'agent su Linux.** I test attuali sono unitari e coprono
      i validatori; il ciclo completo (creazione, montaggio, stato, rimozione) è stato
      provato a mano contro un NAS reale, ma non è automatizzato. Serve un ambiente di
      prova con systemd.
- [x] Riferimenti a strumenti di terze parti nei piè di firma dei commit: rimossi
      riscrivendo la cronologia. Verificato che l'API di GitHub riporti un solo
      contributore.

## Non in programma, per scelta

- **Shell integrata e comandi personalizzati.** Esecuzione di codice remoto su un
  pannello esposto a Internet. Per amministrare il server c'è SSH.
