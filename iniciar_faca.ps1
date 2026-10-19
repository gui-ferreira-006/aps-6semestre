<#
.SYNOPSIS
    Inicializador do Terminal Desktop Biométrico F.A.C.A. (PIVC 2026/2)
.DESCRIPTION
    Script PowerShell para subir o contêiner Docker do Backend FastAPI e
    iniciar o Launcher Desktop nativo (PyWebView) no ambiente Windows.
.PARAMETER Kiosk
    Inicia a janela em modo Totem/Kiosk (tela cheia sem moldura).
.PARAMETER Debug
    Habilita ferramentas de desenvolvedor (DevTools) no PyWebView.
.PARAMETER NoWait
    Inicia o PyWebView imediatamente sem aguardar o health check /ping.
.EXAMPLE
    .\iniciar_faca.ps1
    .\iniciar_faca.ps1 -Kiosk
    .\iniciar_faca.ps1 -Debug
#>

param(
    [switch]$Kiosk,
    [Alias("DevTools")][switch]$Debug,
    [switch]$NoWait,
    [string]$Url = "http://localhost:8000"
)

$Host.UI.RawUI.WindowTitle = "F.A.C.A. - Terminal Biometrico (Inicializador)"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  F.A.C.A. - Frente de Autenticacao e Controle de Acesso" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host "  Inicializador do Terminal Desktop Biometrico" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar e Subir o Contêiner Docker
Write-Host "[1/3] Verificando contêineres Docker do Backend..." -ForegroundColor Yellow

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($null -eq $dockerCmd) {
    Write-Warning "Docker CLI não encontrado no PATH. Certifique-se de que o Docker Desktop está em execução."
} else {
    Write-Host "Subindo serviços via 'docker compose up -d'..." -ForegroundColor DarkGray
    docker compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Host " [OK] Backend Docker está ativo e rodando." -ForegroundColor Green
    } else {
        Write-Warning "Docker compose retornou código de erro $LASTEXITCODE. Tentando prosseguir..."
    }
}
Write-Host ""

# 2. Localizar Interpretador Python no Ambiente Virtual
Write-Host "[2/3] Localizando ambiente Python local..." -ForegroundColor Yellow

$pythonExec = $null
if (Test-Path "venv\Scripts\python.exe") {
    $pythonExec = "venv\Scripts\python.exe"
    Write-Host " [OK] Ambiente virtual encontrado: $pythonExec" -ForegroundColor Green
} elseif (Test-Path ".venv\Scripts\python.exe") {
    $pythonExec = ".venv\Scripts\python.exe"
    Write-Host " [OK] Ambiente virtual encontrado: $pythonExec" -ForegroundColor Green
} else {
    $sysPython = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $sysPython) {
        $pythonExec = "python"
        Write-Warning "venv não localizado. Utilizando Python do sistema."
    } else {
        Write-Error "Nenhum executável Python encontrado. Crie o venv local executando: python -m venv venv"
        exit 1
    }
}

# Verificar se pywebview está instalado
& $pythonExec -c "import webview" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Biblioteca 'pywebview' não detectada. Instalando requirements-desktop.txt..." -ForegroundColor Yellow
    & $pythonExec -m pip install -r requirements-desktop.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha ao instalar dependências de requirements-desktop.txt."
        exit 1
    }
    Write-Host " [OK] Dependências desktop instaladas com sucesso!" -ForegroundColor Green
}
Write-Host ""

# 3. Executar o Launcher Desktop
Write-Host "[3/3] Iniciando o Terminal Desktop Biométrico F.A.C.A. (launcher.py)..." -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor DarkCyan

$launcherArgs = @()
if ($Kiosk) { $launcherArgs += "--kiosk" }
if ($Debug) { $launcherArgs += "--debug" }
if ($NoWait) { $launcherArgs += "--no-wait" }
if ($Url -ne "http://localhost:8000") { $launcherArgs += "--url", $Url }

& $pythonExec launcher.py @launcherArgs
$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "[INFO] Terminal F.A.C.A. finalizado (Código de saída: $exitCode)." -ForegroundColor DarkGray

