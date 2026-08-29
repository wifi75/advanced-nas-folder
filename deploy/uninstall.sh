#!/usr/bin/env bash
#
# Disinstallazione di Advanced NAS Folder.
#
# Per impostazione predefinita **i dati restano**: database, configurazione e
# cartelle montate. Toglierli e' un'altra decisione, e va chiesta a parte con
# --tutto: chi disinstalla un pannello quasi mai vuole perdere anche i permessi
# che ci ha configurato dentro.
#
#   sudo ./uninstall.sh
#   sudo ./uninstall.sh --tutto
#   sudo ./uninstall.sh --dry-run
#
set -Eeuo pipefail

APP="advanced-nas-folder"
RADICE="/var/www/${APP}"
DATI="/var/lib/anf"
SERVIZI=(anf-api anf-agent)

TUTTO=0
DRY_RUN=0
CONFERMATO=0
LINGUA="${ANF_LANG:-it}"

msg() {
    local it="$1" en="$2"
    if [ "$LINGUA" = "en" ]; then printf '%s\n' "$en"; else printf '%s\n' "$it"; fi
}

passo() { printf '\n\033[1;36m==>\033[0m %s\n' "$1"; }
errore() { printf '\033[1;31mErrore:\033[0m %s\n' "$1" >&2; exit 1; }

uso() {
    cat <<'FINE'
Uso: uninstall.sh [opzioni]

  --tutto          Rimuove anche database, configurazione e unit dei mount
  --si             Non chiede conferma (per script non interattivi)
  --dry-run        Mostra cosa farebbe, senza toccare nulla
  --lang it|en     Lingua dei messaggi
  -h, --help       Questo testo

Senza --tutto restano: il database in /var/lib/anf, il file .env e le unit
systemd delle condivisioni NFS, che continuano a montare come prima.
FINE
}

while [ $# -gt 0 ]; do
    case "$1" in
        --tutto) TUTTO=1; shift ;;
        --si|--yes) CONFERMATO=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        --lang) LINGUA="${2:?}"; shift 2 ;;
        -h|--help) uso; exit 0 ;;
        *) errore "Opzione sconosciuta: $1" ;;
    esac
done

esegui() {
    if [ "$DRY_RUN" = 1 ]; then printf '    [prova] %s\n' "$*"; else "$@"; fi
}

[ "$(id -u)" = 0 ] || errore "$(msg 'Serve root: usa sudo.' 'Root required: use sudo.')"

# --- conferma ---------------------------------------------------------------

if [ "$TUTTO" = 1 ] && [ "$CONFERMATO" = 0 ] && [ "$DRY_RUN" = 0 ]; then
    msg "Verranno eliminati anche il database ($DATI), la configurazione e le unit dei mount." \
        "This will also delete the database ($DATI), the configuration and the mount units."
    msg "Le cartelle del NAS non vengono toccate: i file restano sul NAS." \
        "The NAS folders are untouched: the files stay on the NAS."
    printf '%s ' "$(msg 'Scrivi ELIMINA per confermare:' 'Type ELIMINA to confirm:')"
    read -r risposta
    [ "$risposta" = "ELIMINA" ] || errore "$(msg 'Annullato.' 'Cancelled.')"
fi

# --- servizi ----------------------------------------------------------------

passo "$(msg 'Fermo e disabilito i servizi' 'Stopping and disabling services')"
for s in "${SERVIZI[@]}"; do
    esegui systemctl disable --now "$s" 2>/dev/null || true
    esegui rm -f "/etc/systemd/system/${s}.service"
done
esegui systemctl daemon-reload

# --- web server -------------------------------------------------------------

passo "$(msg 'Tolgo la configurazione del web server' 'Removing web server configuration')"
esegui rm -f /etc/apache2/sites-enabled/anf.conf /etc/apache2/sites-available/anf.conf
esegui rm -f /etc/nginx/sites-enabled/anf.conf /etc/nginx/sites-available/anf.conf
# Anche i vhost aggiunti dal pannello, riconoscibili dal prefisso.
esegui rm -f /etc/apache2/sites-enabled/anf-*.conf /etc/apache2/sites-available/anf-*.conf
esegui rm -f /etc/nginx/sites-enabled/anf-* /etc/nginx/sites-available/anf-*

if command -v apache2ctl >/dev/null && apache2ctl configtest >/dev/null 2>&1; then
    esegui systemctl reload apache2 || true
fi
if command -v nginx >/dev/null && nginx -t >/dev/null 2>&1; then
    esegui systemctl reload nginx || true
fi

# --- programma --------------------------------------------------------------

passo "$(msg 'Rimuovo il programma' 'Removing the program')"
esegui rm -rf "$RADICE"

# --- dati -------------------------------------------------------------------

if [ "$TUTTO" = 1 ]; then
    passo "$(msg 'Rimuovo dati e mount gestiti' 'Removing data and managed mounts')"

    # Le unit dei mount portano il marcatore del pannello: si tolgono solo
    # quelle, mai una unit scritta da qualcun altro.
    for unit in /etc/systemd/system/*.mount /etc/systemd/system/*.automount; do
        [ -e "$unit" ] || continue
        if grep -q "Generato da Advanced NAS Folder" "$unit" 2>/dev/null; then
            nome="$(basename "$unit")"
            esegui systemctl disable --now "$nome" 2>/dev/null || true
            esegui rm -f "$unit"
        fi
    done
    esegui systemctl daemon-reload
    esegui rm -rf "$DATI"
    esegui rm -f /run/anf/agent.sock
    esegui userdel anf 2>/dev/null || true
else
    passo "$(msg 'Dati conservati' 'Data kept')"
    msg "Il database resta in $DATI e le condivisioni continuano a montare." \
        "The database stays in $DATI and the shares keep mounting."
    msg "Per togliere anche quelli: sudo ./uninstall.sh --tutto" \
        "To remove those too: sudo ./uninstall.sh --tutto"
fi

passo "$(msg 'Disinstallazione completata.' 'Uninstall complete.')"
