# Esegue tutti i controlli che la CI eseguira' al push, nello stesso ordine.
#
# Esiste perche' lanciarli a mano uno per uno e' andato storto due volte: il
# comando finiva con una pipe verso `tail` per leggere solo il riepilogo, e la
# pipe restituisce l'esito dell'ultimo comando — non quello di pytest. I test
# erano rossi, il comando risultava riuscito, e il difetto e' arrivato su
# GitHub.
#
#   .\controlla.ps1

$ErrorActionPreference = 'Stop'
$radice = $PSScriptRoot
$python = Join-Path $radice 'backend\.venv\Scripts\python.exe'
$fallite = @()

function Passo {
    param([string]$Nome, [scriptblock]$Comando)

    Write-Host ""
    Write-Host "==> $Nome" -ForegroundColor Cyan
    & $Comando
    if ($LASTEXITCODE -ne 0) {
        $script:fallite += $Nome
        Write-Host "    FALLITO" -ForegroundColor Red
    }
}

Passo 'Formattazione (ruff format)' { & $python -m ruff format --check $radice }
Passo 'Analisi statica (ruff check)' { & $python -m ruff check $radice }
Passo 'Tipi del backend (mypy)' {
    Push-Location (Join-Path $radice 'backend')
    & $python -m mypy app
    Pop-Location
}
Passo 'Test (pytest)' { & $python -m pytest -q $radice }

Push-Location (Join-Path $radice 'frontend')
Passo 'Tipi del pannello (vue-tsc)' { npm run --silent typecheck }
Passo 'Analisi statica del pannello (eslint)' { npm run --silent lint }
Passo 'Compilazione del pannello' { npm run --silent build }
Pop-Location

Write-Host ""
if ($fallite.Count -eq 0) {
    Write-Host "Tutti i controlli sono passati." -ForegroundColor Green
    exit 0
}

Write-Host "Controlli falliti:" -ForegroundColor Red
$fallite | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
exit 1
