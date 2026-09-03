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

# Se anf-api gira in Docker (docs/DOCKER.md), il servizio systemd nativo e'
# disabilitato di proposito: fermarlo/riavviarlo qui non farebbe nulla di
# utile, e "start" andrebbe in conflitto sulla porta con il container gia' in
# ascolto. Si rileva da solo controllando se e' abilitato — un'installazione
# nativa lo ha sempre abilitato, una in Docker mai.
SERVIZI=(anf-agent)
ANF_API_IN_DOCKER=0
if systemctl is-enabled anf-api >/dev/null 2>&1; then
    SERVIZI+=(anf-api)
else
    ANF_API_IN_DOCKER=1
fi

VERSIONE="ultima"
DRY_RUN=0
LINGUA="${ANF_LANG:-it}"

# --- lo script si toglie di mezzo da solo ------------------------------------
#
# Il posto naturale di questo file e la cartella dell'applicazione: e uno
# strumento dell'applicazione, non un file sparso in /root. Ma e proprio quella
# cartella che l'aggiornamento riscrive, e bash legge lo script mentre lo
# esegue: sostituirlo a meta corsa interromperebbe l'aggiornamento in un punto
# qualunque.
#
# Quindi, se e in esecuzione da dentro l'installazione, la prima cosa che fa e
# ricopiarsi altrove e ripartire da li. Da quel momento la cartella si puo
# riscrivere in pace.
if [ "${ANF_RILOCATO:-0}" != 1 ] && [ -f "${BASH_SOURCE[0]}" ]; then
    _sorgente="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
    case "$_sorgente" in
        "$RADICE"/*)
            _copia="$(mktemp)"
            cp "$_sorgente" "$_copia"
            export ANF_RILOCATO=1
            exec bash "$_copia" "$@"
            ;;
    esac
fi

# --- messaggi ---------------------------------------------------------------

msg() {
    local it="$1" en="$2"
    if [ "$LINGUA" = "en" ]; then printf '%s\n' "$en"; else printf '%s\n' "$it"; fi
}

# Colori solo su un terminale vero: rediretto in un file o in una pipe, le
# sequenze di escape sporcherebbero l'output senza colorare nulla.
if [ -t 1 ]; then
    C_PIU=$'\033[32m'; C_MENO=$'\033[31m'; C_MOD=$'\033[33m'; C_FINE=$'\033[0m'
else
    C_PIU=""; C_MENO=""; C_MOD=""; C_FINE=""
fi

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

# --- resoconto delle modifiche ----------------------------------------------

# Traduce l'output di `rsync --itemize-changes` in righe leggibili.
#
# Il formato di rsync e un codice di undici caratteri seguito dal percorso:
# `>f+++++++++` per un file nuovo, `*deleting` per uno rimosso, e per uno gia
# presente le lettere dicono *cosa* e cambiato (dimensione, data, permessi).
# Qui serve solo la distinzione fra aggiunto, rimosso e modificato: il resto e
# dettaglio che nessuno legge.
mostra_cambiamenti() {
    local file="$1" riga aggiunti=0 rimossi=0 modificati=0

    while IFS= read -r riga; do
        case "$riga" in
            "*deleting"*)
                printf "  "%s"- %s"%s"\n" "$C_MENO" "${riga:12}" "$C_FINE"
                rimossi=$((rimossi + 1))
                ;;
            ?f+++++++++*|?d+++++++++*|?L+++++++++*)
                printf "  "%s"+ %s"%s"\n" "$C_PIU" "${riga:12}" "$C_FINE"
                aggiunti=$((aggiunti + 1))
                ;;
            ?f.........*|?d.........*)
                # Attributi tutti a punto: rsync l'ha esaminato e non e
                # cambiato niente. Contarlo gonfierebbe il resoconto.
                ;;
            ?f*)
                printf "  "%s"~ %s"%s"\n" "$C_MOD" "${riga:12}" "$C_FINE"
                modificati=$((modificati + 1))
                ;;
        esac
    done <"$file"

    if [ $((aggiunti + rimossi + modificati)) -eq 0 ]; then
        msg 'Nessun file cambiato: eri gia aggiornato.' \
            'No file changed: you were already up to date.'
        return
    fi

    printf "\n  %s+ %d%s  %s- %d%s  %s~ %d%s\n" \
        "$C_PIU" "$aggiunti" "$C_FINE" \
        "$C_MENO" "$rimossi" "$C_FINE" \
        "$C_MOD" "$modificati" "$C_FINE"
}

# --- scaricamento -----------------------------------------------------------

passo "$(msg 'Scarico la nuova versione' 'Downloading the new version')"

TEMPORANEA="$(mktemp -d)"
trap 'rm -rf "$TEMPORANEA"' EXIT

if [ "$VERSIONE" = "ultima" ]; then
    # Si risolve il tag vero invece di usare /releases/latest/download/, che
    # GitHub serve da una cache: subito dopo una pubblicazione quell'indirizzo
    # restituisce ancora il pacchetto precedente, e l'aggiornamento riesce
    # installando in silenzio la versione di prima.
    # La risposta si mette in una variabile invece di darla in pasto a una
    # pipe: `grep -m1` chiude la pipe appena trova la riga, curl non riesce piu
    # a scrivere ed esce con 23 «failure writing output». Con `pipefail`
    # l'aggiornamento si fermava li, con un messaggio che fa pensare al disco
    # pieno.
    RISPOSTA="$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest")"
    TAG="$(printf '%s' "$RISPOSTA" | grep -m1 '"tag_name"' | cut -d'"' -f4)"
    [ -n "$TAG" ] ||
        errore "$(msg 'Non riesco a sapere qual e l ultima versione.'                        'Cannot determine the latest version.')"
    URL="https://github.com/${REPO}/releases/download/${TAG}/${APP}.tar.gz"
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
    # --itemize-changes elenca cosa cambia davvero, riga per riga. Senza, un
    # aggiornamento riuscito e uno che non ha toccato niente sono
    # indistinguibili, ed e proprio la domanda che ci si fa dopo averlo lanciato.
    CAMBIAMENTI="$(mktemp)"
    # Bytecode e metadati del pacchetto restano fuori: Python li rigenera da
    # solo, e senza escluderli venivano cancellati e ricreati a ogni
    # aggiornamento — il resoconto delle modifiche annegava in decine di righe
    # che non dicevano niente.
    # `--checksum` confronta il contenuto invece di data e dimensione: il
    # pacchetto viene ricompilato a ogni rilascio, quindi le date sono sempre
    # nuove e senza questo *ogni* file risulterebbe modificato — un resoconto
    # che segnala tutto non segnala niente. Costa una lettura dell'albero, che
    # e di pochi megabyte.
    rsync -a --delete --itemize-changes --checksum \
        --exclude '.env' \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '*.egg-info' \
        "$TEMPORANEA/nuova/" "$RADICE/" >"$CAMBIAMENTI"

    passo "$(msg 'File cambiati' 'Changed files')"
    mostra_cambiamenti "$CAMBIAMENTI"
    rm -f "$CAMBIAMENTI"

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

if [ "$ANF_API_IN_DOCKER" = 1 ]; then
    passo "$(msg 'anf-api gira in Docker' 'anf-api runs in Docker')"
    msg 'Il codice sorgente e stato aggiornato, ma il container usa ancora' \
        'The source code has been updated, but the container still runs'
    msg "l'immagine costruita dalla versione precedente. Ricostruiscilo:" \
        'the image built from the previous version. Rebuild it:'
    printf '\n  cd %s/deploy/docker && docker compose build --pull && docker compose up -d\n\n' "$RADICE"
fi

passo "$(msg 'Aggiornamento completato.' 'Update complete.')"
