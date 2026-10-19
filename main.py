"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)
Ponto de Entrada da API (Entrypoint)
==============================================================================

Servidor web assíncrono (FastAPI + Uvicorn) que orquestra os contratos de
dados Pydantic v2 e o motor biométrico PIVC desacoplado (OpenCV + dlib/ResNet).
"""

from __future__ import annotations

# ── Bibliotecas padrão ──
import time
from datetime import datetime, timezone

# ── Bibliotecas de terceiros ──
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
    BiometriaComparacaoRequest,
    BiometriaComparacaoResponse,
    BiometriaExtracaoRequest,
    BiometriaExtracaoResponse,
    BiometriaStatusResponse,
    BiometriaVerificacaoRequest,
    BiometriaVerificacaoResponse,
    CaixaDelimitadoraResponse,
    DimensoesImagemResponse,
    ErroResponse,
    MetricasBiometricasResponse,
    PingResponse,
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
# 3. Tratamento Centralizado de Exceções do Domínio Biométrico
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
# 4. Rota de Health Check (Teste de Conectividade)
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
# 5. Rotas de Diagnóstico e Teste Biométrico — PIVC (Sem Dependência de Banco)
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
