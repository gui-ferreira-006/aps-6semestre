<#
.SYNOPSIS
    Script de Reset Instantaneo Pre-Banca — F.A.C.A. (PIVC 2026/2)
.DESCRIPTION
    Derruba os conteineres atuais, remove o volume persistente do MySQL
    (docker compose down -v), sobe novamente o ambiente limpo (docker compose up -d),
    aguarda o MySQL 8.0 e a API FastAPI responderem 200 OK em GET /ping e
    confirma que o banco aps_biometria esta 100% zerado ("Estado Dia Zero")
    e pronto para a apresentacao oficial.
.EXAMPLE
    .\resetar_apresentacao.ps1
#>

param(
    [string]$Url = "http://localhost:8000",
    [int]$TimeoutSegundos = 90
)

$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "F.A.C.A. - Reset Instantaneo Pre-Banca (Dia Zero)"

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  F.A.C.A. - RESET INSTANTANEO PRE-BANCA (ESTADO DIA ZERO)" -ForegroundColor White -BackgroundColor DarkRed
Write-Host "  Expurgo de Volume e Recriacao Limpa do Banco aps_biometria" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Derrubar conteineres e deletar volume persistente
Write-Host "[1/3] Executando 'docker compose down -v' (removendo volume faca_mysql_data)..." -ForegroundColor Yellow
docker compose down -v --remove-orphans
if ($LASTEXITCODE -ne 0) {
    Write-Error "Falha ao executar 'docker compose down -v'. Verifique se o Docker Desktop esta rodando."
    exit 1
}
Write-Host " [OK] Conteineres e volume persistente removidos com sucesso." -ForegroundColor Green
Write-Host ""

# 2. Subir conteineres novamente em modo limpo
Write-Host "[2/3] Executando 'docker compose up -d' (recriando schema e seeds oficiais)..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Error "Falha ao executar 'docker compose up -d'."
    exit 1
}
Write-Host " [OK] Conteineres iniciados. Aguardando inicializacao do MySQL 8.0 e da API..." -ForegroundColor Green
Write-Host ""

# 3. Aguardar GET /ping responder 200 OK com MySQL conectado
Write-Host "[3/3] Aguardando MySQL e API responderem 200 OK em $Url/ping ..." -ForegroundColor Yellow
$inicio = Get-Date
$pronto = $false
$pingDados = $null

while (((Get-Date) - $inicio).TotalSeconds -lt $TimeoutSegundos) {
    try {
        $resp = Invoke-WebRequest -Uri "$Url/ping" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            $json = $resp.Content | ConvertFrom-Json
            if ($json.status -eq "ok" -and $json.mensagem -match "MySQL conectado") {
                $pronto = $true
                $pingDados = $json
                break
            }
        }
    } catch {
        # Ainda inicializando
    }
    Write-Host "." -NoNewline -ForegroundColor DarkGray
    Start-Sleep -Seconds 2
}
Write-Host ""

if (-not $pronto) {
    Write-Error "Tempo limite excedido ($TimeoutSegundos s) aguardando $Url/ping responder 200 OK."
    exit 1
}

# Verificar contagens rapidas no MySQL para exibicao no terminal
$contagemSql = "SELECT CONCAT('biometria=', (SELECT COUNT(*) FROM biometria), ' | tentativa_autenticacao=', (SELECT COUNT(*) FROM tentativa_autenticacao), ' | bloqueio_login=', (SELECT COUNT(*) FROM bloqueio_login), ' | auditoria=', (SELECT COUNT(*) FROM auditoria), ' | usuario=', (SELECT COUNT(*) FROM usuario), ' | toxina=', (SELECT COUNT(*) FROM toxina), ' | documento=', (SELECT COUNT(*) FROM documento)) AS resumo;"
$resumoTabelas = docker exec faca_mysql_db mysql --default-character-set=utf8mb4 -u faca_user -pfaca_pass_2026 -D aps_biometria -N -e $contagemSql 2>$null

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "  [SUCESSO] BANCO 'aps_biometria' 100% ZERADO E PRONTO PARA A BANCA!" -ForegroundColor Black -BackgroundColor Green
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "  Status API      : 200 OK - $($pingDados.mensagem)" -ForegroundColor White
Write-Host "  Instancia Banco : $($pingDados.instancia_banco)" -ForegroundColor Gray
if ($resumoTabelas) {
    Write-Host "  Estado Tabelas  : $resumoTabelas" -ForegroundColor Cyan
}
Write-Host "  Interface Web   : http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Launcher Nativo : .\iniciar_faca.ps1" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Green
