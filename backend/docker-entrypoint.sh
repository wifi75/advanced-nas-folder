#!/bin/sh
# Il container non ha un passo di installazione separato come install.sh:
# applica le migrazioni ad ogni avvio (e' idempotente se non ce n'e' di
# nuove), poi parte.
set -e

# Il .env applicativo arriva come volume montato (docker-compose.yml), non
# come "env_file". "env_file" viene letto dal PROCESSO che esegue
# `docker compose`, non dal motore Docker: se a lanciarlo e' Portainer (che
# gira dentro un proprio container, con solo il socket Docker montato, senza
# /var/www dell'host) quel percorso non esiste dal suo punto di vista e la
# build fallisce, anche se il file c'e' davvero sull'host. Un volume invece
# lo risolve sempre il demone Docker sull'host, indipendentemente da chi ha
# invocato compose: per questo il file arriva qui come bind mount, e questo
# script lo carica lui stesso nell'ambiente prima di partire.
if [ -f /run/secrets/anf.env ]; then
    set -a
    # shellcheck disable=SC1091
    . /run/secrets/anf.env
    set +a
fi

alembic upgrade head

# --host e' sempre 0.0.0.0 dentro il container, non ANF_HOST: quest'ultimo
# nel .env resta "127.0.0.1" per il caso nativo. Nel container l'unico modo
# di raggiungerlo dall'host e' il mapping di porta di docker-compose, gia'
# limitato a 127.0.0.1 — la stessa proprieta' di sicurezza, applicata a un
# livello diverso.
exec uvicorn app.main:app --host 0.0.0.0 --port "${ANF_PORT:-8100}" --proxy-headers
