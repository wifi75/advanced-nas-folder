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

```bash
docker compose build --pull && docker compose up -d
```

Le migrazioni del database girano da sole a ogni avvio del container
(`docker-entrypoint.sh`), quindi non serve un passo separato — a differenza
dell'installazione nativa, dove le applica l'installer.

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
