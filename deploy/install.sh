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
# Database e miniature delle immagini. Le miniature stanno qui e non nel
# mount: scriverle sul NAS sporcherebbe le cartelle condivise e richiederebbe
# un permesso di scrittura che di norma non c'e'.
DATI="/var/lib/anf"
MOUNT_ROOT="/srv/nas"
SOCKET_DIR="/run/anf"
PORTA_API="auto"
PORTA_PREDEFINITA="8100"
PORTA_SCELTA_A_MANO=0
# In prova a vuoto non si verifica nulla: si considera riuscita.
INSTALLAZIONE_OK=1
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
        web_installo) testo="Installo %s" ;;
        xsendfile) testo="Installo mod_xsendfile, necessario per la consegna dei download" ;;
        moduli) testo="Abilito i moduli di Apache che servono al pannello" ;;
        porta_cerco) testo="Cerco una porta libera per l'API" ;;
        porta_ok) testo="Porta %s libera" ;;
        porta_presa) testo="La porta %s è occupata" ;;
        porta_chi) testo="La porta %s è occupata da: %s" ;;
        porta_libere) testo="Fra le prime libere: %s" ;;
        porta_chiedo) testo="Che porta uso? Scrivine una, o Invio per la %s:" ;;
        porta_spostata) testo="La porta %s è già occupata: uso la %s" ;;
        porta_occupata) testo="La porta %s è già occupata da un altro servizio. Indicane un'altra con --porta, oppure libera quella." ;;
        porta_presa_ora) testo="La porta %s è occupata: scegline un'altra." ;;
        porta_niente) testo="Nessuna porta libera fra %s e %s. Indicane una con --porta." ;;
        porta_invalida) testo="Porta non valida: %s. Serve un numero fra 1024 e 65535." ;;
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
        fatto_a_meta) testo="Installazione incompleta: i servizi non rispondono" ;;
        v_indirizzo) testo="Indirizzo del pannello" ;;
        v_porta_api) testo="Porta dell'API" ;;
        v_solo_locale) testo="(solo in locale, dietro il web server)" ;;
        v_utente) testo="Utente" ;;
        v_password) testo="Password" ;;
        come_indagare) testo="Per capire cosa non va: journalctl -u anf-agent -n 50 e journalctl -u anf-api -n 50" ;;
        credenziali) testo="Cambia la password al primo accesso: il pannello te lo ricorda finché non lo fai." ;;
        raggiungibile) testo="Il pannello risponde su http://localhost:%s dietro il web server." ;;
        disinstallo) testo="Rimuovo Advanced NAS Folder" ;;
        disinstalla_dati) testo="I dati in %s e i mount in %s NON vengono toccati." ;;
        prova) testo="PROVA: nessuna modifica verrà applicata" ;;
        sottotitolo) testo="Monta condivisioni NFS, pubblica cartelle, gestisce i file." ;;
        sistema) testo="Il sistema" ;;
        configurazione) testo="Configurazione" ;;
        d_web) testo="Quale web server uso?" ;;
        d_web_no) testo="Non riconosciuto: %s. Scrivi apache oppure nginx." ;;
        d_mount) testo="Dove monto le condivisioni del NAS?" ;;
        d_radice) testo="Dove installo il programma?" ;;
        d_dati) testo="Dove tengo database e dati?" ;;
        percorso_relativo) testo="Serve un percorso assoluto, che inizi con /: %s" ;;
        scelte) testo="Cosa verrà installato" ;;
        conferma) testo="Procedo? [S/n]" ;;
        annullato) testo="Annullato. Non è stato modificato nulla." ;;
        v_sistema) testo="Sistema" ;;
        v_python) testo="Python" ;;
        v_web) testo="Web server" ;;
        v_memoria) testo="Memoria libera" ;;
        v_disco) testo="Spazio libero" ;;
        v_porte) testo="Porte occupate" ;;
        v_porta) testo="Porta dell'API" ;;
        v_cartella) testo="Programma" ;;
        v_dati) testo="Dati" ;;
        v_mount) testo="Radice dei mount" ;;
        v_consegna) testo="Consegna dei file" ;;
        v_assente) testo="assente" ;;
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
        web_installo) testo="Installing %s" ;;
        xsendfile) testo="Installing mod_xsendfile, required to deliver downloads" ;;
        moduli) testo="Enabling the Apache modules the panel needs" ;;
        porta_cerco) testo="Looking for a free port for the API" ;;
        porta_ok) testo="Port %s is free" ;;
        porta_presa) testo="Port %s is taken" ;;
        porta_chi) testo="Port %s is taken by: %s" ;;
        porta_libere) testo="Among the first free ones: %s" ;;
        porta_chiedo) testo="Which port? Type one, or Enter for %s:" ;;
        porta_spostata) testo="Port %s is already taken: using %s instead" ;;
        porta_occupata) testo="Port %s is already taken by another service. Pick another one with --port, or free it." ;;
        porta_presa_ora) testo="Port %s is taken: pick another one." ;;
        porta_niente) testo="No free port between %s and %s. Pick one with --port." ;;
        porta_invalida) testo="Invalid port: %s. A number between 1024 and 65535 is required." ;;
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
        fatto_a_meta) testo="Installation incomplete: the services are not answering" ;;
        v_indirizzo) testo="Panel address" ;;
        v_porta_api) testo="API port" ;;
        v_solo_locale) testo="(local only, behind the web server)" ;;
        v_utente) testo="User" ;;
        v_password) testo="Password" ;;
        come_indagare) testo="To find out what is wrong: journalctl -u anf-agent -n 50 and journalctl -u anf-api -n 50" ;;
        credenziali) testo="Change the password on first sign-in: the panel keeps reminding you until you do." ;;
        raggiungibile) testo="The panel answers on http://localhost:%s behind the web server." ;;
        disinstallo) testo="Removing Advanced NAS Folder" ;;
        disinstalla_dati) testo="Data in %s and mounts in %s are NOT touched." ;;
        prova) testo="DRY RUN: no change will be applied" ;;
        sottotitolo) testo="Mounts NFS shares, publishes folders, manages files." ;;
        sistema) testo="The system" ;;
        configurazione) testo="Configuration" ;;
        d_web) testo="Which web server should I use?" ;;
        d_web_no) testo="Not recognised: %s. Type apache or nginx." ;;
        d_mount) testo="Where should I mount the NAS shares?" ;;
        d_radice) testo="Where should I install the program?" ;;
        d_dati) testo="Where should I keep the database and data?" ;;
        percorso_relativo) testo="An absolute path is required, starting with /: %s" ;;
        scelte) testo="What will be installed" ;;
        conferma) testo="Proceed? [Y/n]" ;;
        annullato) testo="Cancelled. Nothing was changed." ;;
        v_sistema) testo="System" ;;
        v_python) testo="Python" ;;
        v_web) testo="Web server" ;;
        v_memoria) testo="Free memory" ;;
        v_disco) testo="Free space" ;;
        v_porte) testo="Ports in use" ;;
        v_porta) testo="API port" ;;
        v_cartella) testo="Program" ;;
        v_dati) testo="Data" ;;
        v_mount) testo="Mount root" ;;
        v_consegna) testo="File delivery" ;;
        v_assente) testo="missing" ;;
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

# Colori e simboli solo se c'e' un terminale davanti: reindirizzando su file le
# sequenze di controllo sarebbero rumore illeggibile.
if [ -t 1 ]; then
    C_OK=$'\033[32m'; C_INFO=$'\033[36m'; C_WARN=$'\033[33m'; C_ERR=$'\033[31m'
    C_TIT=$'\033[1;36m'; C_DIM=$'\033[2m'; C_GRA=$'\033[1m'; C_FINE=$'\033[0m'
else
    C_OK=""; C_INFO=""; C_WARN=""; C_ERR=""; C_TIT=""; C_DIM=""; C_GRA=""; C_FINE=""
fi

# I simboli Unicode si usano solo se il terminale dichiara UTF-8: altrove
# comparirebbero come caratteri illeggibili, che e' peggio di un trattino.
case "${LC_ALL:-${LC_CTYPE:-${LANG:-C}}}" in
*[Uu][Tt][Ff]*8*) S_PASSO="▸"; S_OK="✓"; S_WARN="!"; S_ERR="✗"; S_RIGA="─"; S_PUNTO="·" ;;
*)                S_PASSO=">"; S_OK="+"; S_WARN="!"; S_ERR="x"; S_RIGA="-"; S_PUNTO="-" ;;
esac

riga() {
    local out=""
    while [ "${#out}" -lt 66 ]; do out="${out}${S_RIGA}"; done
    printf '%s%s%s
' "$C_DIM" "$out" "$C_FINE"
}

passo()  { printf '
%s%s%s %s%s%s
' "$C_INFO" "$S_PASSO" "$C_FINE" "$C_GRA" "$(m "$@")" "$C_FINE"; }
ok()     { printf '  %s%s%s %s
' "$C_OK" "$S_OK" "$C_FINE" "$(m "$@")"; }
avviso() { printf '  %s%s%s %s
' "$C_WARN" "$S_WARN" "$C_FINE" "$(m "$@")"; }
errore() { printf '
  %s%s %s%s

' "$C_ERR" "$S_ERR" "$(m "$@")" "$C_FINE" >&2; exit 1; }

# Riga di una scheda riassuntiva: etichetta a sinistra, valore a destra.
voce() { printf '  %s%-22s%s %s
' "$C_DIM" "$1" "$C_FINE" "$2"; }

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
  --porta <numero>        Porta interna dell'API. Senza questa opzione viene
  --port <number>         scelta la prima libera a partire dalla 8100.

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
        --porta | --port) PORTA_API="$2"; PORTA_SCELTA_A_MANO=1; shift 2 ;;
        --lingua | --lang) LINGUA="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --uninstall) DISINSTALLA=1; shift ;;
        -h | --help) aiuto; exit 0 ;;
        *) printf 'Argomento non riconosciuto / unknown argument: %s\n' "$1" >&2; aiuto; exit 2 ;;
    esac
done

rileva_lingua

# ---------------------------------------------------------------------------
# Domande / Questions
# ---------------------------------------------------------------------------

# Chiede una cosa mostrando il valore predefinito, e restituisce la risposta.
# Invio a vuoto tiene il predefinito: e' il caso piu' frequente, e deve essere
# il piu' rapido.
#
# Senza terminale non chiede e tiene il predefinito: con `curl | bash` non c'e'
# nessuno a rispondere, e restare fermi ad aspettare sarebbe peggio.
chiedi() {
    local domanda="$1" predefinito="$2" risposta=""
    if [ ! -t 0 ]; then
        printf '%s' "$predefinito"
        return
    fi
    printf '  %s%s%s %s[%s]%s ' "$C_GRA" "$domanda" "$C_FINE" "$C_DIM" "$predefinito" "$C_FINE" >&2
    read -r risposta || risposta=""
    risposta="${risposta#"${risposta%%[![:space:]]*}"}"
    risposta="${risposta%"${risposta##*[![:space:]]}"}"
    printf '%s' "${risposta:-$predefinito}"
}

# Come sopra, ma per un percorso assoluto: una risposta relativa qui
# produrrebbe cartelle create dove capita, a seconda di dove si e' lanciato lo
# script.
chiedi_percorso() {
    local domanda="$1" predefinito="$2" risposta=""
    while :; do
        risposta="$(chiedi "$domanda" "$predefinito")"
        case "$risposta" in
        /*) printf '%s' "$risposta"; return ;;
        esac
        [ -t 0 ] || { printf '%s' "$predefinito"; return; }
        avviso percorso_relativo "$risposta"
    done
}

# Le scelte che cambiano davvero l'installazione. Poche e con un predefinito
# sensato: una domanda a cui si risponde sempre Invio e' una domanda che non
# andava fatta.
configura() {
    [ -t 0 ] || return 0

    passo configurazione

    # Il web server si chiede solo se ce ne sono due: con uno solo non c'e'
    # scelta, e chiederlo sarebbe finto.
    if [ "$WEB_AMBIGUO" = 1 ]; then
        local scelto
        while :; do
            scelto="$(chiedi "$(m d_web)" "$WEB")"
            case "$scelto" in
            apache | nginx) WEB="$scelto"; break ;;
            *) avviso d_web_no "$scelto" ;;
            esac
        done
    fi

    MOUNT_ROOT="$(chiedi_percorso "$(m d_mount)" "$MOUNT_ROOT")"
    RADICE="$(chiedi_percorso "$(m d_radice)" "$RADICE")"
    DATI="$(chiedi_percorso "$(m d_dati)" "$DATI")"
}

# ---------------------------------------------------------------------------
# Intestazione e riepilogo / Banner and summary
# ---------------------------------------------------------------------------

intestazione() {
    printf '\n'
    riga
    printf '  %sAdvanced NAS Folder%s\n' "$C_TIT" "$C_FINE"
    printf '  %s%s%s\n' "$C_DIM" "$(m sottotitolo)" "$C_FINE"
    riga
}

# Cosa e' stato trovato sulla macchina, prima di toccarla. Serve a decidere con
# cognizione invece di scoprire i conflitti a meta' installazione.
sistema() {
    passo sistema
    voce "$(m v_sistema)"  "$(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME" || uname -s)"
    voce "$(m v_python)"   "$(command -v "$PYBIN" >/dev/null 2>&1 && "$PYBIN" -V 2>&1 || m v_assente)"
    voce "$(m v_web)"      "$WEB"
    voce "$(m v_memoria)"  "$(free -h 2>/dev/null | awk '/^Mem/{print $7" / "$2}' || echo '?')"
    voce "$(m v_disco)"    "$(df -h "$(dirname "$RADICE")" 2>/dev/null | awk 'NR==2{print $4" / "$2}')"

    # Le porte gia' in ascolto: e' l'informazione che evita il conflitto piu'
    # comune, e non si trova da nessun'altra parte se non guardandola.
    local occupate
    occupate="$(ss -tln 2>/dev/null | awk 'NR>1{print $4}' | grep -oE '[0-9]+$' |
        sort -un | awk '$1>=8000 && $1<=9000' | tr '\n' ' ')"
    [ -n "$occupate" ] && voce "$(m v_porte)" "$occupate"
}

# Riepilogo di cosa verra' fatto, prima di farlo.
riepilogo_scelte() {
    passo scelte
    voce "$(m v_porta)"       "$PORTA_API"
    voce "$(m v_web)"         "$WEB"
    voce "$(m v_cartella)"    "$RADICE"
    voce "$(m v_dati)"        "$DATI"
    voce "$(m v_mount)"       "$MOUNT_ROOT"
    voce "$(m v_consegna)"    "$([ "$WEB" = apache ] && echo 'X-Sendfile' || echo 'X-Accel-Redirect')"

    # Con un terminale davanti si chiede conferma: e' l'ultimo momento utile
    # per fermarsi prima che qualcosa venga scritto sul sistema.
    if [ -t 0 ] && [ "$DRY_RUN" = 0 ]; then
        printf '\n  %s ' "$(m conferma)"
        local r=""; read -r r || r=""
        case "${r,,}" in
        n | no) errore annullato ;;
        esac
    fi
}

# ---------------------------------------------------------------------------
# Scelta della porta / Port selection
# ---------------------------------------------------------------------------

# Vero se qualcosa sta già ascoltando su quella porta.
#
# Si guarda l'ascolto reale con `ss`, non un file di configurazione: la porta
# può essere occupata da un servizio che il pannello non conosce, ed è
# esattamente il caso che rompe l'installazione.
porta_occupata() {
    local porta="$1"
    if command -v ss >/dev/null 2>&1; then
        ss -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${porta}$"
    elif command -v netstat >/dev/null 2>&1; then
        netstat -tln 2>/dev/null | awk '{print $4}' | grep -qE "[:.]${porta}$"
    else
        # Senza strumenti per guardare, si prova ad aprirla: se la connessione
        # riesce, qualcuno risponde.
        (exec 3<>"/dev/tcp/127.0.0.1/${porta}") 2>/dev/null && { exec 3<&-; return 0; }
        return 1
    fi
}

# Nome dell'unit systemd che ascolta su quella porta, se lo si riesce a
# risalire dal cgroup del processo. Vuoto se non si sa.
unita_in_ascolto() {
    local porta="$1" pid
    pid="$(ss -tlnp 2>/dev/null | grep -E "[:.]${porta}[[:space:]]" |
        grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)"
    [ -n "$pid" ] && [ -r "/proc/$pid/cgroup" ] || return 0
    grep -oE '[a-zA-Z0-9@._-]+\.service' "/proc/$pid/cgroup" 2>/dev/null | head -1
}

# Vero se la porta e' presa da qualcosa che non sia anf-api.service. In un
# aggiornamento e' gia' lui a occuparla, in attesa del riavvio che questo
# stesso script fara' fra poco: non e' un conflitto da segnalare o da cui
# scappare su un'altra porta, che lascerebbe nginx (rigenerato) disallineato
# da .env (che l'installer lascia intatto negli aggiornamenti) — trovato
# aggiornando un'installazione gia' attiva.
porta_occupata_da_altri() {
    local porta="$1"
    porta_occupata "$porta" || return 1
    [ "$(unita_in_ascolto "$porta")" = "anf-api.service" ] && return 1
    return 0
}

scegli_porta() {
    # Porta chiesta esplicitamente: se e occupata ci si ferma, non si cambia
    # di nascosto. Chi ha scritto --porta 8110 ha un motivo, e trovarsi il
    # pannello su un'altra porta sarebbe peggio di un errore.
    if [ "$PORTA_SCELTA_A_MANO" = 1 ]; then
        case "$PORTA_API" in
        '' | *[!0-9]*) errore porta_invalida "$PORTA_API" ;;
        esac
        [ "$PORTA_API" -ge 1024 ] && [ "$PORTA_API" -le 65535 ] ||
            errore porta_invalida "$PORTA_API"
        if porta_occupata_da_altri "$PORTA_API"; then
            errore porta_occupata "$PORTA_API"
        fi
        ok porta_ok "$PORTA_API"
        return
    fi

    # Nessuna indicazione: si raccolgono le prime porte libere e, se c'è
    # qualcuno davanti al terminale, gliele si propone. Con `curl | bash` non
    # c'è nessuno a rispondere, quindi si sceglie da soli invece di restare
    # fermi ad aspettare un tasto che non arriverà mai.
    passo porta_cerco

    local candidata="$PORTA_PREDEFINITA"
    local ultima=$((PORTA_PREDEFINITA + 50))
    local libere=""
    local quante=0

    while [ "$candidata" -le "$ultima" ] && [ "$quante" -lt 5 ]; do
        if porta_occupata_da_altri "$candidata"; then
            # Dire *chi* la occupa evita di dover andare a cercarlo a mano.
            # Il nome del servizio systemd e' piu' utile del nome del
            # programma: "ilmioricettario.service" dice cosa fermare,
            # "python" no.
            local chi
            chi="$(ss -tlnp 2>/dev/null | grep -E "[:.]${candidata}[[:space:]]" |
                grep -oE 'users:\(\("[^"]+' | head -1 | sed 's/.*"//')"
            local unit; unit="$(unita_in_ascolto "$candidata")"
            [ -n "$unit" ] && chi="$unit"
            if [ -n "$chi" ]; then
                avviso porta_chi "$candidata" "$chi"
            else
                avviso porta_presa "$candidata"
            fi
        else
            libere="$libere $candidata"
            quante=$((quante + 1))
        fi
        candidata=$((candidata + 1))
    done

    [ "$quante" -gt 0 ] || errore porta_niente "$PORTA_PREDEFINITA" "$ultima"

    # shellcheck disable=SC2086
    set -- $libere
    local prima="$1"

    # Interattivo se c'è un terminale da cui leggere. Vale anche in prova a
    # vuoto: quella prova serve a mostrare cosa succederebbe, e saltare le
    # domande la renderebbe diversa dall'installazione vera.
    if [ -t 0 ]; then
        printf '  %s
' "$(m porta_libere "$(echo $libere | sed 's/ /, /g')")"

        # Si richiede finché la risposta non va bene, invece di interrompere:
        # a una domanda si risponde male per distrazione, e far ricominciare
        # tutta l'installazione per un numero sbagliato sarebbe punitivo.
        local risposta="" tentativi=0
        while [ "$tentativi" -lt 5 ]; do
            tentativi=$((tentativi + 1))
            printf '  %s ' "$(m porta_chiedo "$prima")"
            read -r risposta || risposta=""
            risposta="${risposta//[[:space:]]/}"

            # Invio a vuoto: va bene la proposta.
            [ -z "$risposta" ] && break

            case "$risposta" in
            *[!0-9]*)
                avviso porta_invalida "$risposta"
                continue
                ;;
            esac
            if [ "$risposta" -lt 1024 ] || [ "$risposta" -gt 65535 ]; then
                avviso porta_invalida "$risposta"
                continue
            fi
            if porta_occupata_da_altri "$risposta"; then
                avviso porta_presa_ora "$risposta"
                continue
            fi

            PORTA_API="$risposta"
            ok porta_ok "$PORTA_API"
            return
        done
    fi

    PORTA_API="$prima"
    if [ "$prima" = "$PORTA_PREDEFINITA" ]; then
        ok porta_ok "$prima"
    else
        avviso porta_spostata "$PORTA_PREDEFINITA" "$prima"
    fi
}

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

intestazione
[ "$DRY_RUN" = 1 ] && avviso prova
[ -d "$RADICE" ] && avviso esiste_aggiorno

passo controlli

export DEBIAN_FRONTEND=noninteractive

mancanti=()
# `ffmpeg` serve alle miniature dei video: senza, i video restano con l'icona
# del tipo e tutto il resto funziona lo stesso. Si installa comunque, perche'
# scoprirlo mancante davanti a una cartella di filmati e' peggio dei pochi
# megabyte che occupa.
# `rsync` non serve a install.sh: serve a update.sh (deploy/update.sh), che lo
# richiede e si ferma subito se manca. Va installato qui perche' e' l'unico
# punto che gira una volta sola con apt aggiornato — scoperto mancante sul
# primo aggiornamento reale mai fatto su un'installazione di questo progetto.
for pacchetto in curl nfs-common openssl ffmpeg rsync; do
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

WEB_AMBIGUO=0
if [ "$WEB" = "auto" ]; then
    ha_apache=0; ha_nginx=0
    { command -v apache2ctl >/dev/null 2>&1 || command -v apachectl >/dev/null 2>&1; } && ha_apache=1
    command -v nginx >/dev/null 2>&1 && ha_nginx=1

    if [ "$ha_apache" = 1 ]; then
        WEB="apache"
    elif [ "$ha_nginx" = 1 ]; then
        WEB="nginx"
    else
        errore web_assente
    fi
    # Con tutti e due installati la scelta e' vera, e va lasciata a chi
    # installa: indovinare significherebbe configurare quello sbagliato.
    [ "$ha_apache" = 1 ] && [ "$ha_nginx" = 1 ] && WEB_AMBIGUO=1
fi

# Con --web scelto esplicitamente, il ramo "auto" sopra non gira mai: senza
# questo controllo lo script proseguiva convinto che il web server ci fosse
# gia', e falliva tardi e in modo poco chiaro alla configurazione del vhost
# (es. "sites-available/anf.conf: No such file or directory") invece di
# installarlo o di dirlo subito.
if [ "$WEB" = "apache" ]; then
    if ! { command -v apache2ctl >/dev/null 2>&1 || command -v apachectl >/dev/null 2>&1; }; then
        passo web_installo apache2
        esegui apt-get update -qq
        esegui apt-get install -y -qq apache2
    fi
elif [ "$WEB" = "nginx" ]; then
    if ! command -v nginx >/dev/null 2>&1; then
        passo web_installo nginx
        esegui apt-get update -qq
        esegui apt-get install -y -qq nginx
    fi
fi

ok web_rilevato "$WEB"


# Cosa c'è sulla macchina, prima di toccarla.
sistema

# Le scelte, chieste a chi installa.
configura

# Dopo le domande, perché il web server può essere cambiato lì. La cartella dei
# log non porta il suo nome: Apache scrive in /var/log/apache2, e ricavarla da
# $WEB darebbe un percorso inesistente su cui il monitoraggio non leggerebbe
# mai nulla.
if [ "$WEB" = "apache" ]; then LOG_WEB="/var/log/apache2"; else LOG_WEB="/var/log/nginx"; fi

# La porta si sceglie qui: serve al file .env, al vhost e al controllo finale,
# e va decisa prima di tutti e tre.
scegli_porta

# Ultimo momento utile per fermarsi: da qui in poi si scrive sul sistema.
riepilogo_scelte

if [ "$WEB" = "apache" ]; then
    # Il pacchetto e il modulo sono due cose diverse: il pacchetto può essere
    # installato senza che il modulo sia attivo, e in quel caso i download
    # rispondono vuoti senza dire perche. Si verificano separatamente.
    if ! dpkg -s libapache2-mod-xsendfile >/dev/null 2>&1; then
        passo xsendfile
        esegui apt-get install -y -qq libapache2-mod-xsendfile
    fi

    # `remoteip` serve agli indirizzi reali dietro un reverse proxy, `headers`
    # alle intestazioni di ripresa, `proxy_http` a inoltrare all'API.
    mancanti_mod=""
    for mod in xsendfile remoteip headers proxy proxy_http; do
        apache2ctl -M 2>/dev/null | grep -q "${mod}_module" || mancanti_mod="$mancanti_mod $mod"
    done
    if [ -n "$mancanti_mod" ]; then
        passo moduli
        # shellcheck disable=SC2086
        esegui a2enmod $mancanti_mod
    fi
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
    # update.sh e uninstall.sh mancavano qui: il pacchetto li porta gia' in
    # radice (deploy/release.yml li copia apposta, per lo scaricamento
    # standalone), ma questo ciclo non li includeva mai nella cartella
    # d'installazione. La guida diceva "cd RADICE && sudo bash update.sh" da
    # sempre, e non c'era mai stato — trovato aggiornando per la prima volta
    # un'installazione reale invece di rieseguire solo install.sh.
    for file in README.md README.en.md CHANGELOG.md LICENSE .env.example update.sh uninstall.sh; do
        [ -f "$TEMP/$file" ] && cp -a "$TEMP/$file" "$RADICE/"
    done
    [ -f "$RADICE/update.sh" ] && chmod +x "$RADICE/update.sh"
    [ -f "$RADICE/uninstall.sh" ] && chmod +x "$RADICE/uninstall.sh"
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
ANF_ACCESS_LOG=${LOG_WEB}/anf_access.log
ANF_TRUSTED_PROXIES=127.0.0.1
FINE
        chown "$UTENTE:$GRUPPO" "$ENV_FILE"
        chmod 0600 "$ENV_FILE"
    fi
fi

passo migrazioni
esegui env -C "$RADICE/backend" "$RADICE/venv/bin/alembic" upgrade head

# Le migrazioni girano da root e creano il database di sua proprietà: senza
# questo passaggio l'API, che gira come utente non privilegiato, lo troverebbe
# in sola lettura e non partirebbe — dicendo «attempt to write a readonly
# database», che non lascia capire che è un problema di proprietà.
esegui chown -R "$UTENTE:$GRUPPO" "$DATI"

# Gli access log su Debian e Ubuntu sono di root, gruppo `adm`, e non
# leggibili da altri. Senza questo il pannello non sa mai quanti byte sono
# stati davvero inviati, e ogni trasferimento resta «in corso» per sempre.
esegui usermod -aG adm "$UTENTE"

# ---------------------------------------------------------------------------
# Servizi / Services
# ---------------------------------------------------------------------------

passo unit
for s in anf-agent anf-api; do
    # I percorsi nelle unit non possono essere fissi: le cartelle si scelgono
    # durante l'installazione, e una unit che punta altrove non parte.
    if [ "$DRY_RUN" = 0 ]; then
        sed -e "s|@@RADICE@@|$RADICE|g" -e "s|@@DATI@@|$DATI|g"             -e "s|@@MOUNT_ROOT@@|$MOUNT_ROOT|g" -e "s|@@SOCKET@@|$SOCKET_DIR/agent.sock|g"             -e "s|@@UTENTE@@|$UTENTE|g" -e "s|@@GRUPPO@@|$GRUPPO|g"             "$RADICE/deploy/systemd/${s}.service" >"/etc/systemd/system/${s}.service"
        chmod 0644 "/etc/systemd/system/${s}.service"
    else
        printf '       %s
' "installa /etc/systemd/system/${s}.service"
    fi
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
        # Il sito "default" di Debian/Ubuntu ha "listen 80 default_server",
        # che vince sempre su "server_name _" di anf.conf: senza toglierlo il
        # pannello risulta irraggiungibile (404) pur con una configurazione
        # valida — trovato installando su un server pulito. Rimosso solo se
        # e' ancora il sito di serie della distribuzione, per non toccare un
        # sito personalizzato con lo stesso nome.
        if [ -L /etc/nginx/sites-enabled/default ] &&
            [ "$(readlink -f /etc/nginx/sites-enabled/default)" = "/etc/nginx/sites-available/default" ]; then
            esegui rm -f /etc/nginx/sites-enabled/default
        fi

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
# "enable --now" su un servizio gia' attivo non lo riavvia: "start" e' un
# no-op se e' gia' in esecuzione. In un aggiornamento questo lasciava in
# piedi il processo vecchio, con il codice appena scaricato sul disco ma mai
# caricato — trovato verificando la versione dopo un aggiornamento reale,
# rimasta a quella precedente nonostante l'installer dicesse "completato".
# "restart" funziona in entrambi i casi: parte se non era attivo, ricarica
# se lo era.
esegui systemctl enable anf-agent
esegui systemctl restart anf-agent
esegui systemctl enable anf-api
esegui systemctl restart anf-api

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
        INSTALLAZIONE_OK=1
    else
        avviso verifica_ko
        # Dire "completata" quando i servizi non partono manda a cercare il
        # problema nel posto sbagliato, cioè da nessuna parte.
        INSTALLAZIONE_OK=0
    fi
fi

# ---------------------------------------------------------------------------
# Riepilogo / Summary
# ---------------------------------------------------------------------------

# L'indirizzo su cui il pannello si raggiunge davvero: quello della macchina in
# rete, non "localhost", che dal computer di chi installa non porta da nessuna
# parte. E non la porta dell'API, che ascolta solo in locale dietro il web
# server: scriverla come indirizzo manda a sbattere contro una connessione
# rifiutata.
IP_RETE="$(hostname -I 2>/dev/null | awk '{print $1}')"
[ -n "$IP_RETE" ] || IP_RETE="$(hostname 2>/dev/null || echo localhost)"

printf '
'
riga
if [ "$INSTALLAZIONE_OK" = 1 ]; then
    printf '  %s%s %s%s
' "$C_OK" "$S_OK" "$(m fatto)" "$C_FINE"
else
    printf '  %s%s %s%s
' "$C_WARN" "$S_WARN" "$(m fatto_a_meta)" "$C_FINE"
fi
riga
printf '
'

voce "$(m v_indirizzo)" "http://${IP_RETE}/pannello/"
voce "$(m v_porta_api)" "${PORTA_API} $(m v_solo_locale)"
printf '
'
voce "$(m v_utente)"   "admin"
voce "$(m v_password)" "${C_GRA}Admin1234${C_FINE}"
printf '
  %s%s%s

' "$C_WARN" "$(m credenziali)" "$C_FINE"

if [ "$INSTALLAZIONE_OK" != 1 ]; then
    printf '  %s

' "$(m come_indagare)"
fi
