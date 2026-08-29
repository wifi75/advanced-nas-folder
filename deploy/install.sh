#!/usr/bin/env bash
#
# Advanced NAS Folder — installazione su server Linux
# Advanced NAS Folder — installation on a Linux server
#
# https://github.com/wifi75/advanced-nas-folder
#
# Idempotente: rieseguirlo su un'installazione esistente la aggiorna senza
# perdere configurazione e database.
#
# Idempotent: running it again on an existing installation upgrades it without
# losing configuration or database.

set -euo pipefail

# ---------------------------------------------------------------------------
# Impostazioni / Settings
# ---------------------------------------------------------------------------

APP="advanced-nas-folder"
UTENTE="anf"
GRUPPO="anf"
RADICE="/var/www/${APP}"
DATI="/var/lib/anf"
MOUNT_ROOT="/srv/nas"
SOCKET_DIR="/run/anf"
PORTA_API="8100"
PYTHON_MIN="3.14"
REPO="wifi75/advanced-nas-folder"

LINGUA="${ANF_LINGUA:-}"
SORGENTE=""
WEB="auto"
DRY_RUN=0
DISINSTALLA=0

# ---------------------------------------------------------------------------
# Messaggi bilingui / Bilingual messages
# ---------------------------------------------------------------------------

rileva_lingua() {
    [ -n "$LINGUA" ] && return
    case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in
        it* | IT*) LINGUA="it" ;;
        *) LINGUA="en" ;;
    esac
}

# shellcheck disable=SC2154
m() {
    local chiave="$1"
    shift
    local testo
    if [ "$LINGUA" = "it" ]; then
        case "$chiave" in
        serve_root) testo="Questo script va eseguito come root: usa sudo." ;;
        serve_systemd) testo="Serve un sistema con systemd. Non è stato trovato systemctl." ;;
        serve_linux) testo="Questo script funziona solo su Linux." ;;
        controlli) testo="Controllo dei prerequisiti" ;;
        installo_pacchetti) testo="Installo i pacchetti di sistema mancanti" ;;
        python_assente) testo="Python %s non trovato: lo installo dal repository deadsnakes, ACCANTO all'interprete di sistema, che non viene toccato." ;;
        python_ok) testo="Python %s presente" ;;
        web_rilevato) testo="Web server rilevato: %s" ;;
        web_assente) testo="Nessun web server trovato. Installa Apache o Nginx, oppure indica quale usare con --web." ;;
        xsendfile) testo="Installo mod_xsendfile, necessario per la consegna dei download" ;;
        utente_creo) testo="Creo l'utente di sistema %s" ;;
        utente_esiste) testo="Utente %s già presente" ;;
        cartelle) testo="Preparo le cartelle" ;;
        scarico) testo="Scarico la versione più recente da GitHub" ;;
        copio_locale) testo="Copio i file da %s" ;;
        niente_dist) testo="Il pacchetto non contiene frontend/dist: il frontend va compilato dalla CI. Vedi docs/INSTALL.md." ;;
        venv) testo="Preparo l'ambiente Python e installo le dipendenze" ;;
        env_creo) testo="Genero .env con segreti casuali" ;;
        env_esiste) testo="File .env già presente: lo lascio com'è" ;;
        migrazioni) testo="Applico le migrazioni del database" ;;
        unit) testo="Installo i servizi systemd" ;;
        vhost) testo="Configuro %s" ;;
        configtest_fallito) testo="La configurazione di %s non è valida: annullo la modifica e lascio il server come prima." ;;
        avvio) testo="Avvio i servizi" ;;
        verifica) testo="Verifico che l'API risponda" ;;
        verifica_ok) testo="L'API risponde correttamente" ;;
        verifica_ko) testo="L'API non risponde. Controlla i log con: journalctl -u anf-api -n 50" ;;
        fatto) testo="Installazione completata" ;;
        credenziali) testo="Al primo accesso: utente admin, password admin. CAMBIALA subito." ;;
        raggiungibile) testo="Il pannello risponde su http://localhost:%s dietro il web server." ;;
        disinstallo) testo="Rimuovo Advanced NAS Folder" ;;
        disinstalla_dati) testo="I dati in %s e i mount in %s NON vengono toccati." ;;
        prova) testo="PROVA: nessuna modifica verrà applicata" ;;
        esiste_aggiorno) testo="Installazione esistente trovata: aggiorno" ;;
        *) testo="$chiave" ;;
        esac
    else
        case "$chiave" in
        serve_root) testo="This script must run as root: use sudo." ;;
        serve_systemd) testo="A systemd-based system is required. systemctl was not found." ;;
        serve_linux) testo="This script only runs on Linux." ;;
        controlli) testo="Checking prerequisites" ;;
        installo_pacchetti) testo="Installing missing system packages" ;;
        python_assente) testo="Python %s not found: installing it from the deadsnakes repository, ALONGSIDE the system interpreter, which is left untouched." ;;
        python_ok) testo="Python %s found" ;;
        web_rilevato) testo="Web server detected: %s" ;;
        web_assente) testo="No web server found. Install Apache or Nginx, or pick one with --web." ;;
        xsendfile) testo="Installing mod_xsendfile, required to deliver downloads" ;;
        utente_creo) testo="Creating system user %s" ;;
        utente_esiste) testo="User %s already exists" ;;
        cartelle) testo="Preparing directories" ;;
        scarico) testo="Downloading the latest release from GitHub" ;;
        copio_locale) testo="Copying files from %s" ;;
        niente_dist) testo="The package has no frontend/dist: the frontend is built by CI. See docs/INSTALL.md." ;;
        venv) testo="Preparing the Python environment and installing dependencies" ;;
        env_creo) testo="Generating .env with random secrets" ;;
        env_esiste) testo=".env already present: leaving it untouched" ;;
        migrazioni) testo="Applying database migrations" ;;
        unit) testo="Installing systemd services" ;;
        vhost) testo="Configuring %s" ;;
        configtest_fallito) testo="The %s configuration is invalid: rolling back and leaving the server as it was." ;;
        avvio) testo="Starting services" ;;
        verifica) testo="Checking that the API answers" ;;
        verifica_ok) testo="The API answers correctly" ;;
        verifica_ko) testo="The API does not answer. Check the logs with: journalctl -u anf-api -n 50" ;;
        fatto) testo="Installation complete" ;;
        credenziali) testo="First sign-in: user admin, password admin. CHANGE IT right away." ;;
        raggiungibile) testo="The panel answers on http://localhost:%s behind the web server." ;;
        disinstallo) testo="Removing Advanced NAS Folder" ;;
        disinstalla_dati) testo="Data in %s and mounts in %s are NOT touched." ;;
        prova) testo="DRY RUN: no change will be applied" ;;
        esiste_aggiorno) testo="Existing installation found: upgrading" ;;
        *) testo="$chiave" ;;
        esac
    fi
    # shellcheck disable=SC2059
    printf "$testo" "$@"
}

# ---------------------------------------------------------------------------
# Uscita a schermo / Output
# ---------------------------------------------------------------------------

if [ -t 1 ]; then
    C_OK=$'\033[32m'; C_INFO=$'\033[36m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_FINE=$'\033[0m'
else
    C_OK=""; C_INFO=""; C_WARN=""; C_ERR=""; C_FINE=""
fi

passo() { printf '%s==>%s %s\n' "$C_INFO" "$C_FINE" "$(m "$@")"; }
ok()    { printf '%s  ok%s %s\n' "$C_OK" "$C_FINE" "$(m "$@")"; }
avviso(){ printf '%s  !%s  %s\n' "$C_WARN" "$C_FINE" "$(m "$@")"; }
errore(){ printf '%serrore:%s %s\n' "$C_ERR" "$C_FINE" "$(m "$@")" >&2; exit 1; }

esegui() {
    if [ "$DRY_RUN" = 1 ]; then
        printf '       %s\n' "$*"
    else
        "$@"
    fi
}

# ---------------------------------------------------------------------------
# Argomenti / Arguments
# ---------------------------------------------------------------------------

aiuto() {
    cat <<'FINE'
Advanced NAS Folder — installer

  --sorgente <percorso>   Installa da una cartella locale invece che dalla release
  --source <path>

  --web apache|nginx      Forza il web server invece di rilevarlo
  --porta <numero>        Porta interna dell'API (predefinita 8100)
  --port <number>

  --lingua it|en          Lingua dei messaggi (predefinita: dalla locale)
  --lang it|en

  --dry-run               Mostra cosa farebbe, senza applicare nulla
  --uninstall             Rimuove servizi e programma. Dati e mount restano.
  -h, --help              Questo messaggio
FINE
}

while [ $# -gt 0 ]; do
    case "$1" in
        --sorgente | --source) SORGENTE="$2"; shift 2 ;;
        --web) WEB="$2"; shift 2 ;;
        --porta | --port) PORTA_API="$2"; shift 2 ;;
        --lingua | --lang) LINGUA="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --uninstall) DISINSTALLA=1; shift ;;
        -h | --help) aiuto; exit 0 ;;
        *) printf 'Argomento non riconosciuto / unknown argument: %s\n' "$1" >&2; aiuto; exit 2 ;;
    esac
done

rileva_lingua

# ---------------------------------------------------------------------------
# Disinstallazione / Uninstall
# ---------------------------------------------------------------------------

if [ "$DISINSTALLA" = 1 ]; then
    [ "$(id -u)" -eq 0 ] || errore serve_root
    passo disinstallo
    for s in anf-api anf-agent; do
        esegui systemctl disable --now "$s" 2>/dev/null || true
        esegui rm -f "/etc/systemd/system/${s}.service"
    done
    esegui systemctl daemon-reload
    esegui rm -f /etc/apache2/sites-enabled/anf.conf /etc/apache2/sites-available/anf.conf
    esegui rm -f /etc/nginx/sites-enabled/anf.conf /etc/nginx/sites-available/anf.conf
    esegui rm -rf "$RADICE"
    ok fatto
    printf '  %s\n' "$(m disinstalla_dati "$DATI" "$MOUNT_ROOT")"
    exit 0
fi

# ---------------------------------------------------------------------------
# Controlli / Checks
# ---------------------------------------------------------------------------

[ "$(uname -s)" = "Linux" ] || errore serve_linux
[ "$(id -u)" -eq 0 ] || errore serve_root
command -v systemctl >/dev/null 2>&1 || errore serve_systemd

[ "$DRY_RUN" = 1 ] && avviso prova
[ -d "$RADICE" ] && avviso esiste_aggiorno

passo controlli

export DEBIAN_FRONTEND=noninteractive

mancanti=()
for pacchetto in curl nfs-common openssl; do
    dpkg -s "$pacchetto" >/dev/null 2>&1 || mancanti+=("$pacchetto")
done
if [ ${#mancanti[@]} -gt 0 ]; then
    passo installo_pacchetti
    esegui apt-get update -qq
    esegui apt-get install -y -qq "${mancanti[@]}"
fi

# --- Python -----------------------------------------------------------------
# Va installato ACCANTO all'interprete di sistema: spostare python3 romperebbe
# il sistema operativo e le altre applicazioni presenti sulla macchina.

PYBIN="python${PYTHON_MIN}"
if command -v "$PYBIN" >/dev/null 2>&1; then
    ok python_ok "$PYTHON_MIN"
else
    avviso python_assente "$PYTHON_MIN"
    esegui apt-get install -y -qq software-properties-common
    esegui add-apt-repository -y ppa:deadsnakes/ppa
    esegui apt-get update -qq
    esegui apt-get install -y -qq "$PYBIN" "${PYBIN}-venv" "${PYBIN}-dev"
fi

# --- web server -------------------------------------------------------------

if [ "$WEB" = "auto" ]; then
    if command -v apache2ctl >/dev/null 2>&1 || command -v apachectl >/dev/null 2>&1; then
        WEB="apache"
    elif command -v nginx >/dev/null 2>&1; then
        WEB="nginx"
    else
        errore web_assente
    fi
fi
ok web_rilevato "$WEB"

if [ "$WEB" = "apache" ] && ! dpkg -s libapache2-mod-xsendfile >/dev/null 2>&1; then
    passo xsendfile
    esegui apt-get install -y -qq libapache2-mod-xsendfile
    esegui a2enmod xsendfile
    esegui a2enmod remoteip
    esegui a2enmod proxy proxy_http headers
fi

# ---------------------------------------------------------------------------
# Utente e cartelle / User and directories
# ---------------------------------------------------------------------------

if id "$UTENTE" >/dev/null 2>&1; then
    ok utente_esiste "$UTENTE"
else
    passo utente_creo "$UTENTE"
    esegui groupadd -f "$GRUPPO"
    esegui useradd --system --gid "$GRUPPO" --home-dir "$RADICE" \
        --shell /usr/sbin/nologin --comment "Advanced NAS Folder" "$UTENTE"
fi

passo cartelle
esegui install -d -m 0755 -o "$UTENTE" -g "$GRUPPO" "$RADICE"
esegui install -d -m 0750 -o "$UTENTE" -g "$GRUPPO" "$DATI"
esegui install -d -m 0755 "$MOUNT_ROOT"
esegui install -d -m 0750 -o root -g "$GRUPPO" "$SOCKET_DIR"

# ---------------------------------------------------------------------------
# Codice / Code
# ---------------------------------------------------------------------------

TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT

if [ -n "$SORGENTE" ]; then
    passo copio_locale "$SORGENTE"
    [ -d "$SORGENTE/backend" ] || errore "sorgente non valida / invalid source: $SORGENTE"
    esegui cp -a "$SORGENTE/." "$TEMP/"
else
    passo scarico
    URL="https://github.com/${REPO}/releases/latest/download/${APP}.tar.gz"
    esegui curl -fsSL "$URL" -o "$TEMP/pacchetto.tar.gz"
    esegui tar -xzf "$TEMP/pacchetto.tar.gz" -C "$TEMP"
    esegui rm -f "$TEMP/pacchetto.tar.gz"
fi

if [ "$DRY_RUN" = 0 ]; then
    [ -d "$TEMP/frontend/dist" ] || avviso niente_dist
    # Il database e la configurazione non stanno qui dentro, quindi
    # sovrascrivere il codice non tocca i dati.
    for cartella in backend agent frontend deploy docs; do
        [ -d "$TEMP/$cartella" ] || continue
        rm -rf "${RADICE:?}/$cartella"
        cp -a "$TEMP/$cartella" "$RADICE/"
    done
    for file in README.md CHANGELOG.md LICENSE .env.example; do
        [ -f "$TEMP/$file" ] && cp -a "$TEMP/$file" "$RADICE/"
    done
    chown -R "$UTENTE:$GRUPPO" "$RADICE"
fi

# ---------------------------------------------------------------------------
# Ambiente Python / Python environment
# ---------------------------------------------------------------------------

passo venv
esegui "$PYBIN" -m venv "$RADICE/venv"
esegui "$RADICE/venv/bin/pip" install -q --upgrade pip
esegui "$RADICE/venv/bin/pip" install -q "$RADICE/backend"
esegui chown -R "$UTENTE:$GRUPPO" "$RADICE/venv"

# ---------------------------------------------------------------------------
# Configurazione / Configuration
# ---------------------------------------------------------------------------

ENV_FILE="$RADICE/.env"
if [ -f "$ENV_FILE" ]; then
    ok env_esiste
else
    passo env_creo
    if [ "$DRY_RUN" = 0 ]; then
        cat >"$ENV_FILE" <<FINE
ANF_ENV=production
ANF_HOST=127.0.0.1
ANF_PORT=${PORTA_API}
ANF_LOG_LEVEL=INFO
ANF_SECRET_KEY=$(openssl rand -hex 32)
ANF_DB_PATH=${DATI}/anf.sqlite3
ANF_DB_WAL=true
ANF_AGENT_SOCKET=${SOCKET_DIR}/agent.sock
ANF_MOUNT_ROOT=${MOUNT_ROOT}
ANF_DOWNLOAD_BACKEND=$([ "$WEB" = "apache" ] && echo xsendfile || echo xaccel)
ANF_ACCESS_LOG=/var/log/${WEB}/anf_access.log
ANF_TRUSTED_PROXIES=127.0.0.1
FINE
        chown "$UTENTE:$GRUPPO" "$ENV_FILE"
        chmod 0600 "$ENV_FILE"
    fi
fi

passo migrazioni
esegui env -C "$RADICE/backend" "$RADICE/venv/bin/alembic" upgrade head

# ---------------------------------------------------------------------------
# Servizi / Services
# ---------------------------------------------------------------------------

passo unit
for s in anf-agent anf-api; do
    esegui install -m 0644 "$RADICE/deploy/systemd/${s}.service" "/etc/systemd/system/${s}.service"
done
esegui systemctl daemon-reload

# ---------------------------------------------------------------------------
# Web server
# ---------------------------------------------------------------------------

passo vhost "$WEB"

if [ "$DRY_RUN" = 0 ]; then
    if [ "$WEB" = "apache" ]; then
        DEST="/etc/apache2/sites-available/anf.conf"
        PRECEDENTE=""
        [ -f "$DEST" ] && PRECEDENTE="$(mktemp)" && cp "$DEST" "$PRECEDENTE"

        sed -e "s|@@RADICE@@|$RADICE|g" -e "s|@@PORTA@@|$PORTA_API|g" \
            -e "s|@@MOUNT_ROOT@@|$MOUNT_ROOT|g" \
            "$RADICE/deploy/webserver/apache.conf.tpl" >"$DEST"
        a2ensite anf >/dev/null

        # Il test PRIMA del reload: una configurazione non valida fermerebbe
        # tutti i siti ospitati sulla macchina, non solo questo.
        if ! apache2ctl configtest >/dev/null 2>&1; then
            if [ -n "$PRECEDENTE" ]; then cp "$PRECEDENTE" "$DEST"; else rm -f "$DEST"; a2dissite anf >/dev/null 2>&1 || true; fi
            errore configtest_fallito "Apache"
        fi
        systemctl reload apache2
    else
        DEST="/etc/nginx/sites-available/anf.conf"
        PRECEDENTE=""
        [ -f "$DEST" ] && PRECEDENTE="$(mktemp)" && cp "$DEST" "$PRECEDENTE"

        sed -e "s|@@RADICE@@|$RADICE|g" -e "s|@@PORTA@@|$PORTA_API|g" \
            -e "s|@@MOUNT_ROOT@@|$MOUNT_ROOT|g" \
            "$RADICE/deploy/webserver/nginx.conf.tpl" >"$DEST"
        ln -sf "$DEST" /etc/nginx/sites-enabled/anf.conf

        if ! nginx -t >/dev/null 2>&1; then
            if [ -n "$PRECEDENTE" ]; then cp "$PRECEDENTE" "$DEST"; else rm -f "$DEST" /etc/nginx/sites-enabled/anf.conf; fi
            errore configtest_fallito "Nginx"
        fi
        systemctl reload nginx
    fi
fi

# ---------------------------------------------------------------------------
# Avvio / Start
# ---------------------------------------------------------------------------

passo avvio
esegui systemctl enable --now anf-agent
esegui systemctl enable --now anf-api

if [ "$DRY_RUN" = 0 ]; then
    passo verifica
    risposta=""
    for _ in $(seq 1 20); do
        sleep 1
        risposta="$(curl -fsS "http://127.0.0.1:${PORTA_API}/api/v1/health" 2>/dev/null || true)"
        [ -n "$risposta" ] && break
    done
    if [ -n "$risposta" ]; then
        ok verifica_ok
    else
        avviso verifica_ko
    fi
fi

# ---------------------------------------------------------------------------
# Riepilogo / Summary
# ---------------------------------------------------------------------------

printf '\n%s%s%s\n\n' "$C_OK" "$(m fatto)" "$C_FINE"
printf '  %s\n' "$(m raggiungibile "$PORTA_API")"
printf '  %s%s%s\n\n' "$C_WARN" "$(m credenziali)" "$C_FINE"
