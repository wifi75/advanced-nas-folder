#!/usr/bin/env bash
#
# Aggiornamento di Advanced NAS Folder.
#
# Scarica l'ultima release, la mette accanto a quella in uso e scambia le due
# cartelle solo quando la nuova ha superato i controlli. Se qualcosa non va, la
# versione precedente e' ancora al suo posto e viene rimessa in servizio.
#
#   curl -fsSL .../update.sh | sudo bash
#   sudo ./update.sh --versione v0.6.0
#   sudo ./update.sh --dry-run
#
set -Eeuo pipefail

APP="advanced-nas-folder"
RADICE="/var/www/${APP}"
REPO="wifi75/advanced-nas-folder"
SERVIZI=(anf-api anf-agent)

VERSIONE="ultima"
DRY_RUN=0
LINGUA="${ANF_LANG:-it}"

# --- messaggi ---------------------------------------------------------------

msg() {
    local it="$1" en="$2"
    if [ "$LINGUA" = "en" ]; then printf '%s\n' "$en"; else printf '%s\n' "$it"; fi
}

passo() { printf '\n\033[1;36m==>\033[0m %s\n' "$1"; }
errore() { printf '\033[1;31mErrore:\033[0m %s\n' "$1" >&2; exit 1; }

uso() {
    cat <<'FINE'
Uso: update.sh [opzioni]

  --versione TAG   Aggiorna a una versione precisa (es. v0.6.0)
  --dry-run        Mostra cosa farebbe, senza toccare nulla
  --lang it|en     Lingua dei messaggi
  -h, --help       Questo testo
FINE
}

while [ $# -gt 0 ]; do
    case "$1" in
        --versione) VERSIONE="${2:?}"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --lang) LINGUA="${2:?}"; shift 2 ;;
        -h|--help) uso; exit 0 ;;
        *) errore "Opzione sconosciuta: $1" ;;
    esac
done

esegui() {
    if [ "$DRY_RUN" = 1 ]; then printf '    [prova] %s\n' "$*"; else "$@"; fi
}

# --- controlli --------------------------------------------------------------

[ "$(id -u)" = 0 ] || errore "$(msg 'Serve root: usa sudo.' 'Root required: use sudo.')"
[ -d "$RADICE" ] || errore "$(msg "Installazione non trovata in $RADICE." "No installation found in $RADICE.")"

for strumento in curl tar rsync sha256sum; do
    command -v "$strumento" >/dev/null ||
        errore "$(msg "Manca $strumento: installalo e riprova." "Missing $strumento: install it and retry.")"
done

# --- scaricamento -----------------------------------------------------------

passo "$(msg 'Scarico la nuova versione' 'Downloading the new version')"

TEMPORANEA="$(mktemp -d)"
trap 'rm -rf "$TEMPORANEA"' EXIT

if [ "$VERSIONE" = "ultima" ]; then
    URL="https://github.com/${REPO}/releases/latest/download/${APP}.tar.gz"
else
    URL="https://github.com/${REPO}/releases/download/${VERSIONE}/${APP}.tar.gz"
fi

if [ "$DRY_RUN" = 0 ]; then
    curl -fsSL "$URL" -o "$TEMPORANEA/pacchetto.tar.gz" ||
        errore "$(msg "Scaricamento fallito da $URL" "Download failed from $URL")"

    # La somma di controllo e' pubblicata accanto al pacchetto: verificarla
    # costa nulla ed e' l'unica cosa che distingue un aggiornamento da un file
    # arrivato a meta'.
    if curl -fsSL "${URL}.sha256" -o "$TEMPORANEA/atteso.sha256" 2>/dev/null; then
        ATTESO="$(cut -d' ' -f1 <"$TEMPORANEA/atteso.sha256")"
        OTTENUTO="$(sha256sum "$TEMPORANEA/pacchetto.tar.gz" | cut -d' ' -f1)"
        [ "$ATTESO" = "$OTTENUTO" ] ||
            errore "$(msg 'Il pacchetto scaricato non corrisponde alla sua somma di controllo.' \
                          'The downloaded package does not match its checksum.')"
    fi

    mkdir -p "$TEMPORANEA/nuova"
    tar -xzf "$TEMPORANEA/pacchetto.tar.gz" -C "$TEMPORANEA/nuova"
fi

# --- sostituzione -----------------------------------------------------------

passo "$(msg 'Fermo i servizi' 'Stopping services')"
for s in "${SERVIZI[@]}"; do
    esegui systemctl stop "$s" || true
done

passo "$(msg 'Metto da parte la versione in uso' 'Setting aside the running version')"
PRECEDENTE="${RADICE}.precedente"
esegui rm -rf "$PRECEDENTE"
esegui cp -a "$RADICE" "$PRECEDENTE"

ripristina() {
    printf '\033[1;33m%s\033[0m\n' \
        "$(msg 'Aggiornamento fallito: rimetto la versione precedente.' \
                'Update failed: restoring the previous version.')"
    rm -rf "$RADICE"
    mv "$PRECEDENTE" "$RADICE"
    for s in "${SERVIZI[@]}"; do systemctl start "$s" || true; done
    exit 1
}

if [ "$DRY_RUN" = 0 ]; then
    trap ripristina ERR

    # Il file di configurazione e il database restano dove sono: appartengono
    # all'impianto, non al programma.
    rsync -a --delete \
        --exclude '.env' \
        --exclude 'venv' \
        "$TEMPORANEA/nuova/" "$RADICE/"

    passo "$(msg 'Aggiorno le dipendenze' 'Updating dependencies')"
    "$RADICE/venv/bin/pip" install -q -e "$RADICE/backend"

    passo "$(msg 'Applico le migrazioni del database' 'Applying database migrations')"
    (cd "$RADICE/backend" && "$RADICE/venv/bin/alembic" upgrade head)
fi

# Senza, systemd continua a usare la definizione caricata all'avvio e avvisa
# che il file su disco e cambiato: i servizi ripartono con la versione vecchia
# dell'unit, e la correzione appena installata non ha effetto.
passo "$(msg 'Ricarico le unit systemd' 'Reloading systemd units')"
esegui systemctl daemon-reload

passo "$(msg 'Riavvio i servizi' 'Restarting services')"
for s in "${SERVIZI[@]}"; do
    esegui systemctl start "$s"
done

# --- verifica ---------------------------------------------------------------

if [ "$DRY_RUN" = 0 ]; then
    passo "$(msg 'Verifico che risponda' 'Checking that it responds')"
    PORTA="$(grep -oP '^ANF_PORT=\K\d+' "$RADICE/.env" 2>/dev/null || echo 8100)"

    PRONTO=0
    for _ in $(seq 1 20); do
        if curl -fsS "http://127.0.0.1:${PORTA}/api/v1/health" >/dev/null 2>&1; then
            PRONTO=1
            break
        fi
        sleep 1
    done
    [ "$PRONTO" = 1 ] || ripristina

    trap - ERR
    rm -rf "$PRECEDENTE"
fi

passo "$(msg 'Aggiornamento completato.' 'Update complete.')"
