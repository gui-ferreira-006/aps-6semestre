"""
==============================================================================
F.A.C.A. - Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) - APS 2026/2 (UNIP)
Ponto de Entrada da API (Entrypoint)
==============================================================================
"""

# ── Bibliotecas padrão ──
from datetime import datetime, timezone

# ── Bibliotecas de terceiros ──
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Módulos locais (schemas Pydantic v2) ──
from schemas import PingResponse

# =============================================================================
# 1. Instanciação da aplicação FastAPI com metadados informativos
# =============================================================================
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

# =============================================================================
# 2. Configuração de CORS (Cross-Origin Resource Sharing)
# =============================================================================
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

# =============================================================================
# 3. Rota de Health Check (Teste de Conectividade)
# =============================================================================
# O parâmetro `response_model` desempenha dois papéis fundamentais:
#   a) Documentação automática: o Swagger (/docs) e o Redoc (/redoc) exibem
#      o schema PingResponse com exemplos e tipos dos campos.
#   b) Filtragem de segurança: o FastAPI serializa a resposta usando o schema,
#      garantindo que apenas os campos declarados sejam devolvidos ao cliente
#      — mesmo que o dicionário interno contenha chaves extras acidentais.


@app.get(
    "/ping",
    response_model=PingResponse,
    status_code=200,
    tags=["Health Check"],
    summary="Verifica o status operacional da API",
    response_description="Retorna a confirmação de que o servidor está no ar, "
                         "incluindo versão e timestamp UTC",
)
async def ping() -> PingResponse:
    """
    Endpoint de Health Check utilizado pelo Frontend ou orquestrador para
    validar se o servidor FastAPI está operacional antes de abrir a câmera
    ou exibir formulários.

    A saída passa pela validação e serialização do schema Pydantic
    ``PingResponse``, assegurando conformidade com o contrato definido
    em API.md (Seção 4.1).
    """
    return PingResponse(
        status="ok",
        mensagem="Servidor F.A.C.A. operacional",
        versao="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )


if __name__ == "__main__":
    import uvicorn

    # Permite execução direta via `python main.py` durante o desenvolvimento local
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
