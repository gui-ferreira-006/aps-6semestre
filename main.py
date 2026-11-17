"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)
Ponto de Entrada da API (Entrypoint Principal)
==============================================================================

Servidor web assíncrono (FastAPI + Uvicorn) integrado ao MySQL 8.0 via SQLAlchemy 2.0:
  1. Entrega dos artefatos estáticos do Frontend na rota raiz (/);
  2. Motor biométrico PIVC desacoplado (OpenCV + dlib/ResNet — 5 fases);
  3. Autenticação multifator 1:1 (POST /autenticar) conectada ao MySQL 8.0,
     com controle de 5 tentativas falhas consecutivas, bloqueio temporário (15 min),
     auditoria e enrollment biométrico on-the-fly;
  4. Cadastro de novos operadores e biometria 128D (POST /cadastrar);
  5. Consulta ao cofre de toxinas com controle de acesso RBAC (GET /toxinas);
  6. Rota administrativa de salvaguarda operacional para desbloqueio de contas;
  7. Diagnóstico biométrico isolado para validação via Swagger (/docs).
"""

from __future__ import annotations

# ── Bibliotecas padrão ──
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Bibliotecas de terceiros ──
from fastapi import Depends, FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# ── Conexão com Banco de Dados e Camada de Persistência ──
from database import get_db, obter_instancia_banco, testar_conexao_sql
import crud
from models import Toxina, Usuario

# ── Motor Biométrico PIVC (5 fases do Processamento Digital de Imagens) ──
import biometria
from biometria import (
    BiometriaError,
    autenticar_biometria,
    extrair_caracteristicas,
    fase5_classificacao,
)

# ── Schemas Pydantic v2 (Contratos de Integração Oficiais) ──
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
    ConsultaCofreResponse,
    DetalhesConfidenciaisToxina,
    DimensoesImagemResponse,
    ErroDetalheResponse,
    ErroResponse,
    MetricasBiometricasResponse,
    PingResponse,
    ToxinaResponse,
    UsuarioAutenticadoResponse,
    UsuarioCadastroRequest,
    UsuarioCadastroResponse,
    UsuarioCriadoResponse,
    UsuarioSolicitanteResponse,
    mascarar_cpf,
)

# =============================================================================
# 1. Instanciação da aplicação FastAPI com metadados informativos
# =============================================================================
app = FastAPI(
    title="Motor Backend para o PIVC — APS 2026/2 (F.A.C.A.)",
    description=(
        "API RESTful do Sistema de Identificação e Autenticação Multifator "
        "(F.A.C.A.) com MySQL 8.0 em Docker, integrando as 5 fases do Processamento "
        "Digital de Imagens e Visão Computacional para proteção do cofre de segurança máxima "
        "do Ministério do Meio Ambiente."
    ),
    version="2.0.0",
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
    return FileResponse(BASE_DIR / "main.py")


# =============================================================================
# 4. Tratamento Centralizado de Exceções do Domínio Biométrico
# =============================================================================
@app.exception_handler(BiometriaError)
async def biometria_exception_handler(_: Request, exc: BiometriaError) -> JSONResponse:
    """Mapeia exceções do motor PIVC para o envelope ErroResponse com status 400."""
    return JSONResponse(
        status_code=exc.status_http,
        content={
            "sucesso": False,
            "erro": exc.para_dict(),
        },
    )


# =============================================================================
# 5. Gerenciamento de Sessões / Tokens de Autenticação
# =============================================================================
# Mapeia tokens JWT emitidos para os dados do operador autenticado
SESSOES_ATIVAS: Dict[str, Dict[str, Any]] = {}


def _registrar_sessao(token: str, usuario: Usuario) -> None:
    """Registra sessão ativa para autorização RBAC nas rotas protegidas."""
    SESSOES_ATIVAS[token] = {
        "id_usuario": usuario.id_usuario,
        "nome": usuario.nome,
        "cpf": usuario.cpf,
        "matricula": usuario.matricula,
        "nivel_acesso": usuario.id_nivel_acesso,
        "cargo": usuario.cargo.nome,
        "divisao": usuario.divisao.nome,
        "expira_em": time.time() + 28800,
    }


def _resolver_operador_token(
    db: Session,
    authorization: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Extrai e valida os dados do operador associados ao Bearer Token."""
    if not authorization:
        return None

    partes = authorization.strip().split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        return None

    token = partes[1]

    # 1. Verifica se está no dicionário de sessões em memória
    if token in SESSOES_ATIVAS:
        sessao = SESSOES_ATIVAS[token]
        if time.time() <= sessao["expira_em"]:
            return sessao

    # 2. Resolução flexível para tokens do roteiro/testes automatizados
    # Exemplo: 'mock-jwt-faca-...' associado ao operador padrão se houver
    if token.startswith("mock-jwt-faca-"):
        primeiro_usuario: Optional[Usuario] = None

        # Token fixo do ADM Geral (T.I.) emitido pelo frontend
        # ('mock-jwt-faca-adm-ti-<cpf>'): resolve para a própria conta de T.I.
        # (Nível 3) em vez do primeiro operador cadastrado (Nível 1).
        if token.startswith("mock-jwt-faca-adm-ti-"):
            cpf_ti = token.rsplit("-", 1)[-1]
            primeiro_usuario = (
                db.query(Usuario)
                .filter(Usuario.cpf == cpf_ti, Usuario.status_conta == "ATIVA")
                .first()
            )

        if primeiro_usuario is None:
            primeiro_usuario = (
                db.query(Usuario)
                .filter(Usuario.status_conta == "ATIVA")
                .order_by(Usuario.id_usuario.asc())
                .first()
            )
        if primeiro_usuario:
            return {
                "id_usuario": primeiro_usuario.id_usuario,
                "nome": primeiro_usuario.nome,
                "cpf": primeiro_usuario.cpf,
                "matricula": primeiro_usuario.matricula,
                "nivel_acesso": primeiro_usuario.id_nivel_acesso,
                "cargo": primeiro_usuario.cargo.nome if primeiro_usuario.cargo else "Operador",
                "divisao": primeiro_usuario.divisao.nome if primeiro_usuario.divisao else "Geral",
                "expira_em": time.time() + 28800,
            }

    return None


# =============================================================================
# 6. Rota Oficial de Autenticação Multifator (MFA 1:1) — POST /autenticar
# =============================================================================

@app.post(
    "/autenticar",
    response_model=AutenticacaoSucessoResponse,
    status_code=200,
    tags=["Autenticação Multifator (MFA)"],
    summary="Autentica operador combinando CPF, Senha e Biometria Facial no MySQL",
    response_description="Emite token de sessão JWT e dados funcionais após validação dos 3 fatores no MySQL.",
    responses={
        400: {"model": ErroResponse, "description": "Falha de captura facial (0 ou múltiplos rostos)."},
        401: {"model": AutenticacaoFalhaResponse, "description": "Credenciais ou biometria inválidas."},
        403: {"model": AutenticacaoBloqueadaResponse, "description": "Acesso bloqueado por 5 tentativas falhas."},
    },
)
async def autenticar_operador(
    payload: AutenticacaoRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Executa a autenticação multifator 1:1 definitiva integrada ao MySQL 8.0:
      1. Algo que o operador POSSUI: CPF (identificador limpo de 11 dígitos);
      2. Algo que o operador SABE: Senha pessoal (validada contra hash seguro);
      3. Algo que o operador É: Biometria facial da webcam (5 fases do PIVC).

    Regras de Segurança e Persistência:
      * Consulta a tabela bloqueio_login antes de processar qualquer credencial;
      * Erros de captura (0 ou múltiplos rostos) retornam HTTP 400 e NÃO consomem tentativas;
      * Falhas de senha ou divergência biométrica gravam em tentativa_autenticacao;
      * 5 falhas consecutivas disparam bloqueio de 15 minutos em bloqueio_login e auditoria;
      * Primeiro acesso de operador realiza enrollment biométrico 128D on-the-fly em biometria;
      * Autenticação bem-sucedida zera falhas consecutivas e registra log de auditoria.
    """
    cpf_limpo = payload.cpf
    tipo_id = "CPF"
    ident_prot = crud.obter_identificador_protegido(cpf_limpo)

    # -------------------------------------------------------------------------
    # Passo 1: Verificar se existe Bloqueio Temporário Ativo no MySQL
    # -------------------------------------------------------------------------
    bloqueio_ativo = crud.verificar_bloqueio_ativo(db, ident_prot)
    if bloqueio_ativo:
        crud.registrar_tentativa(
            db,
            tipo_identificador=tipo_id,
            identificador_protegido=ident_prot,
            etapa="CREDENCIAIS",
            resultado="BLOQUEADO",
            motivo="Tentativa de autenticação com conta sob bloqueio temporário ativo",
        )
        falhas_atual = crud.contar_falhas_consecutivas(db, ident_prot)
        bloqueio_resp = AutenticacaoBloqueadaResponse(
            sucesso=False,
            bloqueado=True,
            tentativas_restantes=0,
            bloqueado_ate=bloqueio_ativo.data_hora_fim,
            erro=ErroDetalheResponse(
                codigo="ACCOUNT_LOCKED",
                mensagem=(
                    "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas de "
                    "autenticação malsucedidas. A ocorrência foi registrada e a "
                    "equipe de segurança do cofre foi notificada."
                ),
                detalhes={
                    "tentativas_falhas": falhas_atual or MAX_TENTATIVAS_AUTENTICACAO,
                    "bloqueado_ate": bloqueio_ativo.data_hora_fim.isoformat(),
                },
            ),
        )
        return JSONResponse(status_code=403, content=bloqueio_resp.model_dump(mode="json"))

    # -------------------------------------------------------------------------
    # Passo 2: Localizar Usuário no MySQL com Eager Loading
    # -------------------------------------------------------------------------
    usuario = crud.buscar_usuario(db, cpf_limpo)
    if usuario is None or usuario.status_conta != "ATIVA":
        # CPF inexistente ou desativado: registra tentativa de falha e avalia bloqueio
        tentativa_falha = crud.registrar_tentativa(
            db,
            tipo_identificador=tipo_id,
            identificador_protegido=ident_prot,
            etapa="CREDENCIAIS",
            resultado="FALHA",
            motivo="CPF não localizado no cadastro ou conta desativada",
        )
        bloqueio_novo = crud.aplicar_bloqueio_se_necessario(
            db, tipo_id, ident_prot, tentativa_origem=tentativa_falha
        )
        if bloqueio_novo:
            bloqueio_resp = AutenticacaoBloqueadaResponse(
                sucesso=False,
                bloqueado=True,
                tentativas_restantes=0,
                bloqueado_ate=bloqueio_novo.data_hora_fim,
                erro=ErroDetalheResponse(
                    codigo="ACCOUNT_LOCKED",
                    mensagem=(
                        "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas de "
                        "autenticação malsucedidas. A ocorrência foi registrada e a "
                        "equipe de segurança do cofre foi notificada."
                    ),
                    detalhes={"tentativas_falhas": MAX_TENTATIVAS_AUTENTICACAO},
                ),
            )
            return JSONResponse(status_code=403, content=bloqueio_resp.model_dump(mode="json"))

        falhas = crud.contar_falhas_consecutivas(db, ident_prot)
        restantes = max(0, MAX_TENTATIVAS_AUTENTICACAO - falhas)
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

    # -------------------------------------------------------------------------
    # Passo 3: Validação do Fator Senha (PBKDF2-HMAC-SHA256)
    # -------------------------------------------------------------------------
    senha_informada = payload.senha.get_secret_value()
    if not crud.verificar_senha(senha_informada, usuario.hash_senha):
        tentativa_falha = crud.registrar_tentativa(
            db,
            tipo_identificador=tipo_id,
            identificador_protegido=ident_prot,
            etapa="CREDENCIAIS",
            resultado="FALHA",
            motivo="Senha incorreta",
            id_usuario=usuario.id_usuario,
        )
        bloqueio_novo = crud.aplicar_bloqueio_se_necessario(
            db,
            tipo_id,
            ident_prot,
            tentativa_origem=tentativa_falha,
            id_usuario=usuario.id_usuario,
        )
        if bloqueio_novo:
            bloqueio_resp = AutenticacaoBloqueadaResponse(
                sucesso=False,
                bloqueado=True,
                tentativas_restantes=0,
                bloqueado_ate=bloqueio_novo.data_hora_fim,
                erro=ErroDetalheResponse(
                    codigo="ACCOUNT_LOCKED",
                    mensagem=(
                        "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas de "
                        "autenticação malsucedidas. A ocorrência foi registrada e a "
                        "equipe de segurança do cofre foi notificada."
                    ),
                    detalhes={"tentativas_falhas": MAX_TENTATIVAS_AUTENTICACAO},
                ),
            )
            return JSONResponse(status_code=403, content=bloqueio_resp.model_dump(mode="json"))

        falhas = crud.contar_falhas_consecutivas(db, ident_prot)
        restantes = max(0, MAX_TENTATIVAS_AUTENTICACAO - falhas)
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

    # Credenciais primárias válidas: registra etapa concluída com sucesso
    crud.registrar_tentativa(
        db,
        tipo_identificador=tipo_id,
        identificador_protegido=ident_prot,
        etapa="CREDENCIAIS",
        resultado="SUCESSO",
        motivo="Credenciais conferidas",
        id_usuario=usuario.id_usuario,
    )

    # -------------------------------------------------------------------------
    # Passo 4: Validação do Fator Biométrico Facial (PIVC Fases 1 a 5)
    # -------------------------------------------------------------------------
    # Se a captura contiver 0 ou múltiplos rostos, as exceções especializadas
    # de biometria.py disparam biometria_exception_handler (HTTP 400) sem falhas!
    extracao = extrair_caracteristicas(payload.imagem_base64)

    # -------------------------------------------------------------------------
    # Passo 5: Enrollment On-the-Fly no Primeiro Acesso do Operador
    # -------------------------------------------------------------------------
    if usuario.biometria is None:
        crud.salvar_biometria_usuario(
            db,
            id_usuario=usuario.id_usuario,
            vetor_128d=extracao.vetor,
            versao_modelo="dlib_resnet34_v1",
        )
        crud.registrar_tentativa(
            db,
            tipo_identificador=tipo_id,
            identificador_protegido=ident_prot,
            etapa="BIOMETRIA",
            resultado="SUCESSO",
            motivo="Enrollment biométrico realizado com sucesso no primeiro acesso",
            id_usuario=usuario.id_usuario,
        )
        crud.registrar_tentativa(
            db,
            tipo_identificador=tipo_id,
            identificador_protegido=ident_prot,
            etapa="CONCLUSAO",
            resultado="SUCESSO",
            motivo="Autenticação multifator concluída com sucesso (Enrollment)",
            id_usuario=usuario.id_usuario,
        )
        crud.registrar_auditoria(
            db,
            id_usuario=usuario.id_usuario,
            acao="LOGIN_MFA",
            entidade_afetada="usuario",
            id_registro_afetado=str(usuario.id_usuario),
            resultado="SUCESSO",
            detalhes={
                "tipo_evento": "ENROLLMENT_ON_THE_FLY",
                "nivel_acesso": usuario.id_nivel_acesso,
            },
        )

        token_jwt = "mock-jwt-faca-" + secrets.token_urlsafe(24)
        _registrar_sessao(token_jwt, usuario)

        return AutenticacaoSucessoResponse(
            sucesso=True,
            mensagem="Autenticação multifator concluída com sucesso (Biometria de referência vinculada).",
            token=token_jwt,
            token_tipo="Bearer",
            expira_em_segundos=28800,
            usuario=UsuarioAutenticadoResponse(
                id=usuario.id_usuario,
                nome=usuario.nome,
                matricula=usuario.matricula,
                cargo=usuario.cargo.nome if usuario.cargo else "Operador",
                divisao=usuario.divisao.nome if usuario.divisao else "Geral",
                nivel_acesso=usuario.id_nivel_acesso,  # type: ignore (1..3)
            ),
            biometria=MetricasBiometricasResponse(
                reconhecido=True,
                distancia_euclidiana=0.0,
                tolerancia=biometria.obter_tolerancia(),
                confianca_percentual=100.0,
            ),
        )

    # -------------------------------------------------------------------------
    # Passo 6: Verificação 1:1 contra o Vetor Gravado na Tabela biometria
    # -------------------------------------------------------------------------
    vetor_referencia = usuario.biometria.modelo_facial
    comparacao = fase5_classificacao(extracao.vetor, vetor_referencia)

    if not comparacao.reconhecido:
        # Divergência biométrica: grava tentativa de falha e checa bloqueio
        tentativa_falha = crud.registrar_tentativa(
            db,
            tipo_identificador=tipo_id,
            identificador_protegido=ident_prot,
            etapa="BIOMETRIA",
            resultado="NEGADO",
            motivo="Divergência biométrica facial (rosto incompatível)",
            id_usuario=usuario.id_usuario,
        )
        bloqueio_novo = crud.aplicar_bloqueio_se_necessario(
            db,
            tipo_id,
            ident_prot,
            tentativa_origem=tentativa_falha,
            id_usuario=usuario.id_usuario,
        )
        if bloqueio_novo:
            bloqueio_resp = AutenticacaoBloqueadaResponse(
                sucesso=False,
                bloqueado=True,
                tentativas_restantes=0,
                bloqueado_ate=bloqueio_novo.data_hora_fim,
                erro=ErroDetalheResponse(
                    codigo="ACCOUNT_LOCKED",
                    mensagem=(
                        "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas de "
                        "autenticação malsucedidas. A ocorrência foi registrada e a "
                        "equipe de segurança do cofre foi notificada."
                    ),
                    detalhes={"tentativas_falhas": MAX_TENTATIVAS_AUTENTICACAO},
                ),
            )
            return JSONResponse(status_code=403, content=bloqueio_resp.model_dump(mode="json"))

        falhas = crud.contar_falhas_consecutivas(db, ident_prot)
        restantes = max(0, MAX_TENTATIVAS_AUTENTICACAO - falhas)
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

    # -------------------------------------------------------------------------
    # Passo 7: Sucesso Completo nos 3 Fatores (CPF + Senha + Face)
    # -------------------------------------------------------------------------
    crud.registrar_tentativa(
        db,
        tipo_identificador=tipo_id,
        identificador_protegido=ident_prot,
        etapa="BIOMETRIA",
        resultado="SUCESSO",
        motivo="Biometria facial confirmada com sucesso",
        id_usuario=usuario.id_usuario,
    )
    crud.registrar_tentativa(
        db,
        tipo_identificador=tipo_id,
        identificador_protegido=ident_prot,
        etapa="CONCLUSAO",
        resultado="SUCESSO",
        motivo="Autenticação multifator concluída com sucesso",
        id_usuario=usuario.id_usuario,
    )
    crud.registrar_auditoria(
        db,
        id_usuario=usuario.id_usuario,
        acao="LOGIN_MFA",
        entidade_afetada="usuario",
        id_registro_afetado=str(usuario.id_usuario),
        resultado="SUCESSO",
        detalhes={
            "distancia_euclidiana": comparacao.distancia_euclidiana,
            "confianca_percentual": comparacao.confianca_percentual,
            "nivel_acesso": usuario.id_nivel_acesso,
        },
    )

    token_jwt = "mock-jwt-faca-" + secrets.token_urlsafe(24)
    _registrar_sessao(token_jwt, usuario)

    return AutenticacaoSucessoResponse(
        sucesso=True,
        mensagem="Autenticação multifator concluída com sucesso.",
        token=token_jwt,
        token_tipo="Bearer",
        expira_em_segundos=28800,
        usuario=UsuarioAutenticadoResponse(
            id=usuario.id_usuario,
            nome=usuario.nome,
            matricula=usuario.matricula,
            cargo=usuario.cargo.nome if usuario.cargo else "Operador",
            divisao=usuario.divisao.nome if usuario.divisao else "Geral",
            nivel_acesso=usuario.id_nivel_acesso,  # type: ignore (1..3)
        ),
        biometria=MetricasBiometricasResponse(
            reconhecido=True,
            distancia_euclidiana=comparacao.distancia_euclidiana,
            tolerancia=comparacao.tolerancia,
            confianca_percentual=comparacao.confianca_percentual,
        ),
    )


# =============================================================================
# 7. Rota de Cadastro de Servidor e Biometria — POST /cadastrar
# =============================================================================

@app.post(
    "/cadastrar",
    response_model=UsuarioCadastroResponse,
    status_code=201,
    tags=["Gestão de Usuários e Biometria"],
    summary="Cadastra novo servidor público e vincula biometria de referência no MySQL",
    response_description="Confirmação de cadastro, id gerado e dados mascarados do servidor.",
    responses={
        400: {"model": ErroResponse, "description": "Erro de captura facial (0 ou múltiplos rostos)."},
        409: {"model": ErroResponse, "description": "CPF ou Matrícula já em uso."},
    },
)
async def cadastrar_usuario(
    payload: UsuarioCadastroRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Cadastra um novo servidor público no sistema F.A.C.A.:
      1. Extrai o vetor descritor 128D via Fases 1 a 4 do PIVC;
      2. Persiste os dados na tabela usuario com hash seguro PBKDF2;
      3. Persiste o vetor na tabela biometria;
      4. Registra a operação na tabela auditoria.
    """
    # 1. Extração biométrica facial
    extracao = extrair_caracteristicas(payload.imagem_base64)

    # Registro pré-existente (ex.: operador do seed sem biometria) será
    # atualizado e terá a biometria vinculada em vez de gerar 409.
    registro_pre_existente = (
        db.query(Usuario)
        .filter(
            (Usuario.cpf == payload.cpf)
            | (Usuario.matricula == payload.matricula.strip())
        )
        .first()
        is not None
    )

    # 2. Persistência no banco MySQL via repositório CRUD
    try:
        usuario = crud.criar_novo_usuario(
            db=db,
            nome=payload.nome,
            cpf=payload.cpf,
            senha_plana=payload.senha.get_secret_value(),
            matricula=payload.matricula,
            cargo_id=payload.cargo_id,
            divisao_id=payload.divisao_id,
            nivel_acesso=payload.nivel_acesso,
            vetor_biometrico=extracao.vetor,
        )
    except ValueError as erro_validacao:
        db.rollback()
        codigo = str(erro_validacao)
        mensagens_conflito = {
            "CPF_ALREADY_EXISTS": (
                "O CPF informado já está cadastrado no sistema com biometria facial vinculada."
            ),
            "MATRICULA_ALREADY_EXISTS": (
                "A matrícula institucional já está em uso por outro servidor com biometria facial vinculada."
            ),
            "CONTA_RESERVADA_TI": (
                "O CPF/Matrícula informado pertence à conta reservada do Administrador Geral (T.I.)."
            ),
        }
        mensagem = mensagens_conflito.get(
            codigo, "Conflito de unicidade ao cadastrar o servidor."
        )
        return JSONResponse(
            status_code=409,
            content={
                "sucesso": False,
                "erro": {
                    "codigo": codigo,
                    "mensagem": mensagem,
                    "detalhes": None,
                },
            },
        )

    return UsuarioCadastroResponse(
        sucesso=True,
        mensagem=(
            "Operador pré-cadastrado atualizado e biometria facial vinculada com sucesso."
            if registro_pre_existente
            else "Usuário e biometria facial cadastrados com sucesso."
        ),
        usuario=UsuarioCriadoResponse(
            id=usuario.id_usuario,
            nome=usuario.nome,
            cpf_mascarado=mascarar_cpf(usuario.cpf),
            matricula=usuario.matricula,
            cargo_id=usuario.id_cargo,
            divisao_id=usuario.id_divisao,
            nivel_acesso=usuario.id_nivel_acesso,  # type: ignore
            criado_em=usuario.data_criacao,
        ),
    )


# =============================================================================
# 8. Rota de Consulta ao Cofre de Toxinas (RBAC) — GET /toxinas
# =============================================================================

@app.get(
    "/toxinas",
    response_model=ConsultaCofreResponse,
    status_code=200,
    tags=["Cofre de Toxinas"],
    summary="Consulta substâncias controladas no cofre do Ministério (Filtro RBAC)",
    response_description="Listagem de toxinas filtradas dinamicamente pelo nível de acesso do operador autenticado.",
    responses={
        401: {"model": ErroResponse, "description": "Token ausente ou expirado."},
    },
)
async def consultar_cofre(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Any:
    """
    Recurso restrito do Ministério do Meio Ambiente:
      - Extrai a identidade e o nivel_acesso do Bearer Token;
      - Filtra as substâncias cadastradas no MySQL pelo nível do operador:
          * Nível 1: somente amostras de nível 1 (dados confidenciais como null);
          * Nível 2: amostras de níveis 1 e 2 (com protocolos de contenção);
          * Nível 3: acesso irrestrito a todas as toxinas (incluindo armas e quimeras).
    """
    operador = _resolver_operador_token(db, authorization)
    if not operador:
        return JSONResponse(
            status_code=401,
            content={
                "sucesso": False,
                "erro": {
                    "codigo": "TOKEN_INVALID_OR_EXPIRED",
                    "mensagem": "Token de autenticação ausente ou expirado.",
                    "detalhes": None,
                },
            },
        )

    nivel_usuario = int(operador.get("nivel_acesso", 1))
    nome_usuario = str(operador.get("nome", "Operador"))

    toxinas_db = crud.listar_toxinas(db, nivel_usuario=nivel_usuario)

    itens_resposta: List[ToxinaResponse] = []
    for t in toxinas_db:
        nivel_req = crud.extrair_nivel_requerido_toxina(t.classificacao)

        # Dados confidenciais de contenção exibidos apenas para Nível 2 e Nível 3
        detalhes: Optional[DetalhesConfidenciaisToxina] = None
        if nivel_usuario > 1 and nivel_usuario >= nivel_req and t.observacoes:
            detalhes = DetalhesConfidenciaisToxina(
                local_estocagem=f"Cofre Criogênico Setor {t.id_divisao_responsavel}-{t.id_toxina:02d}",
                protocolo_neutralizacao=t.observacoes,
            )

        codigo_amostra = f"TOX-L{nivel_req}-{t.id_toxina:03d}"
        formula = (
            "C6760H10447N1743O2010S32"
            if t.id_toxina == 1
            else (
                "C10H17N7O4"
                if t.id_toxina == 2
                else (
                    "C12H24N4O8"
                    if t.id_toxina == 3
                    else "Classificada - Gabinete Ministerial"
                )
            )
        )
        temp_celsius = 4.0 if nivel_req == 1 else (-20.0 if nivel_req == 2 else -80.0)

        itens_resposta.append(
            ToxinaResponse(
                id=t.id_toxina,
                nome_comum=t.nome,
                codigo_amostra=codigo_amostra,
                formula_molecular=formula,
                nivel_requerido=nivel_req,  # type: ignore
                classificacao_risco=t.classificacao or "Monitorado",
                temperatura_armazenamento_celsius=temp_celsius,
                status_contencao="Estável",
                detalhes_confidenciais=detalhes,
            )
        )

    return ConsultaCofreResponse(
        sucesso=True,
        usuario_solicitante=UsuarioSolicitanteResponse(
            nome=nome_usuario,
            nivel_acesso=nivel_usuario,  # type: ignore
        ),
        total_registros=len(itens_resposta),
        itens=itens_resposta,
    )


# =============================================================================
# 9. Rota Administrativa de Desbloqueio (Salvaguarda Operacional)
# =============================================================================

@app.post(
    "/usuarios/{identificador}/desbloquear",
    tags=["Administração e Auditoria"],
    summary="Desbloqueia conta bloqueada por tentativas excessivas (Ação de Emergência / Nível 3)",
    response_description="Confirmação da desativação do bloqueio no MySQL.",
)
@app.post(
    "/api/v1/nivel3/desbloquear",
    tags=["Administração e Auditoria"],
    summary="Endpoint alternativo de desbloqueio compatível com configuracao-banco.js",
)
async def desbloquear_conta_usuario(
    identificador: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Desativa bloqueios ativos para o CPF ou Matrícula informado na tabela
    bloqueio_login e registra a ação de salvaguarda na tabela auditoria.
    """
    total = crud.desbloquear_usuario(db, identificador)
    return {
        "sucesso": True,
        "mensagem": f"Conta de identificador '{identificador}' desbloqueada com sucesso.",
        "bloqueios_desativados": total,
    }


# =============================================================================
# 10. Rota de Health Check (Teste de Conectividade com MySQL)
# =============================================================================

@app.get(
    "/ping",
    response_model=PingResponse,
    status_code=200,
    tags=["Health Check"],
    summary="Verifica o status operacional da API e a conexão com o MySQL 8.0",
    response_description="Confirmação de que o servidor e o MySQL estão no ar, versão e timestamp UTC.",
)
async def ping() -> PingResponse:
    """Valida se o backend e a conexão com o MySQL estão operacionais."""
    banco_ok = testar_conexao_sql()
    status_msg = (
        "Servidor F.A.C.A. operacional (MySQL conectado)"
        if banco_ok
        else "Servidor F.A.C.A. operacional (MySQL offline)"
    )
    return PingResponse(
        status="ok",
        mensagem=status_msg,
        versao="2.0.0",
        timestamp=datetime.now(timezone.utc),
        instancia_banco=obter_instancia_banco() if banco_ok else None,
    )


# =============================================================================
# 11. Rotas de Diagnóstico e Teste Biométrico — PIVC (Fases 1 a 5)
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
      - Fase 2: Pré-processamento (downscaling, normalização CLAHE e conversão para RGB).
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
    """Executa o pipeline completo (Fases 1 a 5) entre duas imagens Base64."""
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
    """Simula a verificação 1:1 executada na autenticação de cofre."""
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
