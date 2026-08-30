# Installazione

🇬🇧 [English version](INSTALL.en.md)

Guida completa all'installazione di Advanced NAS Folder su un server Linux.

---

## Prima di cominciare

| Serve | Perché |
|---|---|
| **Linux con systemd** | i mount e i servizi sono unit systemd |
| **Apache** *oppure* **Nginx** | consegnano i file al posto dell'applicazione |
| **Python 3.14 o superiore** | il codice usa sintassi introdotta in quella versione |
| **`nfs-common`** | per montare le condivisioni |
| accesso **root** | l'installer crea utenti, servizi e mount |

Su Apache serve anche **`mod_xsendfile`**, senza il quale i download rispondono
vuoti: **lo installa e lo abilita l'installer**, insieme a `mod_remoteip` e ai moduli
proxy. Non c'è nulla da preparare a mano.

**Node.js non serve sul server**: il frontend viene compilato dalla CI e distribuito
già pronto nella release.

Sviluppato e verificato su **Ubuntu 24.04 LTS**. Su altre distribuzioni l'installer
va adattato: usa `apt-get` e il PPA `deadsnakes`.

### Il NAS

Prima di installare, controlla due cose sul NAS:

1. **La cartella è esportata verso l'indirizzo del server.** Su Synology:
   *Pannello di controllo → Cartella condivisa → Modifica → Permessi NFS*.
2. **Quale versione di NFS espone.** Molti NAS offrono solo la v3, e chiedere la v4
   fa fallire il montaggio con un messaggio poco chiaro (`Protocol not supported`).
   Dal server:

   ```bash
   rpcinfo -p INDIRIZZO_NAS | grep nfs
   ```

   Se compaiono solo `2` e `3`, userai NFSv3. Il pannello se ne accorge da solo e
   disabilita le versioni non disponibili.

Per abilitare la **scrittura** vedi la [guida dedicata](synology-nfs-scrittura.md):
va abilitata sia sul NAS sia nel pannello, e sbagliare l'impostazione di *squash*
rende i file caricati ingestibili da File Station.

---

## Installazione

L'installer si scarica, si controlla e si esegue in **passi separati**: gira da root,
quindi merita che tu possa leggerlo prima.

**Scaricalo da una cartella tua**, per esempio `/root`. Non da `/var/www`: lì
l'installer ci si installa da solo, e lasciarci in mezzo anche il file di
installazione confonde le cose.

```bash
cd /root
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh
```

Guarda cosa hai scaricato, prima di darlo a root:

```bash
sha256sum install.sh
less install.sh
```

### Prima la prova a vuoto

Mostra tutto quello che farebbe — comandi compresi — senza toccare niente. Su un
server che ospita altri siti non è un'opzione: è il primo passo.

```bash
sudo bash install.sh --dry-run
```

Da qui vedi già le tre cose che contano: quale web server ha trovato, **quali porte
sono occupate e da chi**, e dove finirà ogni cosa.

### Poi l'installazione vera

```bash
sudo bash install.sh
```

Ti fa alcune domande, e per ognuna **basta Invio** per accettare quello che propone:

| Domanda | Predefinito |
|---|---|
| quale web server usare — *solo se ne hai due installati* | quello trovato |
| dove montare le condivisioni del NAS | `/srv/nas` |
| dove installare il programma | `/var/www/advanced-nas-folder` |
| dove tenere database e dati | `/var/lib/anf` |
| **quale porta** per l'API | la prima libera dalla 8100 |

Sulla porta ti mostra le prime cinque libere e, se la 8100 è occupata, **da quale
servizio**. Puoi scriverne una qualsiasi, anche fuori da quell'elenco: se è occupata o
non è valida te lo dice e te la richiede, senza far ricominciare tutto.

Alla fine arriva il **riepilogo di cosa verrà installato e dove**, con la conferma. È
l'ultimo momento per fermarsi prima che qualcosa venga scritto.

I messaggi escono nella lingua del sistema. Per forzarla: `--lingua it` o `--lang en`.

> **Se usi `curl … | sudo bash` l'installer non ti chiede niente** e decide da solo.
> Non è un difetto: in quel modo non ha un terminale da cui leggere, e restare fermo
> ad aspettare una risposta che non arriverà sarebbe peggio. Funziona, ma perdi le
> domande — scarica il file se le vuoi.

### Opzioni

| Opzione | Cosa fa |
|---|---|
| `--dry-run` | mostra cosa farebbe, senza applicare nulla |
| `--web apache` \| `nginx` | forza il web server invece di rilevarlo |
| `--porta 8110` | porta interna dell'API. Senza, viene scelta la prima libera dalla 8100 |
| `--lingua it` \| `en` | lingua dei messaggi |
| `--sorgente /percorso` | installa da una cartella locale invece che dalla release |
| `--uninstall` | rimuove servizi e programma |

### La porta non è fissa

L'API ascolta su una porta locale, dietro il web server. Su una macchina che ospita
già altre applicazioni trovare la 8100 occupata è il caso normale, non un'eccezione.

Senza domande — cioè con `curl | bash` o con `--dry-run` — l'installer prende la prima
libera a partire dalla 8100 e dice quale ha scelto.

Con `--porta` si indica invece una porta precisa: se quella è occupata l'installer
**si ferma** invece di spostarsi da solo. Chi l'ha indicata aveva un motivo, e
ritrovarsi il pannello altrove sarebbe peggio di un errore.

Il numero scelto finisce in `.env` (`ANF_PORT`) e nella configurazione del web
server, che restano coerenti fra loro.

---

## Cosa fa l'installer, passo per passo

1. **Controlla i prerequisiti**: root, Linux, systemd.
2. **Installa i pacchetti mancanti**: `curl`, `nfs-common`, `openssl`.
3. **Installa Python 3.14** dal PPA `deadsnakes`, se assente. Viene installato
   **accanto** all'interprete di sistema, che non viene toccato: spostare `python3`
   romperebbe il sistema operativo e le altre applicazioni della macchina.
4. **Rileva Apache o Nginx**, e su Apache abilita `mod_xsendfile`, `mod_remoteip` e i
   moduli proxy.
5. **Crea l'utente di sistema `anf`**, senza shell di accesso.
6. **Prepara le cartelle**:

   | Percorso | Contenuto |
   |---|---|
   | `/var/www/advanced-nas-folder` | programma |
   | `/var/lib/anf` | database SQLite |
   | `/srv/nas` | punti di montaggio |
   | `/run/anf` | socket dell'agent |

7. **Scarica la release** e la scompatta.
8. **Crea l'ambiente Python** e installa le dipendenze.
9. **Genera `.env`** con segreti casuali, permessi `0600`. Se esiste già, lo lascia.
10. **Applica le migrazioni** del database.
11. **Installa i due servizi systemd**.
12. **Configura il web server** — e prima di ricaricarlo ne verifica la
    configurazione. Se non è valida, ripristina la precedente e si ferma: senza
    questo controllo un errore qui fermerebbe *tutti* i siti ospitati sulla
    macchina, non solo questo.
13. **Avvia i servizi** e verifica che l'API risponda.

---

## Dopo l'installazione

### Primo accesso

Il pannello risponde su `/pannello` del web server: dall'indirizzo di rete
della macchina, non solo da `localhost`. Per esempio
`http://192.168.1.106/pannello/`.

La porta che l'installer ti ha chiesto **non c'entra con questo indirizzo**: è
il canale interno fra il web server e l'applicazione, in ascolto solo su
`127.0.0.1`. Puntarci il browser da un'altra macchina dà connessione rifiutata,
ed è voluto. Se pubblichi il pannello attraverso un firewall o un reverse proxy,
inoltra la **80/443**, mai quella porta.

Al primo avvio viene creato l'utente amministratore:

| | |
|---|---|
| **Utente** | `admin` |
| **Password** | `Admin1234` |

Il pannello mostra un avviso in evidenza finché la password resta questa.

> **Cambiala prima di rendere il pannello raggiungibile da Internet.** È scritta
> qui in chiaro apposta — è pubblica per chiunque legga questa pagina, quindi
> non protegge nulla: serve solo a farti entrare la prima volta.

### Indirizzi reali dei visitatori

Se davanti al server c'è un reverse proxy che termina il TLS, senza configurazione
ogni visitatore risulta avere l'indirizzo del proxy, e il monitoraggio dei download
non distingue nessuno.

Nel file generato dall'installer aggiungi gli indirizzi dei tuoi proxy:

```bash
RemoteIPTrustedProxy 192.168.1.2
```

e in `.env`:

```bash
ANF_TRUSTED_PROXIES=127.0.0.1,192.168.1.2
```

### Controllare che funzioni

```bash
systemctl status anf-agent anf-api
```

```bash
curl -fsS http://127.0.0.1:$(grep -oP '^ANF_PORT=\K\d+' /var/www/advanced-nas-folder/.env)/api/v1/health
```

---

## Altri nomi host, dal pannello

L'installer configura il primo vhost (`anf.conf`). Per pubblicare il pannello
anche su un altro nome host non serve tornare sul server: dalla voce **Web
server** del menu si indica il nome, si guarda l'anteprima della
configurazione e la si applica.

Il file generato si chiama `anf-<nomehost>.conf` e non tocca quello
dell'installer. Prima di applicarla, la configurazione viene provata con
`apache2ctl configtest` o `nginx -t`: **se il test non passa, quella
precedente torna al suo posto** e il pannello mostra l'errore riportato dal
web server.

Restano fuori dal pannello, di proposito: DNS, certificati e ascolto in
HTTPS. Vivono a monte, tipicamente su un reverse proxy, e generare
configurazioni che fingono di gestirli produrrebbe file che non
corrispondono all'impianto reale.

## Aggiornare

Riesegui l'installer: è idempotente e **non tocca `.env` né il database**.

```bash
curl -fsSLO https://github.com/wifi75/advanced-nas-folder/releases/latest/download/install.sh && sudo bash install.sh
```

## Disinstallare

```bash
sudo bash install.sh --uninstall
```

Rimuove servizi, configurazione del web server e programma. **Non tocca** il database
in `/var/lib/anf` né i mount in `/srv/nas`: se vuoi rimuovere anche quelli, va fatto a
mano e con cognizione.

---

## Se qualcosa non va

### L'API non risponde

```bash
journalctl -u anf-api -n 50 --no-pager
```

Le cause più frequenti: `.env` con una chiave assente, o il database non
raggiungibile perché i permessi di `/var/lib/anf` non appartengono all'utente `anf`.

### L'agent non parte

```bash
journalctl -u anf-agent -n 50 --no-pager
```

L'agent **si rifiuta di partire se non gira da root**: è voluto, monta filesystem e
non deve degradare in silenzio.

### Il pannello dice che l'agent non è raggiungibile

Verifica il socket e i suoi permessi: deve essere di `root`, gruppo `anf`, `0660`.

```bash
ls -la /run/anf/
```

### Il montaggio fallisce con `Protocol not supported`

Non è un problema di permessi ma di versione: la configurazione chiede NFSv4 e il NAS
espone solo la v3. Verifica con `rpcinfo -p INDIRIZZO_NAS` e imposta la versione 3
nel pannello.

### La cartella risulta in sola lettura anche se hai chiesto la scrittura

È il NAS che la sta negando, e il pannello te lo dice esplicitamente. Vedi la
[guida sulla scrittura NFS](synology-nfs-scrittura.md).
