@echo off
setlocal enabledelayedexpansion

title F.A.C.A. - Reset Instantaneo Pre-Banca (Dia Zero)

echo ==============================================================================
echo   F.A.C.A. - RESET INSTANTANEO PRE-BANCA (ESTADO DIA ZERO)
echo   Expurgo de Volume e Recriacao Limpa do Banco aps_biometria
echo ==============================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0resetar_apresentacao.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

if %EXIT_CODE% NEQ 0 (
    echo.
    echo [ERRO] O reset encontrou uma falha (Codigo: %EXIT_CODE%).
    pause
    exit /b %EXIT_CODE%
)

endlocal
