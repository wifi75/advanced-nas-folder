<#
.SYNOPSIS
    Avvia backend e frontend in sviluppo, raggiungibili anche dalla rete locale.

.DESCRIPTION
    Apre i due servizi come schede della stessa finestra di Windows Terminal
    quando è disponibile, altrimenti in due finestre separate.

    Entrambi ascoltano su tutte le interfacce, così il pannello si può provare
    da un altro dispositivo della rete — un telefono, un tablet, un altro PC.

.PARAMETER SoloLocale
    Ascolta solo su 127.0.0.1, come prima. Da usare quando non serve provare da
    altri dispositivi.

.EXAMPLE
    .\avvia-dev.ps1
    .\avvia-dev.ps1 -SoloLocale
#>

[CmdletBinding()]
param(
    [switch]$SoloLocale,
    [int]$PortaApi = 8100,
    [int]$PortaWeb = 5195
)

$ErrorActionPreference = 'Stop'
$radice = $PSScriptRoot
$ascolto = if ($SoloLocale) { '127.0.0.1' } else { '0.0.0.0' }

# --- controlli preliminari -------------------------------------------------

$python = Join-Path $radice 'backend\.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
    Write-Error @"
Ambiente Python assente. Crealo con:
    cd backend
    python3.14 -m venv .venv
    .venv\Scripts\pip install -e ".[dev]"
"@
}

if (-not (Test-Path (Join-Path $radice 'frontend\node_modules'))) {
    Write-Error "Dipendenze del frontend assenti. Esegui: cd frontend; npm install"
}

if (-not (Test-Path (Join-Path $radice 'backend\.env'))) {
    Write-Warning "backend\.env non trovato: copia .env.example e genera ANF_SECRET_KEY."
}

# --- indirizzo in rete -----------------------------------------------------

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
    Sort-Object -Property SkipAsSource |
    Select-Object -First 1).IPAddress

# --- avvio -----------------------------------------------------------------

$cmdApi = "cd '$radice\backend'; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host $ascolto --port $PortaApi --reload"
$cmdWeb = "cd '$radice\frontend'; npm run dev -- --port $PortaWeb" + $(if ($SoloLocale) { ' --host 127.0.0.1' } else { ' --host' })

$wt = Get-Command wt.exe -ErrorAction SilentlyContinue
if ($wt) {
    # Due schede della stessa finestra. Il punto e virgola va sfuggito con un
    # apice inverso, altrimenti PowerShell lo interpreta come proprio separatore.
    & wt.exe -w 0 new-tab --title 'ANF api' powershell -NoExit -Command $cmdApi `; `
        new-tab --title 'ANF web' powershell -NoExit -Command $cmdWeb
}
else {
    # Ripiego: due finestre separate.
    Start-Process powershell -ArgumentList '-NoExit', '-Command', $cmdApi
    Start-Process powershell -ArgumentList '-NoExit', '-Command', $cmdWeb
}

# --- riepilogo -------------------------------------------------------------

Write-Host ''
Write-Host 'Advanced NAS Folder - ambiente di sviluppo' -ForegroundColor Cyan
Write-Host ''
Write-Host ("  Pannello   http://localhost:{0}/pannello/" -f $PortaWeb)
Write-Host ("  API        http://localhost:{0}/docs" -f $PortaApi)

if (-not $SoloLocale -and $ip) {
    Write-Host ''
    Write-Host '  Dalla rete locale:' -ForegroundColor Cyan
    Write-Host ("  Pannello   http://{0}:{1}/pannello/" -f $ip, $PortaWeb)
    Write-Host ("  API        http://{0}:{1}/docs" -f $ip, $PortaApi)
    Write-Host ''
    Write-Host '  ATTENZIONE: il pannello e raggiungibile da chiunque sia nella tua' -ForegroundColor Yellow
    Write-Host '  rete, e in sviluppo le credenziali iniziali sono admin/admin.' -ForegroundColor Yellow
    Write-Host '  Usa -SoloLocale quando non ti serve provarlo da altri dispositivi.' -ForegroundColor Yellow
}

Write-Host ''
