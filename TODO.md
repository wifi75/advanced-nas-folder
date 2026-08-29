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
- [ ] `install.sh` funzionante end-to-end
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

## Fase 2 — Pubblicazione e permessi

- [ ] Modello `Share`: cartella pubblicata a partire da un mount
- [ ] `AccessRule` per prefisso di percorso
- [ ] Visibilità: pubblica / password / utenti registrati / link con scadenza
- [ ] Link di condivisione con limite di download e revoca
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

- [ ] Tema chiaro/scuro, branding, titolo e logo personalizzabili
- [ ] Multilingua
- [ ] Spazio disco nella barra laterale, nascondere i file nascosti
- [ ] `update.sh` e `uninstall.sh`
- [ ] Documentazione utente completa
- [ ] *(opzionale)* Integrazione API HAProxy per creare i sottodomini end-to-end

---

## Emerso durante i rilasci

- [ ] **Test end-to-end dell'agent su Linux.** I test attuali sono unitari e coprono
      i validatori; il ciclo completo (creazione, montaggio, stato, rimozione) è stato
      provato a mano contro un NAS reale, ma non è automatizzato. Serve un ambiente di
      prova con systemd.
- [ ] **Decisione in sospeso:** i commit precedenti al 29 agosto 2026 contengono un
      riferimento a uno strumento di terze parti nel piè di firma. Toglierlo richiede
      di riscrivere la cronologia e un force-push, che non è stato ancora autorizzato.

## Non in programma, per scelta

- **Shell integrata e comandi personalizzati.** Esecuzione di codice remoto su un
  pannello esposto a Internet. Per amministrare il server c'è SSH.
