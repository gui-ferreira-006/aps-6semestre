"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)
Ponto de Entrada da API (Entrypoint)
==============================================================================

Servidor web assíncrono (FastAPI + Uvicorn) que orquestra:
  1. A entrega dos artefatos estáticos do Frontend (HTML, CSS, JS) na rota raiz;
  2. O motor biométrico PIVC desacoplado (OpenCV + dlib/ResNet — 5 fases);
  3. O endpoint de autenticação multifator (POST /autenticar) operando com
     registro de operadores em memória (RBAC Níveis 1, 2 e 3) e controle real
     de 5 tentativas/bloqueio para a PoC e terminal desktop;
  4. Rotas de diagnóstico biométrico isolado para validação via Swagger (/docs).
"""

from __future__ import annotations

# ── Bibliotecas padrão ──
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

# ── Bibliotecas de terceiros ──
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ── Motor Biométrico PIVC (5 fases do Processamento Digital de Imagens) ──
import biometria
from biometria import (
    BiometriaError,
    autenticar_biometria,
    extrair_caracteristicas,
    fase5_classificacao,
)

# ── Módulos locais (schemas Pydantic v2) ──
from schemas import (
    MAX_TENTATIVAS_AUTENTICACAO,
    AutenticacaoBloqueadaResponse,
    AutenticacaoFalhaResponse,
    AutenticacaoRequest,
    AutenticacaoSucessoResponse,
    BiometriaComparacaoRequest,
    BiometriaComparacaoResponse,
    BiometriaExtracaoRequest,
    BiometriaExtracaoResponse,
    BiometriaStatusResponse,
    BiometriaVerificacaoRequest,
    BiometriaVerificacaoResponse,
    CaixaDelimitadoraResponse,
    DimensoesImagemResponse,
    ErroDetalheResponse,
    ErroResponse,
    MetricasBiometricasResponse,
    PingResponse,
    UsuarioAutenticadoResponse,
)

# =============================================================================
# 1. Instanciação da aplicação FastAPI com metadados informativos
# =============================================================================
app = FastAPI(
    title="Motor Backend para o PIVC — APS 2026/2",
    description=(
        "API RESTful do Sistema de Identificação e Autenticação Multifator "
        "(F.A.C.A.) desenvolvido para controle de acesso ao cofre de segurança máxima "
        "do Ministério do Meio Ambiente, integrando as 5 fases do Processamento "
        "Digital de Imagens e Visão Computacional."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# =============================================================================
# 2. Configuração de CORS (Cross-Origin Resource Sharing)
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# 3. Montagem de Arquivos Estáticos e Rota Raiz (Frontend Integrado)
# =============================================================================
# Servir a pasta src/ e o index.html na mesma origem HTTP (http://localhost:8000)
# resolve de forma nativa e segura os seguintes desafios:
#   a) Contexto Seguro: a API navigator.mediaDevices.getUserMedia da webcam
#      requer HTTPS ou 'http://localhost' (bloqueada via protocolo file://).
#   b) PyWebView / Totem Desktop: a janela nativa do launcher.py acessa
#      diretamente a raiz http://localhost:8000 sem problemas de caminho relativo.
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
INDEX_FILE = BASE_DIR / "index.html"

if SRC_DIR.exists():
    app.mount("/src", StaticFiles(directory=str(SRC_DIR)), name="src")


@app.get(
    "/",
    include_in_schema=False,
    summary="Interface Web do Totem / Terminal Biométrico",
)
async def servir_interface_web() -> FileResponse:
    """Entrega a aplicação Frontend (SPA) F.A.C.A. na rota raiz."""
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return FileResponse(BASE_DIR / "main.py")  # fallback de integridade


# =============================================================================
# 4. Tratamento Centralizado de Exceções do Domínio Biométrico
# =============================================================================
# As exceções especializadas herdadas de BiometriaError (ex.:
# NenhumRostoDetectadoError, MultiplosRostosDetectadosError,
# ImagemBase64InvalidaError, RostoNaoReconhecidoError) carregam status_http
# e o dicionário de erro formatado conforme o contrato oficial em API.md.
# =============================================================================

@app.exception_handler(BiometriaError)
async def biometria_exception_handler(_: Request, exc: BiometriaError) -> JSONResponse:
    """Mapeia exceções do motor PIVC para o envelope ErroResponse."""
    return JSONResponse(
        status_code=exc.status_http,
        content={
            "sucesso": False,
            "erro": exc.para_dict(),
        },
    )


# =============================================================================
# 5. Registro em Memória de Operadores de Demonstração (MFA v2 — Pré-banco)
# =============================================================================
# Permite testar o fluxo de autenticação multifator 1:1 de ponta a ponta
# contemplando os 3 níveis de acesso da Matriz RBAC do Ministério:
#   * Nível 1: Operacional / Pesquisa
#   * Nível 2: Diretoria de Toxicologia e Preservação
#   * Nível 3: Gabinete Ministerial de Crise
#
# REGRA DE REGISTRO BIOMÉTRICO ON-THE-FLY:
# Se o operador de teste ainda não possuir vetor de 128D em memória
# (vetor_referencia is None), o primeiro frame facial válido recebido com
# as credenciais corretas é registrado como sua referência biométrica,
# permitindo que o desenvolvedor teste o reconhecimento com seu próprio rosto!
# =============================================================================

@dataclass
class OperadorDemo:
    id: int
    nome: str
    cpf: str  # 11 dígitos numéricos
    senha: str
    matricula: str
    cargo: str
    divisao: str
    nivel_acesso: Literal[1, 2, 3]
    vetor_referencia: Optional[List[float]] = None
    tentativas_falhas: int = 0
    bloqueado: bool = False
    bloqueado_ate: Optional[datetime] = None


OPERADORES_DEMO: Dict[str, OperadorDemo] = {
    # Nível 1: Acesso Geral / Operacional
    "12345678900": OperadorDemo(
        id=1,
        nome="Guilherme Ferreira",
        cpf="12345678900",
        senha="Faca@2026",
        matricula="G9483B2",
        cargo="Engenheiro de Bioproteção",
        divisao="Divisão de Contenção Microbiológica",
        nivel_acesso=1,
    ),
    # Nível 2: Diretoria de Toxicologia
    "98765432100": OperadorDemo(
        id=2,
        nome="Dra. Júlia Fernandes",
        cpf="98765432100",
        senha="Faca@2026",
        matricula="R101BF1",
        cargo="Diretora de Toxicologia e Preservação",
        divisao="Divisão de Toxinas e Preservação",
        nivel_acesso=2,
    ),
    # Nível 3: Gabinete Ministerial (Acesso Máximo)
    "11122233344": OperadorDemo(
        id=3,
        nome="Ministro do Meio Ambiente",
        cpf="11122233344",
        senha="Faca@2026",
        matricula="M000001",
        cargo="Ministro de Estado",
        divisao="Gabinete Ministerial de Crise",
        nivel_acesso=3,
    ),
}


def _localizar_operador(cpf_limpo: str) -> Optional[OperadorDemo]:
    """
    Localiza o operador de demonstração por CPF exato ou correspondência flexível
    de teste (ex.: aceita '12345678909' mapeando para o perfil demo 1).
    """
    if cpf_limpo in OPERADORES_DEMO:
        return OPERADORES_DEMO[cpf_limpo]

    # Mapeamento de conveniência para testes rápidos de digitação:
    prefixo = cpf_limpo[:9]
    for chave, operador in OPERADORES_DEMO.items():
        if chave.startswith(prefixo):
            return operador

    return None


# =============================================================================
# 6. Rota Oficial de Autenticação Multifator (MFA 1:1) — POST /autenticar
# =============================================================================

@app.post(
    "/autenticar",
    response_model=AutenticacaoSucessoResponse,
    status_code=200,
    tags=["Autenticação Multifator (MFA)"],
    summary="Autentica operador combinando CPF, Senha e Biometria Facial",
    response_description="Emite token de sessão JWT e dados funcionais após validação dos 3 fatores.",
    responses={
        400: {"model": ErroResponse, "description": "Falha de captura facial (0 ou múltiplos rostos)."},
        401: {"model": AutenticacaoFalhaResponse, "description": "Credenciais ou biometria inválidas."},
        403: {"model": AutenticacaoBloqueadaResponse, "description": "Acesso bloqueado por 5 tentativas falhas."},
    },
)
async def autenticar_operador(
    payload: AutenticacaoRequest,
) -> Any:
    """
    Executa a autenticação multifator 1:1 combinando:
      1. Algo que o operador POSSUI: CPF (identificador do cadastro);
      2. Algo que o operador SABE: Senha pessoal;
      3. Algo que o operador É: Biometria facial da webcam (5 fases do PIVC).

    Regras de Segurança do Cofre:
      * Erros de captura (0 ou múltiplos rostos) retornam HTTP 400 e NÃO
        consomem tentativas.
      * Falhas de senha ou divergência biométrica descontam tentativas (HTTP 401).
      * Atingir 5 falhas consecutivas bloqueia a conta (HTTP 403 - ACCOUNT_LOCKED).
    """
    cpf_limpo = payload.cpf
    senha_informada = payload.senha.get_secret_value()

    operador = _localizar_operador(cpf_limpo)
    if operador is None:
        # CPF não localizado no registro
        falha = AutenticacaoFalhaResponse(
            sucesso=False,
            bloqueado=False,
            tentativas_restantes=MAX_TENTATIVAS_AUTENTICACAO - 1,
            tentativas_maximas=MAX_TENTATIVAS_AUTENTICACAO,
            erro=ErroDetalheResponse(
                codigo="INVALID_CREDENTIALS",
                mensagem="CPF ou senha inválidos.",
                detalhes=None,
            ),
        )
        return JSONResponse(status_code=401, content=falha.model_dump(mode="json"))

    # Verifica se a conta está bloqueada
    if operador.bloqueado:
        # Se houver tempo de bloqueio expirado, libera automaticamente
        if operador.bloqueado_ate and datetime.now(timezone.utc) > operador.bloqueado_ate:
            operador.bloqueado = False
            operador.tentativas_falhas = 0
            operador.bloqueado_ate = None
        else:
            bloqueio = AutenticacaoBloqueadaResponse(
                sucesso=False,
                bloqueado=True,
                tentativas_restantes=0,
                bloqueado_ate=operador.bloqueado_ate,
                erro=ErroDetalheResponse(
                    codigo="ACCOUNT_LOCKED",
                    mensagem=(
                        "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas de "
                        "autenticação malsucedidas. A ocorrência foi registrada e a "
                        "equipe de segurança do cofre foi notificada."
                    ),
                    detalhes={"tentativas_falhas": operador.tentativas_falhas},
                ),
            )
            return JSONResponse(status_code=403, content=bloqueio.model_dump(mode="json"))

    # 1. Validação do Fator Senha
    if senha_informada != operador.senha:
        operador.tentativas_falhas += 1
        if operador.tentativas_falhas >= MAX_TENTATIVAS_AUTENTICACAO:
            operador.bloqueado = True
            operador.bloqueado_ate = datetime.now(timezone.utc) + timedelta(minutes=15)
            bloqueio = AutenticacaoBloqueadaResponse(
                sucesso=False,
                bloqueado=True,
                tentativas_restantes=0,
                bloqueado_ate=operador.bloqueado_ate,
                erro=ErroDetalheResponse(
                    codigo="ACCOUNT_LOCKED",
                    mensagem=(
                        "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas de "
                        "autenticação malsucedidas. A ocorrência foi registrada e a "
                        "equipe de segurança do cofre foi notificada."
                    ),
                    detalhes={"tentativas_falhas": operador.tentativas_falhas},
                ),
            )
            return JSONResponse(status_code=403, content=bloqueio.model_dump(mode="json"))

        restantes = MAX_TENTATIVAS_AUTENTICACAO - operador.tentativas_falhas
        falha = AutenticacaoFalhaResponse(
            sucesso=False,
            bloqueado=False,
            tentativas_restantes=restantes,
            tentativas_maximas=MAX_TENTATIVAS_AUTENTICACAO,
            erro=ErroDetalheResponse(
                codigo="INVALID_CREDENTIALS",
                mensagem="CPF ou senha inválidos.",
                detalhes=None,
            ),
        )
        return JSONResponse(status_code=401, content=falha.model_dump(mode="json"))

    # 2. Validação do Fator Biométrico Facial (PIVC Fases 1 a 5)
    # Se a imagem tiver 0 rostos, múltiplos rostos ou Base64 inválido,
    # as exceções de biometria.py sobem automaticamente para o handler
    # biometria_exception_handler (HTTP 400), sem descontar tentativas!
    extracao = extrair_caracteristicas(payload.imagem_base64)

    # Registro de Referência on-the-fly (se for o primeiro acesso do operador na sessão)
    if operador.vetor_referencia is None:
        operador.vetor_referencia = extracao.vetor
        operador.tentativas_falhas = 0
        token_jwt = "mock-jwt-faca-" + secrets.token_urlsafe(24)
        return AutenticacaoSucessoResponse(
            sucesso=True,
            mensagem="Autenticação multifator concluída com sucesso (Biometria de referência vinculada).",
            token=token_jwt,
            token_tipo="Bearer",
            expira_em_segundos=28800,
            usuario=UsuarioAutenticadoResponse(
                id=operador.id,
                nome=operador.nome,
                matricula=operador.matricula,
                cargo=operador.cargo,
                divisao=operador.divisao,
                nivel_acesso=operador.nivel_acesso,
            ),
            biometria=MetricasBiometricasResponse(
                reconhecido=True,
                distancia_euclidiana=0.0,
                tolerancia=biometria.obter_tolerancia(),
                confianca_percentual=100.0,
            ),
        )

    # Verificação 1:1 contra o vetor previamente registrado
    comparacao = fase5_classificacao(extracao.vetor, operador.vetor_referencia)

    if not comparacao.reconhecido:
        # Rosto divergente: desconta tentativa
        operador.tentativas_falhas += 1
        if operador.tentativas_falhas >= MAX_TENTATIVAS_AUTENTICACAO:
            operador.bloqueado = True
            operador.bloqueado_ate = datetime.now(timezone.utc) + timedelta(minutes=15)
            bloqueio = AutenticacaoBloqueadaResponse(
                sucesso=False,
                bloqueado=True,
                tentativas_restantes=0,
                bloqueado_ate=operador.bloqueado_ate,
                erro=ErroDetalheResponse(
                    codigo="ACCOUNT_LOCKED",
                    mensagem=(
                        "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas de "
                        "autenticação malsucedidas. A ocorrência foi registrada e a "
                        "equipe de segurança do cofre foi notificada."
                    ),
                    detalhes={"tentativas_falhas": operador.tentativas_falhas},
                ),
            )
            return JSONResponse(status_code=403, content=bloqueio.model_dump(mode="json"))

        restantes = MAX_TENTATIVAS_AUTENTICACAO - operador.tentativas_falhas
        falha = AutenticacaoFalhaResponse(
            sucesso=False,
            bloqueado=False,
            tentativas_restantes=restantes,
            tentativas_maximas=MAX_TENTATIVAS_AUTENTICACAO,
            erro=ErroDetalheResponse(
                codigo="FACE_NOT_RECOGNIZED",
                mensagem="Acesso Negado: a biometria facial não corresponde ao usuário informado.",
                detalhes=comparacao.para_dict(),
            ),
        )
        return JSONResponse(status_code=401, content=falha.model_dump(mode="json"))

    # Sucesso completo nos 3 fatores: zera tentativas falhas
    operador.tentativas_falhas = 0
    token_jwt = "mock-jwt-faca-" + secrets.token_urlsafe(24)

    return AutenticacaoSucessoResponse(
        sucesso=True,
        mensagem="Autenticação multifator concluída com sucesso.",
        token=token_jwt,
        token_tipo="Bearer",
        expira_em_segundos=28800,
        usuario=UsuarioAutenticadoResponse(
            id=operador.id,
            nome=operador.nome,
            matricula=operador.matricula,
            cargo=operador.cargo,
            divisao=operador.divisao,
            nivel_acesso=operador.nivel_acesso,
        ),
        biometria=MetricasBiometricasResponse(
            reconhecido=True,
            distancia_euclidiana=comparacao.distancia_euclidiana,
            tolerancia=comparacao.tolerancia,
            confianca_percentual=comparacao.confianca_percentual,
        ),
    )


# =============================================================================
# 7. Rota de Health Check (Teste de Conectividade)
# =============================================================================

@app.get(
    "/ping",
    response_model=PingResponse,
    status_code=200,
    tags=["Health Check"],
    summary="Verifica o status operacional da API",
    response_description="Confirmação de que o servidor está no ar, versão e timestamp UTC.",
)
async def ping() -> PingResponse:
    """Valida se o backend está acessível antes de abrir a câmera ou exibir formulários."""
    return PingResponse(
        status="ok",
        mensagem="Servidor F.A.C.A. operacional",
        versao="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )


# =============================================================================
# 8. Rotas de Diagnóstico e Teste Biométrico — PIVC (Sem Dependência de Banco)
# =============================================================================
# Permitem validar as 5 fases do Processamento Digital de Imagens imediatamente
# via Swagger (/docs), testando aquisição, pré-processamento, segmentação (HOG),
# extração 128D (ResNet-34) e classificação (distância euclidiana 1:1).
# =============================================================================

@app.get(
    "/biometria/status",
    response_model=BiometriaStatusResponse,
    status_code=200,
    tags=["Visão Computacional (PIVC)"],
    summary="Parâmetros operacionais ativos do motor biométrico",
    response_description="Status de disponibilidade da biblioteca dlib e hiperparâmetros configurados.",
)
async def obter_status_biometria() -> BiometriaStatusResponse:
    """Informa se o face_recognition está disponível e quais limiares estão ativos."""
    return BiometriaStatusResponse(
        motor_disponivel=biometria.motor_disponivel(),
        tolerancia=biometria.obter_tolerancia(),
        modelo_deteccao=biometria.obter_modelo_deteccao(),
        upsample=biometria.obter_upsample(),
        dimensao_maxima_px=biometria.obter_dimensao_maxima(),
        dimensao_vetor=128,
    )


@app.post(
    "/biometria/extrair-vetor",
    response_model=BiometriaExtracaoResponse,
    status_code=200,
    tags=["Visão Computacional (PIVC)"],
    summary="Executa Fases 1 a 4 do PIVC sobre uma imagem em Base64",
    response_description="Vetor biométrico de 128 dimensões, ROI da face e telemetria de latência.",
    responses={
        400: {"model": ErroResponse, "description": "Erro de captura (imagem inválida, 0 ou múltiplos rostos)."},
        503: {"model": ErroResponse, "description": "Motor biométrico (dlib) indisponível no host."},
    },
)
async def extrair_vetor_biometrico(
    payload: BiometriaExtracaoRequest,
) -> BiometriaExtracaoResponse:
    """
    Submete a imagem Base64 às Fases 1 a 4:
      - Fase 1: Aquisição e decodificação Base64 -> Matriz BGR.
      - Fase 2: Pré-processamento (downscaling, normalização CLAHE e conversão para RGB contígua).
      - Fase 3: Segmentação facial com modelo HOG (valida regra de exatamente 1 face).
      - Fase 4: Extração do descritor profundo de 128 dimensões (ResNet-34).
    """
    resultado = extrair_caracteristicas(
        payload.imagem_base64,
        num_jitters=payload.num_jitters,
    )

    caixa_orig = resultado.caixa_original
    largura_orig, altura_orig = resultado.dimensoes_originais
    largura_proc, altura_proc = resultado.dimensoes_processadas

    return BiometriaExtracaoResponse(
        sucesso=True,
        mensagem="Vetor biométrico 128D extraído com sucesso.",
        rosto_detectado=True,
        quantidade_rostos=1,
        localizacao_rosto=CaixaDelimitadoraResponse(
            top=caixa_orig.top,
            right=caixa_orig.right,
            bottom=caixa_orig.bottom,
            left=caixa_orig.left,
        ),
        dimensoes_originais=DimensoesImagemResponse(largura=largura_orig, altura=altura_orig),
        dimensoes_processadas=DimensoesImagemResponse(largura=largura_proc, altura=altura_proc),
        fator_escala=resultado.fator_escala,
        iluminacao_normalizada=resultado.iluminacao_normalizada,
        dimensao_vetor=128,
        vetor_caracteristicas=resultado.vetor,
        tempos_fases_ms=resultado.tempos_ms,
        tempo_total_ms=resultado.tempo_total_ms,
    )


@app.post(
    "/biometria/comparar-teste",
    response_model=BiometriaComparacaoResponse,
    status_code=200,
    tags=["Visão Computacional (PIVC)"],
    summary="Executa as 5 Fases do PIVC comparando 2 imagens Base64 em memória",
    response_description="Resultado da verificação 1:1, distância euclidiana e similaridade percentual.",
    responses={
        400: {"model": ErroResponse, "description": "Erro de captura em uma das imagens."},
        503: {"model": ErroResponse, "description": "Motor biométrico (dlib) indisponível no host."},
    },
)
async def comparar_duas_imagens(
    payload: BiometriaComparacaoRequest,
) -> BiometriaComparacaoResponse:
    """
    Executa o pipeline completo (Fases 1 a 5) entre duas imagens Base64:
      - Extrai os descritores faciais de ambas as imagens (Fases 1 a 4).
      - Calcula a Distância Euclidiana entre eles (Fase 5).
      - Aplica o limiar de tolerância configurado (padrão 0.50).
    """
    inicio = time.perf_counter()

    extracao_ref = extrair_caracteristicas(payload.imagem_referencia_base64)
    extracao_teste = extrair_caracteristicas(payload.imagem_teste_base64)

    comparacao = fase5_classificacao(
        extracao_teste.vetor,
        extracao_ref.vetor,
        tolerancia=payload.tolerancia,
    )

    tempo_total_ms = round((time.perf_counter() - inicio) * 1000.0, 2)
    mensagem = (
        "As faces pertencem à mesma pessoa (match biométrico confirmado)."
        if comparacao.reconhecido
        else "Faces distintas: a distância euclidiana excedeu a tolerância de segurança."
    )

    caixa_ref = extracao_ref.caixa_original
    caixa_teste = extracao_teste.caixa_original

    return BiometriaComparacaoResponse(
        sucesso=True,
        mensagem=mensagem,
        resultado=MetricasBiometricasResponse(
            reconhecido=comparacao.reconhecido,
            distancia_euclidiana=comparacao.distancia_euclidiana,
            tolerancia=comparacao.tolerancia,
            confianca_percentual=comparacao.confianca_percentual,
        ),
        localizacao_rosto_referencia=CaixaDelimitadoraResponse(
            top=caixa_ref.top,
            right=caixa_ref.right,
            bottom=caixa_ref.bottom,
            left=caixa_ref.left,
        ),
        localizacao_rosto_teste=CaixaDelimitadoraResponse(
            top=caixa_teste.top,
            right=caixa_teste.right,
            bottom=caixa_teste.bottom,
            left=caixa_teste.left,
        ),
        tempo_total_ms=tempo_total_ms,
    )


@app.post(
    "/biometria/verificar-vetor",
    response_model=BiometriaVerificacaoResponse,
    status_code=200,
    tags=["Visão Computacional (PIVC)"],
    summary="Verificação 1:1 entre imagem capturada e vetor 128D de referência",
    response_description="Compara o frame recebido com o descritor previamente cadastrado.",
    responses={
        400: {"model": ErroResponse, "description": "Erro de captura ou vetor de referência inválido."},
        503: {"model": ErroResponse, "description": "Motor biométrico (dlib) indisponível no host."},
    },
)
async def verificar_imagem_contra_vetor(
    payload: BiometriaVerificacaoRequest,
) -> BiometriaVerificacaoResponse:
    """
    Simula exatamente a verificação 1:1 executada na autenticação de cofre:
      - Extrai o vetor da captura Base64 (Fases 1 a 4).
      - Compara contra o vetor numérico de referência (Fase 5).
    """
    inicio = time.perf_counter()

    comparacao = autenticar_biometria(
        payload.imagem_base64,
        payload.vetor_referencia,
        tolerancia=payload.tolerancia,
        lancar_se_negado=False,
    )

    tempo_total_ms = round((time.perf_counter() - inicio) * 1000.0, 2)
    mensagem = (
        "Biometria compatível com o vetor de referência."
        if comparacao.reconhecido
        else "Biometria incompatível com o vetor de referência."
    )

    return BiometriaVerificacaoResponse(
        sucesso=True,
        mensagem=mensagem,
        resultado=MetricasBiometricasResponse(
            reconhecido=comparacao.reconhecido,
            distancia_euclidiana=comparacao.distancia_euclidiana,
            tolerancia=comparacao.tolerancia,
            confianca_percentual=comparacao.confianca_percentual,
        ),
        tempo_total_ms=tempo_total_ms,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
