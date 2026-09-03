# Installazione con Docker

🇬🇧 [English version](DOCKER.en.md)

Guida all'esecuzione di **anf-api** in un container, in alternativa al
servizio systemd nativo.

---

## Cosa containerizza, e cosa no

Solo `anf-api`. L'agent privilegiato (`anf-agent`) e il web server
(Apache/Nginx) **restano servizi nativi sull'host**, non containerizzati.

Non è una scelta provvisoria: è la stessa separazione dei privilegi descritta
in [PIANO.md](PIANO.md#nodo-1--montare-filesystem-richiede-root). L'agent gira
da root e genera unit systemd `.mount`/`.automount` sull'host — una unit
isolata non può danneggiare il resto del sistema se è sbagliata, un mount
fatto dentro un container privilegiato sì. Spostare l'agent in un container
richiederebbe di dargli accesso completo al systemd dell'host (`--privileged`
o il socket D-Bus), che non protegge nulla in più di un servizio nativo e
aggiunge solo un livello di indirezione. Il web server resta nativo per lo
stesso motivo del Nodo 2 del piano tecnico: consegna i file con `X-Sendfile`
/ `X-Accel-Redirect` leggendo direttamente dal filesystem dell'host, e deve
vedere lo stesso mount NFS che vede l'agent.

## Prerequisiti

**L'installazione nativa va fatta comunque, prima.** Serve a creare l'utente
di sistema `anf`, il servizio `anf-agent`, il web server e le cartelle
(`/var/lib/anf`, `/srv/nas`, `/run/anf`) — vedi [INSTALL.md](INSTALL.md).
Docker sostituisce **solo** il servizio systemd `anf-api`, non l'installer.

| Serve | Perché |
|---|---|
| Installazione nativa già fatta | agent, web server e cartelle esistono già |
| Docker Engine con plugin Compose | `docker compose version` deve rispondere |

## Installazione

Scoprire UID e GID dell'utente creato dall'installer:

```bash
id anf
```

Copiare l'esempio e compilarlo con i valori trovati e i percorsi reali
dell'impianto (di norma coincidono con i predefiniti se non sono stati
cambiati durante l'installazione nativa):

```bash
cd /var/www/advanced-nas-folder/deploy/docker
cp .env.example .env
nano .env
```

Fermare il servizio nativo — il container userà la stessa porta:

```bash
sudo systemctl disable --now anf-api
```

Costruire e avviare:

```bash
docker compose up -d --build
```

Verificare:

```bash
docker compose logs -f anf-api
curl -fsS http://127.0.0.1:$(grep -oP '^ANF_PORT=\K\d+' ../../.env)/api/v1/health
```

Il container legge la configurazione applicativa dallo stesso `.env` alla
radice del progetto usato dall'installazione nativa — nessun segreto duplicato.

## Aggiornare

`docker compose build` costruisce l'immagine dal codice sorgente **già
presente sul disco**, in `/var/www/advanced-nas-folder/backend`: da solo non
scarica una versione più recente del progetto. `--pull` aggiorna solo
l'immagine di base di Python, non il codice — un errore facile da fare,
capitato anche qui la prima volta che questa guida è stata scritta.

Il codice si aggiorna con lo stesso `update.sh` dell'installazione nativa,
che da questa versione riconosce da solo che `anf-api` gira in Docker (perché
il suo servizio systemd è disabilitato) e non prova a riavviarlo — gestisce
solo `anf-agent` e sincronizza i file:

```bash
cd /var/www/advanced-nas-folder && sudo bash update.sh
```

Alla fine stampa da sé il comando per ricostruire il container col codice
appena arrivato:

```bash
cd deploy/docker && docker compose build --pull && docker compose up -d
```

Le migrazioni del database girano comunque da sole a ogni avvio del
container (`docker-entrypoint.sh`), oltre a quelle già applicate da
`update.sh`: idempotenti, non fanno danno a ripetersi.

## Aggiornare da Portainer, con un click

In alternativa al giro manuale sopra: Portainer sa gestire uno stack
**direttamente dal repository Git**, cloni il progetto da sé e ricostruisce
l'immagine dal codice appena scaricato quando si preme "Pull and redeploy" —
non serve più collegarsi via SSH per aggiornare il container.

**Perché il `.env` applicativo arriva come volume e non come `env_file`.**
`env_file` nel compose lo legge il **processo che esegue `docker compose`**,
non il motore Docker — e quando a lanciarlo è Portainer, quel processo gira
**dentro il container di Portainer stesso**, che ha montato solo il socket
Docker, non il filesystem dell'host: nessun percorso host, assoluto o
relativo, è visibile da lì. Un volume invece lo risolve sempre il **demone
Docker sull'host**, indipendentemente da chi ha chiamato `docker compose` —
funziona identico da riga di comando e da Portainer. Per questo il compose
monta il `.env` reale come volume di sola lettura
(`${ANF_ENV_FILE:-/var/www/advanced-nas-folder/.env}`) e
`docker-entrypoint.sh` lo carica lui stesso nell'ambiente prima di partire.

Il contesto di build (`../../backend`) resta invece relativo di proposito:
deve costruire dal codice che Portainer ha appena clonato, non da quello
dell'installazione nativa — altrimenti "Pull and redeploy" scaricherebbe il
codice nuovo senza usarlo davvero.

**Perché `pull_policy: build`.** "Pull and redeploy" prova prima a
*scaricare* l'immagine da un registry — ma `advanced-nas-folder-api:local`
non esiste su nessun registry, si costruisce solo in locale dal
`Dockerfile`. Senza questa riga il pull fallisce con "pull access denied".
`pull_policy: build` dice esplicitamente di costruire sempre, mai
scaricare.

**Prerequisito**: l'installazione nativa resta comunque necessaria (agent,
web server, cartelle, e soprattutto il `.env` reale con i segreti — non
finisce mai nel repository, quindi Portainer non può portarselo da solo).

Configurazione dello stack, in Portainer:

1. **Stacks → Add stack → Repository**.
2. **Repository URL**: `https://github.com/wifi75/advanced-nas-folder.git`.
3. **Reference**: `refs/heads/main` (o un tag preciso, es. `refs/tags/v0.28.8`,
   per non aggiornarsi da soli a ogni push).
4. **Compose path**: `deploy/docker/docker-compose.yml`.
5. **Environment variables**, da inserire a mano nel modulo di Portainer
   (sono le stesse di `deploy/docker/.env.example`, Portainer non legge quel
   file da un repository Git): `ANF_UID`, `ANF_GID` (da `id anf` sull'host),
   `ANF_ENV_FILE` (di norma non va cambiato: `/var/www/advanced-nas-folder/.env`),
   `ANF_DATA_DIR`, `ANF_MOUNT_ROOT`, `ANF_SOCKET_DIR`, `ANF_PORT` — stessi
   valori usati nell'installazione nativa.
6. Deploy the stack.

Da quel momento, aggiornare significa aprire lo stack in Portainer e premere
**"Pull and redeploy"**: Portainer scarica l'ultimo commit del riferimento
scelto e ricostruisce il container da lì. Il codice sorgente sul disco
dell'installazione nativa (`/var/www/advanced-nas-folder/backend`, quello
usato da `agent`) resta comunque aggiornato **solo** da `update.sh` — le due
copie del codice (quella clonata da Portainer, quella dell'installazione
nativa) sono indipendenti, e vale la pena tenerle allineate lanciando
entrambe quando si aggiorna.

## Perché la porta resta solo su `127.0.0.1`

Il processo dentro il container ascolta per forza su `0.0.0.0`, perché nel suo
namespace di rete `127.0.0.1` non sarebbe raggiungibile dall'host. La stessa
proprietà di sicurezza dell'installazione nativa — irraggiungibile da fuori la
macchina — è garantita qui dal mapping di porta di `docker-compose.yml`
(`127.0.0.1:PORTA:PORTA`), non dal bind interno del processo. Non cambiare
quel mapping per esporre il pannello direttamente: passa dal reverse proxy
o dal web server, come nell'installazione nativa.

## Se le condivisioni montate dopo l'avvio non si vedono nel container

I mount NFS li gestisce `systemd` sull'host, anche dopo che il container è
partito — l'`automount` monta alla prima richiesta. Il volume di
`/srv/nas` è dichiarato con propagazione `rslave` apposta per farli comparire
senza riavviare nulla. Se sul sistema la propagazione dei mount non è
condivisa (raro, di norma systemd la imposta così di default), riavviare il
container:

```bash
docker compose restart anf-api
```

## Tornare al servizio nativo

```bash
docker compose down
sudo systemctl enable --now anf-api
```

## Limiti dichiarati, non difetti

- **Nessuna immagine per l'agent.** Vedi «Cosa containerizza, e cosa no»
  sopra: è una decisione, non un pezzo mancante.
- **Nessuna immagine per il web server.** Stesso motivo: deve leggere i file
  dal filesystem dell'host per `X-Sendfile`/`X-Accel-Redirect`.
