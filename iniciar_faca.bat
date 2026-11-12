@echo off
setlocal enabledelayedexpansion

title F.A.C.A. - Terminal Biometrico (Inicializador Desktop)

echo ==============================================================================
echo   F.A.C.A. - Frente de Autenticacao e Controle de Acesso (PIVC 2026/2)
echo   Inicializador do Terminal Desktop Biometrico
echo ==============================================================================
echo.

:: 1. Verificar Docker
echo [1/3] Verificando conteineres Docker do Backend...
where docker >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Docker nao encontrado no PATH do sistema.
    echo Certifique-se de que o Docker Desktop esta instalado e em execucao.
    echo Prosseguindo para tentar conectar ao servidor local...
    echo.
) else (
    echo [INFO] Garantindo que o ambiente Docker esta em execucao (docker compose up -d)...
    docker compose up -d
    if %ERRORLEVEL% NEQ 0 (
        echo [AVISO] Ocorreu uma falha ao executar 'docker compose up -d'.
        echo Tentando prosseguir com o Launcher Desktop...
    ) else (
        echo [OK] Servicos Docker iniciados com sucesso!
    )
    echo.
)

:: 2. Identificar Ambiente Virtual Python Local
echo [2/3] Localizando ambiente Python local para o PyWebView...
set "PYTHON_EXEC="

if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXEC=venv\Scripts\python.exe"
    echo [OK] Ambiente virtual encontrado em: venv\Scripts\python.exe
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXEC=.venv\Scripts\python.exe"
    echo [OK] Ambiente virtual encontrado em: .venv\Scripts\python.exe
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "PYTHON_EXEC=python"
        echo [AVISO] venv nao detectado. Utilizando Python padrao do sistema: python
    ) else (
        echo [ERRO CRITICO] Nenhum executavel Python foi encontrado no sistema ou na pasta venv!
        echo Crie o ambiente virtual local com:
        echo     python -m venv venv
        echo     .\venv\Scripts\pip install -r requirements-desktop.txt
        pause
        exit /b 1
    )
)
echo.

:: 3. Verificar instalacao do pywebview
"%PYTHON_EXEC%" -c "import webview" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] A biblioteca 'pywebview' nao esta instalada no ambiente Python selecionado.
    echo Instalando dependencias desktop via requirements-desktop.txt...
    "%PYTHON_EXEC%" -m pip install -r requirements-desktop.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERRO] Falha ao instalar dependencias desktop.
        pause
        exit /b 1
    )
    echo [OK] Dependencias instaladas com sucesso!
    echo.
)

:: 4. Executar o Launcher Desktop
echo [3/3] Iniciando o Terminal Desktop Biometrico F.A.C.A. (launcher.py)...
echo ==============================================================================
echo.

"%PYTHON_EXEC%" launcher.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] O terminal foi encerrado com codigo de retorno: %ERRORLEVEL%
)

endlocal
