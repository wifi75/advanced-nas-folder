#!/bin/sh
# Il container non ha un passo di installazione separato come install.sh:
# applica le migrazioni ad ogni avvio (e' idempotente se non ce n'e' di
# nuove), poi parte.
set -e

alembic upgrade head

# --host e' sempre 0.0.0.0 dentro il container, non ANF_HOST: quest'ultimo
# nel .env resta "127.0.0.1" per il caso nativo. Nel container l'unico modo
# di raggiungerlo dall'host e' il mapping di porta di docker-compose, gia'
# limitato a 127.0.0.1 — la stessa proprieta' di sicurezza, applicata a un
# livello diverso.
exec uvicorn app.main:app --host 0.0.0.0 --port "${ANF_PORT:-8100}" --proxy-headers
