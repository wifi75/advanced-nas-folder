# Advanced NAS Folder

Pannello self-hosted che **monta condivisioni NFS**, **pubblica cartelle con permessi
per sottocartella** e sostituisce integralmente FileBrowser — senza che tu debba mai
modificare a mano un file di configurazione del server.

> **Stato: fase 0 — fondamenta.** Il progetto è in costruzione. Questa versione
> contiene struttura, documentazione e decisioni architetturali. Vedere
> [TODO.md](TODO.md) per il piano delle fasi.

---

## Perché esiste

Pubblicare una cartella di un NAS sul web di solito significa: montarla a mano in
`/etc/fstab`, scrivere un `Alias` nella configurazione di Apache, e accontentarsi di
un elenco di file senza permessi né controllo. Se il mount cade, l'elenco diventa
silenziosamente vuoto e nessuno se ne accorge.

Advanced NAS Folder porta tutto questo dentro un pannello: scopri le condivisioni del
NAS, le monti con un clic, decidi chi vede cosa fino al livello della singola
sottocartella, e vedi in tempo reale chi sta scaricando.

## Funzionalità

**Mount NFS** — scoperta automatica delle condivisioni esportate dal NAS, montaggio e
smontaggio dal pannello, opzioni scelte da whitelist, stato *richiesto* e stato
*effettivo* sempre visibili. Non tocca mai `/etc/fstab`: genera unit systemd, una per
mount, così un errore resta isolato e non impedisce l'avvio del server.

**Pubblicazione e permessi** — cartelle pubblicate come *share*, con regole di accesso
per prefisso di percorso: pubblica, protetta da password, riservata a utenti
registrati, o link con scadenza e limite di download.

**Gestione file** — navigazione con viste elenco / griglia / galleria, upload
drag&drop riprendibile, download di cartelle come archivio, editor di testo e codice,
anteprime, ricerca, multiutente con ambiti e permessi granulari.

**Download** — la consegna dei file è delegata al web server (`X-Sendfile` su Apache,
`X-Accel-Redirect` su Nginx): Python non tocca mai il contenuto, e il *resume* delle
richieste interrotte funziona in modo nativo. Dashboard in tempo reale con file, IP
reale del client, percentuale e velocità.

## Sicurezza

Il pannello esegue operazioni privilegiate (montare filesystem, scrivere
configurazioni del web server) senza mai girare da root:

| Processo | Utente | Ruolo |
|---|---|---|
| `anf-api` | `anf`, non privilegiato | applicazione web, non tocca il sistema |
| `anf-agent` | `root` | esegue le operazioni privilegiate, ascolta solo su socket Unix locale |

Fra i due passano **comandi tipizzati**, mai stringhe di shell. L'agent valida ogni
richiesta: i mountpoint sono confinati sotto `ANF_MOUNT_ROOT`, le opzioni di mount
vengono da una whitelist, e ogni modifica alla configurazione del web server passa da
`apache2ctl configtest` (o `nginx -t`) **prima** del reload, con ripristino automatico
se il test fallisce.

Due scelte deliberate:

- **La scrittura sui mount è disattivata di default.** Va abilitata esplicitamente,
  con avviso di rischio, e richiede che sia consentita anche lato NAS
  ([guida](docs/synology-nfs-scrittura.md)).
- **La shell integrata e i comandi personalizzati di FileBrowser non sono
  replicati.** Su un pannello raggiungibile da Internet sono esecuzione di codice
  remoto per definizione.

## Requisiti

- Linux con systemd (sviluppato e testato su Ubuntu 24.04 LTS)
- Apache con `mod_xsendfile`, **oppure** Nginx
- Python 3.12 o superiore
- Nessun server di database: i dati stanno in un file SQLite
- `nfs-common` per i mount NFS

Node.js **non** è richiesto sul server: il frontend viene compilato dalla CI e
distribuito già pronto nella release.

## Installazione

```bash
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh
sha256sum install.sh
sudo bash install.sh
```

Lo script è volutamente da scaricare, controllare ed eseguire in tre passi separati:
si esegue da root, quindi merita che tu possa leggerlo prima. Rileva da solo se il
server usa Apache o Nginx e installa la configurazione corrispondente.

Aggiornamento con `sudo bash update.sh`, rimozione con `sudo bash uninstall.sh`.

## Configurazione

Tutte le voci sono documentate in [`.env.example`](.env.example). I segreti
(`ANF_SECRET_KEY`, password del database) vengono generati da `install.sh` e scritti
solo in `.env`, con permessi `0600`. Nel repository non è presente alcun dato reale.

## Documentazione

- [Piano tecnico completo](docs/PIANO.md) — architettura, stack, roadmap
- [Abilitare la scrittura NFS su Synology](docs/synology-nfs-scrittura.md)
- [TODO.md](TODO.md) — stato delle fasi

## Licenza

[MIT](LICENSE) — Copyright © 2026 Tiziano Cassone

---

Ideato e sviluppato da Tiziano Cassone
