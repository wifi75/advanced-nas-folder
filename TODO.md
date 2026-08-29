# TODO — Advanced NAS Folder

Piano di sviluppo per fasi. Ogni fase produce qualcosa di installabile e usabile;
nessuna dipende da quelle successive.

---

## Fase 0 — Fondamenta `in corso`

- [x] Struttura del repository
- [x] Licenza MIT
- [x] README, piano tecnico, wiki NFS Synology
- [x] `.env.example` e `.gitignore`
- [ ] **Verificare le versioni provvisorie** in `backend/pyproject.toml` e
      `frontend/package.json`. Sono confermate con ricerca: FastAPI 0.141.1,
      Vue 3.5.33, Vite 8.0.9, PostgreSQL 18.6, Node 24.18.1. Le altre dipendenze
      sono state fissate senza verifica e vanno controllate prima della prima
      installazione reale.
- [ ] Scheletro backend FastAPI con `core/version.py` e endpoint di health
- [ ] Scheletro frontend Vue 3 + TypeScript + Vite
- [ ] Modelli e prima migrazione Alembic
- [ ] `install.sh` funzionante end-to-end
- [ ] Workflow CI: build di `dist/` e allegato alla release

## Fase 1 — Mount NFS dal pannello

- [ ] Autenticazione: login, token JWT, hash Argon2, sessioni
- [ ] `anf-agent`: protocollo tipizzato su socket Unix, senza dipendenze esterne
- [ ] Validatori: mountpoint confinati, whitelist delle opzioni
- [ ] Generazione unit `.mount` / `.automount` da template
- [ ] Scoperta delle condivisioni esportate dal NAS
- [ ] Montaggio, smontaggio, stato *richiesto* vs *effettivo*
- [ ] Interruttore scrittura, disattivato di default, con avviso di rischio
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

## Non in programma, per scelta

- **Shell integrata e comandi personalizzati.** Esecuzione di codice remoto su un
  pannello esposto a Internet. Per amministrare il server c'è SSH.
