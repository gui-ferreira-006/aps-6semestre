"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)

Launcher Desktop Nativo (Totem / Terminal Biométrico com PyWebView)
==============================================================================

Este script executa a aplicação F.A.C.A. no sistema hospedeiro (Windows) como
um aplicativo Desktop nativo de missão crítica para terminal biométrico,
sem barras de navegação ou controles de browser convencional.

Funcionamento:
  1. Verifica a conectividade com o Backend FastAPI (GET /ping);
  2. Se a API estiver respondendo no Docker (ou local), abre a janela gráfica
     nativa apontando diretamente para http://localhost:8000;
  3. Caso a API não esteja acessível, exibe no terminal e em janela gráfica
     uma tela de diagnóstico com a identidade visual do F.A.C.A., orientando
     a inicialização dos contêineres (docker compose up -d) com botão de
     reconectar automático.

Uso:
    python launcher.py
    python launcher.py --kiosk       # Modo Totem / Tela Cheia
    python launcher.py --url http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

# Configuração de Logging do Launcher
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("faca.launcher")

# Importação condicional do pywebview com tratamento amigável de erro
try:
    import webview  # type: ignore[import-not-found]
except ImportError:
    webview = None  # type: ignore[assignment]


# =============================================================================
# Constantes do Launcher
# =============================================================================
URL_PADRAO: str = "http://localhost:8000"
TITULO_JANELA: str = "F.A.C.A. — Terminal Biométrico de Segurança Máxima (MMA)"
LARGURA_PADRAO: int = 1280
ALTURA_PADRAO: int = 800
LARGURA_MINIMA: int = 1024
ALTURA_MINIMA: int = 700
COR_FUNDO: str = "#0a0b0e"

# =============================================================================
# Tela de Diagnóstico Offline (Cyberpunk / Militar MMA)
# =============================================================================
TELA_DIAGNOSTICO_HTML: str = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>F.A.C.A. - Diagnóstico de Conexão</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: #0a0b0e;
      color: #dfe4ec;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      overflow: hidden;
      padding: 20px;
    }
    .diag-card {
      background: rgba(16, 20, 28, 0.95);
      border: 1px solid rgba(255, 42, 64, 0.4);
      box-shadow: 0 0 40px rgba(255, 42, 64, 0.15);
      border-radius: 8px;
      max-width: 620px;
      width: 100%;
      padding: 40px;
      text-align: center;
      position: relative;
    }
    .diag-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, #ff2a40, #ff6b81, #ff2a40);
    }
    .icon-alert {
      width: 64px;
      height: 64px;
      margin: 0 auto 20px;
      color: #ff2a40;
    }
    h1 {
      font-size: 24px;
      letter-spacing: 2px;
      color: #ffffff;
      margin-bottom: 8px;
    }
    h2 {
      font-size: 13px;
      letter-spacing: 3px;
      color: #ff4757;
      margin-bottom: 24px;
      font-weight: 600;
    }
    p {
      color: #a0aab8;
      font-size: 15px;
      line-height: 1.6;
      margin-bottom: 20px;
    }
    .code-box {
      background: #050608;
      border: 1px dashed rgba(255, 255, 255, 0.2);
      border-radius: 4px;
      padding: 14px;
      font-family: Consolas, monospace;
      color: #2ed573;
      font-size: 15px;
      margin-bottom: 28px;
      user-select: all;
    }
    .btn-retry {
      background: #ff2a40;
      color: #ffffff;
      border: none;
      padding: 12px 28px;
      font-size: 14px;
      letter-spacing: 1.5px;
      font-weight: 700;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .btn-retry:hover {
      background: #ff4757;
      box-shadow: 0 0 15px rgba(255, 71, 87, 0.5);
    }
    .status-poll {
      margin-top: 18px;
      font-size: 12px;
      color: #6b7787;
    }
  </style>
</head>
<body>
  <div class="diag-card">
    <svg class="icon-alert" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
    <h1>F.A.C.A. — TERMINAL OFFLINE</h1>
    <h2>BACKEND BIOMÉTRICO INACESSÍVEL</h2>
    <p>O servidor FastAPI não respondeu na porta 8000. Certifique-se de que o contêiner Docker do backend esteja ativo executando no terminal:</p>
    <div class="code-box">docker compose up -d</div>
    <button class="btn-retry" id="btn-retest" onclick="tentarReconectar()">TENTAR RECONECTAR</button>
    <div class="status-poll" id="status-poll">Verificando automaticamente a cada 3 segundos...</div>
  </div>

  <script>
    async function tentarReconectar() {
      const btn = document.getElementById('btn-retest');
      const info = document.getElementById('status-poll');
      btn.disabled = true;
      btn.innerText = 'CONECTANDO...';
      info.innerText = 'Consultando http://localhost:8000/ping...';

      try {
        const res = await fetch('http://localhost:8000/ping');
        if (res.ok) {
          info.innerText = 'Servidor online! Carregando terminal biométrico...';
          window.location.href = 'http://localhost:8000/';
          return;
        }
      } catch (e) {
        // continua offline
      }

      setTimeout(() => {
        btn.disabled = false;
        btn.innerText = 'TENTAR RECONECTAR';
        info.innerText = 'Ainda offline. Aguardando inicialização do Docker...';
      }, 1000);
    }

    // Polling automático suave
    setInterval(async () => {
      try {
        const res = await fetch('http://localhost:8000/ping');
        if (res.ok) {
          window.location.href = 'http://localhost:8000/';
        }
      } catch (e) {}
    }, 3000);
  </script>
</body>
</html>
"""


# =============================================================================
# Funções Auxiliares de Conectividade
# =============================================================================

def verificar_api_online(base_url: str, timeout: float = 2.5) -> bool:
    """
    Realiza uma consulta rápida ao endpoint de Health Check (GET /ping)
    da API para atestar que o servidor FastAPI está funcional.
    """
    ping_url = f"{base_url.rstrip('/')}/ping"
    try:
        requisicao = urllib.request.Request(
            ping_url,
            headers={"User-Agent": "FACA-Desktop-Launcher/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            if resposta.status == 200:
                corpo = json.loads(resposta.read().decode("utf-8"))
                return bool(corpo.get("status") == "ok")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False
    return False


def aguardar_api_online(base_url: str, max_tentativas: int = 3, intervalo: float = 1.0) -> bool:
    """Tenta conectar na API repetidamente até o limite de tentativas."""
    for tentativa in range(1, max_tentativas + 1):
        logger.info("Verificando status da API em %s (tentativa %d/%d)...", base_url, tentativa, max_tentativas)
        if verificar_api_online(base_url, timeout=2.0):
            logger.info("Backend F.A.C.A. detectado e operacional!")
            return True
        if tentativa < max_tentativas:
            time.sleep(intervalo)
    return False


# =============================================================================
# Ponto de Entrada Principal do Launcher
# =============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="F.A.C.A. — Terminal Desktop Nativo de Reconhecimento Facial (MMA)"
    )
    parser.add_argument(
        "--url",
        default=URL_PADRAO,
        help=f"URL base do servidor FastAPI (padrão: {URL_PADRAO})",
    )
    parser.add_argument(
        "--kiosk",
        "-k",
        action="store_true",
        help="Inicia a janela em modo Totem/Quiosque (tela cheia sem barra de título)",
    )
    parser.add_argument(
        "--fullscreen",
        "-f",
        action="store_true",
        help="Inicia a janela em modo Tela Cheia convencional",
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Habilita console de ferramentas de desenvolvedor (DevTools)",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Abre a janela imediatamente sem esperar confirmação do /ping",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Validação do pacote pywebview
    if webview is None:
        logger.error(
            "Biblioteca 'pywebview' não encontrada no ambiente virtual.\n"
            "Instale as dependências desktop executando:\n"
            "    pip install -r requirements-desktop.txt"
        )
        return 1

    base_url: str = args.url.rstrip("/")
    api_online: bool = True

    if not args.no_wait:
        api_online = aguardar_api_online(base_url, max_tentativas=2, intervalo=0.8)

    # Define se abre a URL direta da aplicação ou a tela embutida de diagnóstico
    if api_online:
        target = f"{base_url}/"
        logger.info("Iniciando janela Desktop conectada a %s", target)
    else:
        target = None
        logger.warning(
            "Backend F.A.C.A. não respondeu em %s. Exibindo tela de diagnóstico.", base_url
        )

    # Criação da janela nativa PyWebView
    fullscreen_mode = bool(args.kiosk or args.fullscreen)

    if target is not None:
        janela = webview.create_window(
            title=TITULO_JANELA,
            url=target,
            width=LARGURA_PADRAO,
            height=ALTURA_PADRAO,
            min_size=(LARGURA_MINIMA, ALTURA_MINIMA),
            background_color=COR_FUNDO,
            fullscreen=fullscreen_mode,
            confirm_close=True,
            text_select=False,
        )
    else:
        janela = webview.create_window(
            title=TITULO_JANELA,
            html=TELA_DIAGNOSTICO_HTML,
            width=LARGURA_PADRAO,
            height=ALTURA_PADRAO,
            min_size=(LARGURA_MINIMA, ALTURA_MINIMA),
            background_color=COR_FUNDO,
            fullscreen=fullscreen_mode,
            confirm_close=True,
            text_select=False,
        )

    # Inicializa o loop de eventos gráfico da interface nativa
    webview.start(debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
