"""
==============================================================================
F.A.C.A. - Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) - APS 2026/2 (UNIP)
Ponto de Entrada da API (Entrypoint)
==============================================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Instanciação da aplicação FastAPI com metadados informativos
app = FastAPI(
    title="Motor Backend para o PIVC - APS 2026/2",
    description=(
        "API RESTful do Sistema de Identificação e Autenticação Biométrica "
        "(F.A.C.A.) desenvolvido para controle de acesso ao cofre de segurança máxima "
        "do Ministério do Meio Ambiente."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 2. Configuração de CORS (Cross-Origin Resource Sharing)
# Para permitir wildcard ("*") sem violar a especificação W3C e navegadores,
# allow_credentials deve ser False ao usar allow_origins=["*"].
# (A API utiliza token Bearer no header Authorization, não necessitando de cookies de sessão)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Rota de Health Check (Teste de Conectividade)
@app.get(
    "/ping",
    tags=["Health Check"],
    summary="Verifica o status operacional da API",
    response_description="Retorna a confirmação de que o servidor está no ar"
)
async def ping() -> dict:
    """
    Endpoint simples para o Frontend ou orquestrador testar se o servidor
    está respondendo requisições antes de abrir a câmera ou submeter formulários.
    """
    return {
        "status": "ok",
        "mensagem": "API PIVC Operante"
    }


if __name__ == "__main__":
    import uvicorn

    # Permite execução direta via `python main.py` durante o desenvolvimento local
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
