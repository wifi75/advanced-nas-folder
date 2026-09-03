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

Le miniature delle immagini le produce **Pillow**, installata con le altre
dipendenze Python: la sua distribuzione per Linux include già le librerie di
compressione, quindi non serve nessun pacchetto di sistema in più. Le miniature
finiscono in `/var/lib/anf/miniature`, **non sul NAS**: scriverle nel mount
sporcherebbe le cartelle condivise, e richiederebbe un permesso di scrittura
che di norma non c'è.
| accesso **root** | l'installer crea utenti, servizi e mount |

Su Apache serve anche **`mod_xsendfile`**, senza il quale i download rispondono
vuoti: **lo installa e lo abilita l'installer**, insieme a `mod_remoteip` e ai moduli
proxy. Non c'è nulla da preparare a mano.

**Node.js non serve sul server**: il frontend viene compilato dalla CI e distribuito
già pronto nella release.

Sviluppato e verificato su **Ubuntu 24.04 LTS**. Su altre distribuzioni l'installer
va adattato: usa `apt-get` e il PPA `deadsnakes`.

### Su Debian (niente `deadsnakes`)

`deadsnakes` è un PPA specifico di Ubuntu: su Debian non esiste, e i repository di
Debian stabile restano spesso una minor version indietro rispetto a quella richiesta.
Va compilato da sorgente, **accanto** all'interprete di sistema:

```bash
apt-get install -y build-essential libbz2-dev libffi-dev libgdbm-dev \
  libgdbm-compat-dev liblzma-dev libncurses5-dev libreadline6-dev \
  libsqlite3-dev libssl-dev tk-dev uuid-dev zlib1g-dev wget xz-utils

cd /usr/local/src
wget https://www.python.org/ftp/python/3.14.7/Python-3.14.7.tgz
tar -xzf Python-3.14.7.tgz && cd Python-3.14.7
./configure --prefix=/usr/local --with-ensurepip=install
make -j"$(nproc)"
make altinstall   # MAI "make install": sovrascriverebbe python3 di sistema
```

`make altinstall` installa `python3.14` senza toccare `python3`. Una volta sul
`PATH`, `install.sh` lo trova da solo e salta il passo `deadsnakes`: non serve
modificare l'installer. Pulire dopo con `rm -rf /usr/local/src/Python-3.14.7*`.

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
2. **Installa i pacchetti mancanti**: `curl`, `nfs-common`, `openssl`, `ffmpeg`.
   Quest'ultimo serve solo alle miniature dei video: senza, i video restano con
   l'icona del tipo e tutto il resto funziona lo stesso.
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
   | `/var/lib/anf` | database SQLite e miniature delle immagini |
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

## I byte trasferiti, e perché a volte non compaiono

Il pannello sa **quando** un download è stato autorizzato, ma non quanti byte
sono arrivati: da quel momento il file lo invia il web server. Il numero vero
lo scrive lui nel proprio access log, ed è da lì che il pannello lo legge.

Perché possa farlo servono due cose, che l'installer sistema da sé:

1. **L'utente `anf` deve poter leggere il log.** Su Debian e Ubuntu gli access
   log sono di `root`, gruppo `adm`, non leggibili da altri: l'installer
   aggiunge `anf` a quel gruppo.
2. **La riga `CustomLog` deve stare dentro il VirtualHost** che serve il
   pannello. Una `CustomLog` nella configurazione di server vale solo per le
   richieste che *non* finiscono in un vhost, e i vhost non la ereditano.

Se manca la seconda, il file di log resta vuoto e nella pagina **Trasferimenti**
ogni riga rimane «in corso» per sempre. La riga da copiare nel vhost è:

```apache
CustomLog /var/log/apache2/anf_access.log anf
```

`LogFormat`, invece, è globale: basta definirlo una volta, e lo fa già
`anf.conf`.

## Indirizzi corti delle cartelle pubblicate

Il pannello vive sotto `/pannello/`, quindi l'indirizzo completo di una cartella
pubblicata è `https://sito/pannello/archivio/documenti`. È corretto, ma non è un
indirizzo che si detta al telefono.

Per ogni pubblicazione attiva viene quindi generata una **scorciatoia sulla radice
del sito**: `https://sito/documenti` porta allo stesso posto. Il file
`anf-scorciatoie.conf` viene riscritto per intero a ogni modifica, a partire
dall'elenco delle pubblicazioni: una scorciatoia non può sopravvivere alla
pubblicazione che l'aveva creata.

Tre cose da sapere, perché sono scelte e non limiti accidentali:

- **Viene generata una regola per ogni pubblicazione, mai una che cattura tutto.**
  Il sito ospita quasi sempre anche altro: una regola generica ne oscurerebbe i
  contenuti, e lo farebbe in silenzio.
- **Sono redirezioni, non riscritture interne.** Il pannello è un'applicazione a
  pagina singola servita sotto `/pannello/`, e il suo router non riconoscerebbe un
  indirizzo che parte dalla radice: il browser prosegue quindi sull'indirizzo lungo,
  che resta quello visibile nella barra.
- **Solo su Apache.** Su Nginx le `location` devono stare dentro il blocco `server`,
  quindi un file a sé non sarebbe configurazione valida. Il pannello lo dice invece
  di scrivere qualcosa che non funziona.

I nomi `pannello`, `api`, `server-status` e `server-info` sono rifiutati: una
scorciatoia `/pannello` renderebbe il pannello irraggiungibile, e a quel punto non
ci sarebbe più modo di toglierla.

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

`update.sh` viene installato **nella cartella dell'applicazione**: è uno strumento
dell'applicazione, e il posto dove cercarlo è la sua cartella.

```bash
cd /var/www/advanced-nas-folder && sudo bash update.sh
```

Lo script si ricopia da solo in una cartella temporanea e riparte da lì, perché è
proprio la cartella dell'applicazione che riscrive: bash legge lo script mentre lo
esegue, e sostituirlo a metà corsa interromperebbe l'aggiornamento in un punto
qualunque.

Non tocca `.env` né il database, ricarica le unit systemd e verifica che l'API
risponda. **Se qualcosa fallisce rimette la versione precedente e la riavvia.**

In alternativa si può rieseguire l'installer, che è idempotente:

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

## Eseguire l'API in Docker invece che nativa

Il servizio `anf-api` può girare in un container invece che nativamente — agent e web
server restano nativi in entrambi i casi. Vedi [DOCKER.md](DOCKER.md).

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
