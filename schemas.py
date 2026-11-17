"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)

Camada de Schemas Pydantic v2
==============================================================================

Este módulo define todos os modelos de validação e serialização de dados
(request bodies e response bodies) utilizados pelos endpoints da API F.A.C.A.

Cada schema corresponde fielmente ao contrato de integração documentado em
API.md, garantindo que:
  - Toda requisição recebida seja estritamente validada antes de atingir
    a lógica de negócio.
  - Toda resposta devolvida siga a estrutura JSON exata esperada pelo
    Frontend.
  - A documentação interativa (/docs e /redoc) apresente exemplos
    realistas e autoexplicativos.

Organização:
  1. Imports, Configurações Base e Tipos Reutilizáveis (CPF, Base64)
  2. Schemas do Health Check (/ping)
  3. Schemas de Autenticação Multifator — CPF + Senha + Face (/autenticar)
  4. Schemas de Cadastro de Usuário (/cadastrar)
  5. Schemas do Cofre de Toxinas (/toxinas)
  6. Schemas Genéricos de Erro
  7. Schemas de Falha (401) e Bloqueio (403) da Autenticação MFA
  8. Schemas do Diagnóstico Biométrico Isolado — PIVC (/biometria/*)
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Any, Dict, List, Literal, Optional, cast

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, SecretStr


# =============================================================================
# 1. CONFIGURAÇÃO BASE REUTILIZÁVEL
# =============================================================================

class _SchemaBase(BaseModel):
    """
    Classe-base interna que aplica convenções globais a todos os schemas
    do projeto F.A.C.A.:
      - Serialização por alias desativada (usamos nomes snake_case).
      - Campos extras são proibidos para evitar payloads inesperados.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )


# ── Constantes de validação compartilhadas ──

#: Número máximo de tentativas de autenticação antes do bloqueio (Roteiro v2).
MAX_TENTATIVAS_AUTENTICACAO: int = 5

#: Teto de caracteres aceitos em campos Base64 (~10 MB ≈ 7,5 MB binários).
_TAMANHO_MAXIMO_BASE64: int = 10 * 1024 * 1024

#: Cabeçalho Data URL gerado por canvas.toDataURL() (ex: data:image/jpeg;base64,).
_REGEX_DATA_URL = re.compile(r"^data:[^,;]*(?:;[^,;]+)*;base64,", re.IGNORECASE)
_REGEX_ESPACOS = re.compile(r"\s+")
_REGEX_NAO_DIGITOS = re.compile(r"\D")


def _normalizar_imagem_base64(valor: str) -> str:
    """
    Normaliza o campo de imagem: remove automaticamente um eventual prefixo
    Data URL (``data:image/...;base64,``) e espaços/quebras de linha.

    Política do Roteiro v2: o Frontend DEVE preferir o Base64 puro, mas o
    backend é tolerante ao cabeçalho para reduzir atritos de integração
    (o motor ``biometria.py`` aplica a mesma sanitização como defesa em
    profundidade).
    """
    texto = _REGEX_ESPACOS.sub("", _REGEX_DATA_URL.sub("", valor.strip(), count=1))
    if not texto:
        raise ValueError("A imagem Base64 não pode ser vazia.")
    return texto


def _normalizar_cpf(valor: str) -> str:
    """
    Limpa a formatação do CPF (pontos, hífen, espaços) e valida o formato
    de 11 dígitos. Ex.: ``"123.456.789-09"`` → ``"12345678909"``.

    Observação: os dígitos verificadores NÃO são validados nesta etapa para
    permitir massas de teste fictícias na PoC acadêmica.
    """
    digitos = _REGEX_NAO_DIGITOS.sub("", valor)
    if len(digitos) != 11:
        raise ValueError(
            "O CPF deve conter exatamente 11 dígitos (com ou sem máscara)."
        )
    return digitos


def mascarar_cpf(cpf: str) -> str:
    """
    Mascara o CPF para exibição/log em conformidade com a LGPD.
    Ex.: ``"12345678909"`` → ``"***.456.789-**"``.
    """
    digitos = _REGEX_NAO_DIGITOS.sub("", cpf)
    if len(digitos) != 11:
        return "***.***.***-**"
    return f"***.{digitos[3:6]}.{digitos[6:9]}-**"


# ── Tipos anotados reutilizáveis (validação declarativa Pydantic v2) ──

ImagemBase64Str = Annotated[str, AfterValidator(_normalizar_imagem_base64)]
"""String Base64 de imagem JPEG/PNG (Data URL tolerado e removido)."""

CpfStr = Annotated[str, AfterValidator(_normalizar_cpf)]
"""CPF aceito com ou sem máscara; armazenado apenas com os 11 dígitos."""

# Vetor de exemplo (128 floats) usado na documentação interativa.
_EXEMPLO_VETOR_128D: List[float] = [
    round(((i * 37) % 101 - 50) / 400.0, 4) for i in range(128)
]


# =============================================================================
# 2. SCHEMAS DO HEALTH CHECK — GET /ping
# =============================================================================
# Modelo de resposta para a rota de teste de conectividade. Permite que o
# Frontend valide rapidamente se o backend está operacional antes de ativar
# a webcam ou exibir formulários.
# =============================================================================

class PingResponse(_SchemaBase):
    """Resposta do endpoint de Health Check (GET /ping)."""

    status: str = Field(
        ...,
        description="Indicador textual do estado do servidor (ex: 'ok').",
        examples=["ok"],
    )
    mensagem: str = Field(
        ...,
        description="Mensagem descritiva confirmando a disponibilidade da API.",
        examples=["Servidor F.A.C.A. operacional"],
    )
    versao: str = Field(
        ...,
        description="Versão semântica corrente da API (SemVer).",
        examples=["1.0.0"],
    )
    timestamp: datetime = Field(
        ...,
        description="Instante UTC em que a resposta foi gerada pelo servidor.",
        examples=["2026-09-06T20:50:00Z"],
    )
    instancia_banco: Optional[str] = Field(
        default=None,
        description=(
            "Identificador do ciclo de vida do banco aps_biometria (instante de "
            "criação do schema). Muda a cada recriação do volume Docker; o "
            "frontend o utiliza para descartar caches locais de instâncias antigas."
        ),
        examples=["2026-11-17T13:50:00"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "mensagem": "Servidor F.A.C.A. operacional",
                "versao": "1.0.0",
                "timestamp": "2026-09-06T20:50:00Z",
                "instancia_banco": "2026-11-17T13:50:00",
            }
        }
    )


# =============================================================================
# 3. SCHEMAS DE AUTENTICAÇÃO MULTIFATOR (MFA 1:1) — POST /autenticar
# =============================================================================
# Roteiro Oficial v2 (index.html / principal.js): a autenticação combina
# TRÊS fatores em uma única requisição:
#   1. Algo que o operador SABE   → senha
#   2. Algo que o operador POSSUI → CPF (identificador do cadastro)
#   3. Algo que o operador É      → biometria facial (frame da webcam)
#
# O CPF localiza o vetor biométrico de referência no banco, permitindo uma
# VERIFICAÇÃO 1:1 (muito mais segura e rápida que a identificação 1:N). Cada
# falha (senha ou face) consome uma tentativa; após 5 falhas consecutivas a
# conta é bloqueada (HTTP 403 — ver Seção 7).
# =============================================================================

class AutenticacaoRequest(_SchemaBase):
    """
    Payload de entrada do endpoint de autenticação multifator (POST /autenticar).

    * ``cpf``: aceito com ou sem máscara — é normalizado para 11 dígitos.
    * ``senha``: tratada como ``SecretStr`` (nunca aparece em logs/repr).
    * ``imagem_base64``: frame JPEG/PNG da webcam. O Base64 puro é o formato
      recomendado; um eventual prefixo ``data:image/...;base64,`` é removido
      automaticamente.
    """

    cpf: CpfStr = Field(
        ...,
        min_length=11,
        max_length=14,
        description=(
            "CPF do servidor (identificador do usuário), com ou sem máscara. "
            "Normalizado para 11 dígitos."
        ),
        examples=["123.456.789-09"],
    )
    senha: SecretStr = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Senha pessoal do servidor (fator de conhecimento).",
        examples=["Faca@2026"],
    )
    imagem_base64: ImagemBase64Str = Field(
        ...,
        min_length=1,
        max_length=_TAMANHO_MAXIMO_BASE64,
        description=(
            "Captura facial da webcam em Base64 (JPEG ou PNG). Recomendado "
            "enviar Base64 puro; o prefixo Data URL é tolerado e removido."
        ),
        examples=["/9j/4AAQSkZJRgABAQEASABIAAD..."],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cpf": "123.456.789-09",
                "senha": "Faca@2026",
                "imagem_base64": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP...",
            }
        }
    )


# ── Sub-modelo: métricas da Fase 5 (classificação) para telemetria ──

class MetricasBiometricasResponse(_SchemaBase):
    """
    Métricas da verificação biométrica 1:1 (Fase 5 do PIVC). Reutilizado na
    resposta de sucesso, nos detalhes de falha e nas rotas de diagnóstico.
    """

    reconhecido: bool = Field(
        ...,
        description="True se distância_euclidiana <= tolerância (match).",
        examples=[True],
    )
    distancia_euclidiana: float = Field(
        ...,
        ge=0,
        description=(
            "Distância Euclidiana (norma L2) entre o vetor 128D capturado e o "
            "de referência, arredondada para 4 casas decimais."
        ),
        examples=[0.3412],
    )
    tolerancia: float = Field(
        ...,
        gt=0,
        le=1,
        description="Limiar de decisão aplicado (FACE_RECOGNITION_TOLERANCE).",
        examples=[0.5],
    )
    confianca_percentual: float = Field(
        ...,
        ge=0,
        le=100,
        description=(
            "Similaridade percentual derivada da distância (apenas "
            "telemetria; 50% corresponde exatamente ao limiar)."
        ),
        examples=[93.87],
    )


# ── Sub-modelo: dados do usuário identificado após match biométrico ──

class UsuarioAutenticadoResponse(_SchemaBase):
    """
    Dados funcionais do servidor público identificado pelo motor biométrico.
    Retornado como objeto aninhado dentro de ``AutenticacaoSucessoResponse``.
    """

    id: int = Field(
        ...,
        description="Identificador único (PK) do usuário no banco de dados.",
        examples=[1],
    )
    nome: str = Field(
        ...,
        description="Nome completo do servidor público.",
        examples=["Guilherme Ferreira"],
    )
    matricula: str = Field(
        ...,
        description="Matrícula funcional / RA institucional do servidor.",
        examples=["G9483B2"],
    )
    cargo: str = Field(
        ...,
        description="Cargo ou ocupação funcional do servidor no Ministério.",
        examples=["Engenheiro de Bioproteção"],
    )
    divisao: str = Field(
        ...,
        description="Divisão / departamento governamental ao qual pertence.",
        examples=["Divisão de Contenção Microbiológica"],
    )
    nivel_acesso: Literal[1, 2, 3] = Field(
        ...,
        description=(
            "Nível de acesso RBAC do servidor: "
            "1 (Operacional), 2 (Diretoria), 3 (Ministerial / Irrestrito)."
        ),
        examples=[1],
    )


# ── Resposta de sucesso completa ──

class AutenticacaoSucessoResponse(_SchemaBase):
    """
    Resposta retornada quando os TRÊS fatores (CPF, senha e face) são
    validados com sucesso (HTTP 200). Contém o token JWT, metadados de
    expiração, os dados funcionais do usuário e, opcionalmente, as métricas
    da verificação biométrica para telemetria.
    """

    sucesso: Literal[True] = Field(
        default=True,
        description="Indicador booleano de sucesso da operação.",
    )
    mensagem: str = Field(
        ...,
        description="Mensagem explicativa do resultado da autenticação.",
        examples=["Autenticação multifator concluída com sucesso."],
    )
    token: str = Field(
        ...,
        description="Token JWT assinado para autenticação nas rotas protegidas.",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxIiwibm9tZSI6Ikd1aWxoZXJtZSIsIm5pdmVsIjoxfQ."
            "mock_signature_hash"
        ],
    )
    token_tipo: str = Field(
        default="Bearer",
        description="Esquema de autenticação HTTP (sempre 'Bearer').",
        examples=["Bearer"],
    )
    expira_em_segundos: int = Field(
        default=28800,
        description="Tempo de vida do token em segundos (padrão: 8 horas).",
        examples=[28800],
    )
    usuario: UsuarioAutenticadoResponse = Field(
        ...,
        description="Objeto contendo os dados funcionais do servidor identificado.",
    )
    biometria: Optional[MetricasBiometricasResponse] = Field(
        default=None,
        description=(
            "Métricas opcionais da verificação facial 1:1 (distância "
            "euclidiana, tolerância e confiança) para telemetria/log."
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sucesso": True,
                "mensagem": "Autenticação multifator concluída com sucesso.",
                "token": (
                    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
                    "eyJzdWIiOiIxIiwibm9tZSI6Ikd1aWxoZXJtZSIsIm5pdmVsIjoxfQ."
                    "mock_signature_hash"
                ),
                "token_tipo": "Bearer",
                "expira_em_segundos": 28800,
                "usuario": {
                    "id": 1,
                    "nome": "Guilherme Ferreira",
                    "matricula": "G9483B2",
                    "cargo": "Engenheiro de Bioproteção",
                    "divisao": "Divisão de Contenção Microbiológica",
                    "nivel_acesso": 1,
                },
                "biometria": {
                    "reconhecido": True,
                    "distancia_euclidiana": 0.3412,
                    "tolerancia": 0.5,
                    "confianca_percentual": 93.87,
                },
            }
        }
    )


# =============================================================================
# 4. SCHEMAS DE CADASTRO DE USUÁRIO — POST /cadastrar
# =============================================================================
# Permite registrar um novo servidor público no sistema, associando seus
# dados funcionais e credenciais (CPF + senha) ao vetor de características
# faciais (128D) extraído da foto de referência enviada em Base64.
# =============================================================================

class UsuarioCadastroRequest(_SchemaBase):
    """
    Payload de entrada para o cadastro de novo servidor e biometria de
    referência (POST /cadastrar).
    """

    nome: str = Field(
        ...,
        min_length=3,
        description="Nome completo do servidor público (mínimo 3 caracteres).",
        examples=["Júlia Fernandes"],
    )
    cpf: CpfStr = Field(
        ...,
        min_length=11,
        max_length=14,
        description="CPF do servidor (com ou sem máscara; identificador único de login).",
        examples=["987.654.321-00"],
    )
    senha: SecretStr = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Senha inicial do servidor (mínimo 8 caracteres). Será armazenada como hash.",
        examples=["Faca@2026"],
    )
    matricula: str = Field(
        ...,
        min_length=1,
        description="Matrícula funcional / RA institucional (identificador único).",
        examples=["R101BF1"],
    )
    cargo_id: int = Field(
        ...,
        description="ID de referência do cargo no banco de dados.",
        examples=[2],
    )
    divisao_id: int = Field(
        ...,
        description="ID de referência da divisão / departamento governamental.",
        examples=[1],
    )
    nivel_acesso: Literal[1, 2, 3] = Field(
        ...,
        description=(
            "Nível hierárquico de permissão RBAC: "
            "1 (Operacional), 2 (Diretoria), 3 (Ministerial)."
        ),
        examples=[2],
    )
    imagem_base64: ImagemBase64Str = Field(
        ...,
        min_length=1,
        max_length=_TAMANHO_MAXIMO_BASE64,
        description=(
            "Foto de referência nítida da face em Base64 para extração do "
            "vetor de características biométricas (Fases 1 a 4 do PIVC). "
            "Recomendado Base64 puro; o prefixo Data URL é tolerado."
        ),
        examples=["/9j/4AAQSkZJRgABAQEASABIAAD..."],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Júlia Fernandes",
                "cpf": "987.654.321-00",
                "senha": "Faca@2026",
                "matricula": "R101BF1",
                "cargo_id": 2,
                "divisao_id": 1,
                "nivel_acesso": 2,
                "imagem_base64": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP...",
            }
        }
    )


# ── Sub-modelo: dados do usuário recém-criado na resposta ──

class UsuarioCriadoResponse(_SchemaBase):
    """
    Dados do usuário retornados após cadastro bem-sucedido.
    Reflete os campos persistidos no banco, incluindo o ``id`` gerado
    e o timestamp de criação.
    """

    id: int = Field(
        ...,
        description="ID gerado automaticamente pelo banco de dados.",
        examples=[2],
    )
    nome: str = Field(
        ...,
        description="Nome completo do servidor cadastrado.",
        examples=["Júlia Fernandes"],
    )
    cpf_mascarado: str = Field(
        ...,
        description="CPF mascarado conforme a LGPD (ver ``mascarar_cpf``).",
        examples=["***.654.321-**"],
    )
    matricula: str = Field(
        ...,
        description="Matrícula funcional registrada.",
        examples=["R101BF1"],
    )
    cargo_id: int = Field(
        ...,
        description="ID do cargo associado.",
        examples=[2],
    )
    divisao_id: int = Field(
        ...,
        description="ID da divisão associada.",
        examples=[1],
    )
    nivel_acesso: Literal[1, 2, 3] = Field(
        ...,
        description="Nível de acesso atribuído ao servidor.",
        examples=[2],
    )
    criado_em: datetime = Field(
        ...,
        description="Timestamp UTC da criação do registro no banco.",
        examples=["2026-09-06T20:55:00Z"],
    )


# ── Resposta completa do cadastro ──

class UsuarioCadastroResponse(_SchemaBase):
    """
    Resposta retornada após cadastro bem-sucedido de servidor e biometria
    (HTTP 201 Created).
    """

    sucesso: Literal[True] = Field(
        default=True,
        description="Indicador booleano de sucesso do cadastro.",
    )
    mensagem: str = Field(
        ...,
        description="Mensagem informativa confirmando o registro.",
        examples=["Usuário e biometria facial cadastrados com sucesso."],
    )
    usuario: UsuarioCriadoResponse = Field(
        ...,
        description="Objeto contendo os dados do servidor recém-cadastrado.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sucesso": True,
                "mensagem": "Usuário e biometria facial cadastrados com sucesso.",
                "usuario": {
                    "id": 2,
                    "nome": "Júlia Fernandes",
                    "cpf_mascarado": "***.654.321-**",
                    "matricula": "R101BF1",
                    "cargo_id": 2,
                    "divisao_id": 1,
                    "nivel_acesso": 2,
                    "criado_em": "2026-09-06T20:55:00Z",
                },
            }
        }
    )


# =============================================================================
# 5. SCHEMAS DO COFRE DE TOXINAS — GET /toxinas
# =============================================================================
# Rota protegida por Bearer Token JWT. O backend extrai o nivel_acesso do
# token e filtra dinamicamente os registros retornados de acordo com a
# Matriz de Níveis de Acesso (RBAC) documentada na Seção 3 do API.md.
# =============================================================================

class DetalhesConfidenciaisToxina(_SchemaBase):
    """
    Dados sigilosos de contenção de uma toxina. Visível apenas quando o
    nivel_acesso do requisitante é >= ao nivel_requerido do registro, ou
    retornado como ``null`` caso o operador não tenha privilégio suficiente.
    """

    local_estocagem: str = Field(
        ...,
        description="Localização física do espécime no complexo do Ministério.",
        examples=["Cofre Criogênico A-01"],
    )
    protocolo_neutralizacao: str = Field(
        ...,
        description="Procedimento operacional padrão para neutralização da amostra.",
        examples=["Autoclave 121°C por 30min ou solução de hipoclorito a 0.5%"],
    )


class ToxinaResponse(_SchemaBase):
    """
    Registro individual de uma substância biológica/química controlada
    armazenada no Cofre de Segurança Máxima do Ministério do Meio Ambiente.
    """

    id: int = Field(
        ...,
        description="Identificador numérico único do registro no banco.",
        examples=[101],
    )
    nome_comum: str = Field(
        ...,
        description="Nome químico ou popular da substância biológica/química.",
        examples=["Toxina Botulínica (Amostra Controle)"],
    )
    codigo_amostra: str = Field(
        ...,
        description="Código identificador do composto perigoso (ex: 'TOX-L1-004').",
        examples=["TOX-L1-004"],
    )
    formula_molecular: str = Field(
        ...,
        description="Fórmula molecular da substância (ou 'Classificada' se restrita).",
        examples=["C6760H10447N1743O2010S32"],
    )
    nivel_requerido: Literal[1, 2, 3] = Field(
        ...,
        description=(
            "Nível de permissão mínimo exigido para visualização completa: "
            "1 (Operacional), 2 (Diretoria), 3 (Ministerial)."
        ),
        examples=[1],
    )
    classificacao_risco: str = Field(
        ...,
        description="Classificação do nível de risco biológico/químico da substância.",
        examples=["Moderado / Monitorado"],
    )
    temperatura_armazenamento_celsius: float = Field(
        ...,
        description="Temperatura de conservação da amostra em graus Celsius.",
        examples=[4.0],
    )
    status_contencao: str = Field(
        ...,
        description="Estado atual do confinamento da substância.",
        examples=["Estável"],
        serialization_alias="status_contenção",
        validation_alias="status_contenção",
    )
    detalhes_confidenciais: Optional[DetalhesConfidenciaisToxina] = Field(
        default=None,
        description=(
            "Dados sigilosos de protocolo de contenção. Retorna ``null`` "
            "quando o nível de acesso do requisitante é insuficiente."
        ),
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


# ── Sub-modelo: resumo do solicitante incluído na resposta do cofre ──

class UsuarioSolicitanteResponse(_SchemaBase):
    """
    Resumo do operador que efetuou a consulta ao cofre, extraído do token JWT.
    """

    nome: str = Field(
        ...,
        description="Nome completo do servidor que realizou a requisição.",
        examples=["Guilherme Ferreira"],
    )
    nivel_acesso: Literal[1, 2, 3] = Field(
        ...,
        description="Nível RBAC do requisitante utilizado na filtragem.",
        examples=[1],
    )


# ── Resposta completa da consulta ao cofre ──

class ConsultaCofreResponse(_SchemaBase):
    """
    Resposta paginada da consulta ao Cofre de Toxinas (GET /toxinas — HTTP 200).
    Os registros em ``itens`` já vêm filtrados conforme o nível de acesso
    do Bearer Token apresentado na requisição.
    """

    sucesso: Literal[True] = Field(
        default=True,
        description="Indicador booleano de sucesso da consulta.",
    )
    usuario_solicitante: UsuarioSolicitanteResponse = Field(
        ...,
        description="Resumo do operador que efetuou a consulta.",
    )
    total_registros: int = Field(
        ...,
        ge=0,
        description="Quantidade total de registros retornados após a filtragem RBAC.",
        examples=[1],
    )
    itens: List[ToxinaResponse] = Field(
        ...,
        description="Lista de toxinas visíveis ao nível de acesso do requisitante.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sucesso": True,
                "usuario_solicitante": {
                    "nome": "Guilherme Ferreira",
                    "nivel_acesso": 1,
                },
                "total_registros": 1,
                "itens": [
                    {
                        "id": 101,
                        "nome_comum": "Toxina Botulínica (Amostra Controle)",
                        "codigo_amostra": "TOX-L1-004",
                        "formula_molecular": "C6760H10447N1743O2010S32",
                        "nivel_requerido": 1,
                        "classificacao_risco": "Moderado / Monitorado",
                        "temperatura_armazenamento_celsius": 4.0,
                        "status_contenção": "Estável",
                        "detalhes_confidenciais": None,
                    }
                ],
            }
        }
    )


# =============================================================================
# 6. SCHEMAS GENÉRICOS DE ERRO
# =============================================================================
# O contrato define respostas de erro categorizadas com códigos de erro
# específicos para que o Frontend exiba feedbacks contextuais na UI (ex:
# "Nenhum rosto detectado", "Múltiplos rostos", "Token expirado").
#
# A estrutura segue o padrão:
#   { "sucesso": false, "erro": { "codigo": "...", "mensagem": "...", "detalhes": ... } }
# =============================================================================

class ErroDetalheResponse(_SchemaBase):
    """
    Estrutura do objeto ``erro`` aninhado nas respostas de erro da API.
    Contém o código máquina do erro, a mensagem humanizada e detalhes
    adicionais (formato variável conforme o contexto).
    """

    codigo: str = Field(
        ...,
        description=(
            "Código de erro legível por máquina para tratamento no Frontend "
            "(ex: INVALID_IMAGE, NO_FACE_DETECTED, MULTIPLE_FACES_DETECTED, "
            "INVALID_FACE_VECTOR, FEATURE_EXTRACTION_FAILED, "
            "INVALID_CREDENTIALS, FACE_NOT_RECOGNIZED, ACCOUNT_LOCKED, "
            "TOKEN_INVALID_OR_EXPIRED, INSUFFICIENT_PRIVILEGES, "
            "CPF_ALREADY_EXISTS, MATRICULA_ALREADY_EXISTS, VALIDATION_ERROR, "
            "BIOMETRIC_ENGINE_UNAVAILABLE)."
        ),
        examples=["NO_FACE_DETECTED"],
    )
    mensagem: str = Field(
        ...,
        description="Mensagem explicativa humanizada detalhando a causa do erro.",
        examples=[
            "Nenhum rosto foi detectado na imagem. Centralize seu rosto no "
            "enquadramento e certifique-se de estar em um ambiente iluminado."
        ],
    )
    detalhes: Optional[Any] = Field(
        default=None,
        description=(
            "Dados adicionais contextuais do erro. Pode ser um dicionário "
            "(ex: rostos_encontrados, confianca), uma lista de erros de "
            "validação ou null se não aplicável."
        ),
        examples=[{"rostos_encontrados": 0}],
    )


class ErroResponse(_SchemaBase):
    """
    Envelope padronizado para **todas** as respostas de erro da API F.A.C.A.
    Utilizado em respostas HTTP 400, 401, 403, 409, 422, 500 e 503.
    """

    sucesso: Literal[False] = Field(
        default=False,
        description="Indicador booleano de falha — sempre ``false`` em erros.",
    )
    erro: ErroDetalheResponse = Field(
        ...,
        description="Objeto contendo os detalhes estruturados do erro.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sucesso": False,
                    "erro": {
                        "codigo": "NO_FACE_DETECTED",
                        "mensagem": (
                            "Nenhum rosto foi detectado na imagem. "
                            "Centralize seu rosto no enquadramento e "
                            "certifique-se de estar em um ambiente iluminado."
                        ),
                        "detalhes": {"rostos_encontrados": 0},
                    },
                },
                {
                    "sucesso": False,
                    "erro": {
                        "codigo": "MULTIPLE_FACES_DETECTED",
                        "mensagem": (
                            "Múltiplos rostos detectados (2). Por motivos de "
                            "segurança, apenas uma pessoa deve estar visível "
                            "para a autenticação."
                        ),
                        "detalhes": {"rostos_encontrados": 2},
                    },
                },
                {
                    "sucesso": False,
                    "erro": {
                        "codigo": "INVALID_IMAGE",
                        "mensagem": (
                            "A imagem enviada é inválida, corrompida ou está "
                            "vazia. Envie uma captura JPEG ou PNG codificada "
                            "em Base64."
                        ),
                        "detalhes": None,
                    },
                },
                {
                    "sucesso": False,
                    "erro": {
                        "codigo": "TOKEN_INVALID_OR_EXPIRED",
                        "mensagem": (
                            "Token de autorização não fornecido, inválido "
                            "ou expirado."
                        ),
                        "detalhes": None,
                    },
                },
                {
                    "sucesso": False,
                    "erro": {
                        "codigo": "MATRICULA_ALREADY_EXISTS",
                        "mensagem": (
                            "Já existe um usuário cadastrado com a matrícula "
                            "informada."
                        ),
                        "detalhes": None,
                    },
                },
            ]
        }
    )


# =============================================================================
# 7. SCHEMAS DE FALHA (401) E BLOQUEIO (403) DA AUTENTICAÇÃO MFA
# =============================================================================
# Política de tentativas do Roteiro v2:
#   * Cada falha de senha (INVALID_CREDENTIALS) ou de face
#     (FACE_NOT_RECOGNIZED) consome UMA tentativa → HTTP 401 informando
#     ``tentativas_restantes``.
#   * Por segurança, a mensagem de INVALID_CREDENTIALS não revela se o erro
#     foi no CPF ou na senha (evita enumeração de usuários).
#   * Ao atingir 5 falhas consecutivas, a conta é bloqueada → HTTP 403 com
#     ``bloqueado: true`` e mensagem de ALERTA DE AMEAÇA.
#   * Erros de CAPTURA (400 — sem rosto, múltiplos rostos, imagem inválida)
#     NÃO consomem tentativas, pois não indicam tentativa de fraude.
# Ambos os schemas estendem o envelope ``ErroResponse`` (Seção 6), mantendo
# compatibilidade com o tratamento genérico de erros do Frontend.
# =============================================================================

class AutenticacaoFalhaResponse(ErroResponse):
    """
    Resposta de falha de autenticação recuperável (HTTP 401): credenciais
    inválidas ou biometria não correspondente, ainda com tentativas restantes.
    """

    bloqueado: Literal[False] = Field(
        default=False,
        description="Indica que a conta AINDA NÃO foi bloqueada.",
    )
    tentativas_restantes: int = Field(
        ...,
        ge=0,
        le=MAX_TENTATIVAS_AUTENTICACAO,
        description="Quantidade de tentativas restantes antes do bloqueio.",
        examples=[3],
    )
    tentativas_maximas: int = Field(
        default=MAX_TENTATIVAS_AUTENTICACAO,
        ge=1,
        description="Limite de tentativas consecutivas antes do bloqueio.",
        examples=[MAX_TENTATIVAS_AUTENTICACAO],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "sucesso": False,
                    "bloqueado": False,
                    "tentativas_restantes": 4,
                    "tentativas_maximas": 5,
                    "erro": {
                        "codigo": "INVALID_CREDENTIALS",
                        "mensagem": "CPF ou senha inválidos.",
                        "detalhes": None,
                    },
                },
                {
                    "sucesso": False,
                    "bloqueado": False,
                    "tentativas_restantes": 3,
                    "tentativas_maximas": 5,
                    "erro": {
                        "codigo": "FACE_NOT_RECOGNIZED",
                        "mensagem": (
                            "Acesso Negado: a biometria facial não "
                            "corresponde ao usuário informado."
                        ),
                        "detalhes": {
                            "reconhecido": False,
                            "distancia_euclidiana": 0.7231,
                            "tolerancia": 0.5,
                            "confianca_percentual": 27.7,
                        },
                    },
                },
            ]
        }
    )


class AutenticacaoBloqueadaResponse(ErroResponse):
    """
    Resposta de bloqueio de segurança (HTTP 403) emitida após 5 falhas
    consecutivas — ou em qualquer nova tentativa enquanto o bloqueio durar.
    """

    bloqueado: Literal[True] = Field(
        default=True,
        description="Indica que a conta está BLOQUEADA por suspeita de ameaça.",
    )
    tentativas_restantes: Literal[0] = Field(
        default=0,
        description="Sempre 0 quando a conta está bloqueada.",
    )
    bloqueado_ate: Optional[datetime] = Field(
        default=None,
        description=(
            "Instante UTC até o qual o bloqueio permanece ativo "
            "(null = bloqueio por tempo indeterminado / desbloqueio manual)."
        ),
        examples=["2026-10-19T04:45:00Z"],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sucesso": False,
                "bloqueado": True,
                "tentativas_restantes": 0,
                "bloqueado_ate": "2026-10-19T04:45:00Z",
                "erro": {
                    "codigo": "ACCOUNT_LOCKED",
                    "mensagem": (
                        "ALERTA DE AMEAÇA: acesso bloqueado após 5 tentativas "
                        "de autenticação malsucedidas. A ocorrência foi "
                        "registrada e a equipe de segurança do cofre foi "
                        "notificada."
                    ),
                    "detalhes": {"tentativas_falhas": 5},
                },
            }
        }
    )


# =============================================================================
# 8. SCHEMAS DO DIAGNÓSTICO BIOMÉTRICO ISOLADO — PIVC (/biometria/*)
# =============================================================================
# Rotas técnicas SEM banco de dados para validar as 5 fases do PIVC via
# Swagger (/docs) antes de o MySQL estar populado:
#   * GET  /biometria/status          → parâmetros ativos do motor
#   * POST /biometria/extrair-vetor   → Fases 1–4 (vetor 128D + ROI)
#   * POST /biometria/comparar-teste  → Fases 1–5 entre DUAS imagens
#   * POST /biometria/verificar-vetor → Fases 1–5 imagem × vetor (simula o
#                                       vetor que virá do banco)
# =============================================================================

class CaixaDelimitadoraResponse(_SchemaBase):
    """ROI da face (Fase 3) em pixels da imagem ORIGINAL enviada."""

    top: int = Field(..., ge=0, description="Coordenada y da borda superior.", examples=[112])
    right: int = Field(..., ge=0, description="Coordenada x da borda direita.", examples=[418])
    bottom: int = Field(..., ge=0, description="Coordenada y da borda inferior.", examples=[341])
    left: int = Field(..., ge=0, description="Coordenada x da borda esquerda.", examples=[189])


class DimensoesImagemResponse(_SchemaBase):
    """Dimensões de uma matriz de imagem em pixels."""

    largura: int = Field(..., ge=1, examples=[1280])
    altura: int = Field(..., ge=1, examples=[720])


class BiometriaStatusResponse(_SchemaBase):
    """Parâmetros operacionais ativos do motor biométrico."""

    motor_disponivel: bool = Field(
        ...,
        description="True se o face_recognition (dlib) foi carregado com sucesso.",
    )
    tolerancia: float = Field(..., description="FACE_RECOGNITION_TOLERANCE ativa.", examples=[0.5])
    modelo_deteccao: Literal["hog", "cnn"] = Field(..., examples=["hog"])
    upsample: int = Field(..., ge=0, examples=[1])
    dimensao_maxima_px: int = Field(..., ge=1, examples=[800])
    dimensao_vetor: Literal[128] = Field(default=128)


class BiometriaExtracaoRequest(_SchemaBase):
    """Payload de POST /biometria/extrair-vetor (Fases 1 → 4)."""

    imagem_base64: ImagemBase64Str = Field(
        ...,
        min_length=1,
        max_length=_TAMANHO_MAXIMO_BASE64,
        description="Imagem JPEG/PNG em Base64 (Data URL tolerado).",
        examples=["/9j/4AAQSkZJRgABAQEASABIAAD..."],
    )
    num_jitters: int = Field(
        default=1,
        ge=1,
        le=10,
        description=(
            "Reamostragens da face cuja média forma o descritor (maior = "
            "mais estável e mais lento)."
        ),
    )


class BiometriaExtracaoResponse(_SchemaBase):
    """Resultado das Fases 1 → 4 do PIVC sobre uma única imagem."""

    sucesso: Literal[True] = Field(default=True)
    mensagem: str = Field(..., examples=["Vetor biométrico 128D extraído com sucesso."])
    rosto_detectado: Literal[True] = Field(default=True)
    quantidade_rostos: Literal[1] = Field(default=1)
    localizacao_rosto: CaixaDelimitadoraResponse = Field(
        ...,
        description="Caixa delimitadora (top, right, bottom, left) na imagem original.",
    )
    dimensoes_originais: DimensoesImagemResponse
    dimensoes_processadas: DimensoesImagemResponse
    fator_escala: float = Field(..., gt=0, le=1, examples=[0.625])
    iluminacao_normalizada: bool = Field(
        ...,
        description="True se o CLAHE (Fase 2) foi aplicado por baixa luminosidade/contraste.",
    )
    dimensao_vetor: Literal[128] = Field(default=128)
    vetor_caracteristicas: List[float] = Field(
        ...,
        min_length=128,
        max_length=128,
        description="Descritor facial de 128 dimensões (ResNet-34 dlib).",
    )
    tempos_fases_ms: Dict[str, float] = Field(
        ...,
        description="Latência de cada fase do pipeline em milissegundos.",
        examples=[{
            "fase1_aquisicao": 4.1,
            "fase2_preprocessamento": 2.3,
            "fase3_segmentacao": 182.5,
            "fase4_extracao": 61.7,
        }],
    )
    tempo_total_ms: float = Field(..., ge=0, examples=[250.6])

    model_config = ConfigDict(
        json_schema_extra=cast(Any, {
            "example": {
                "sucesso": True,
                "mensagem": "Vetor biométrico 128D extraído com sucesso.",
                "rosto_detectado": True,
                "quantidade_rostos": 1,
                "localizacao_rosto": {"top": 112, "right": 418, "bottom": 341, "left": 189},
                "dimensoes_originais": {"largura": 1280, "altura": 720},
                "dimensoes_processadas": {"largura": 800, "altura": 450},
                "fator_escala": 0.625,
                "iluminacao_normalizada": False,
                "dimensao_vetor": 128,
                "vetor_caracteristicas": _EXEMPLO_VETOR_128D,
                "tempos_fases_ms": {
                    "fase1_aquisicao": 4.1,
                    "fase2_preprocessamento": 2.3,
                    "fase3_segmentacao": 182.5,
                    "fase4_extracao": 61.7,
                },
                "tempo_total_ms": 250.6,
            }
        })
    )


class BiometriaComparacaoRequest(_SchemaBase):
    """Payload de POST /biometria/comparar-teste (1:1 entre duas imagens)."""

    imagem_referencia_base64: ImagemBase64Str = Field(
        ...,
        min_length=1,
        max_length=_TAMANHO_MAXIMO_BASE64,
        description="Imagem de referência (simula a foto do cadastro).",
        examples=["/9j/4AAQSkZJRgABAQEASABIAAD..."],
    )
    imagem_teste_base64: ImagemBase64Str = Field(
        ...,
        min_length=1,
        max_length=_TAMANHO_MAXIMO_BASE64,
        description="Imagem de teste (simula o frame da webcam no login).",
        examples=["/9j/4AAQSkZJRgABAQEASABIAAD..."],
    )
    tolerancia: Optional[float] = Field(
        default=None,
        gt=0,
        le=1,
        description="Limiar opcional; se omitido usa FACE_RECOGNITION_TOLERANCE (0.50).",
        examples=[0.5],
    )


class BiometriaComparacaoResponse(_SchemaBase):
    """
    Resultado da comparação 1:1 entre duas imagens (Fases 1 → 5). Sendo uma
    rota de diagnóstico, um NÃO-match retorna HTTP 200 com ``reconhecido: false``.
    """

    sucesso: Literal[True] = Field(default=True)
    mensagem: str = Field(..., examples=["As faces pertencem à mesma pessoa (match)."])
    resultado: MetricasBiometricasResponse
    localizacao_rosto_referencia: CaixaDelimitadoraResponse
    localizacao_rosto_teste: CaixaDelimitadoraResponse
    tempo_total_ms: float = Field(..., ge=0, examples=[498.2])


class BiometriaVerificacaoRequest(_SchemaBase):
    """
    Payload de POST /biometria/verificar-vetor: imagem × vetor 128D de
    referência (exatamente o fluxo que o /autenticar usará com o banco).
    """

    imagem_base64: ImagemBase64Str = Field(
        ...,
        min_length=1,
        max_length=_TAMANHO_MAXIMO_BASE64,
        description="Frame da webcam em Base64 (Data URL tolerado).",
        examples=["/9j/4AAQSkZJRgABAQEASABIAAD..."],
    )
    vetor_referencia: List[float] = Field(
        ...,
        min_length=128,
        max_length=128,
        description="Vetor 128D de referência (ex.: obtido em /biometria/extrair-vetor).",
        examples=[_EXEMPLO_VETOR_128D],
    )
    tolerancia: Optional[float] = Field(
        default=None,
        gt=0,
        le=1,
        description="Limiar opcional; se omitido usa FACE_RECOGNITION_TOLERANCE (0.50).",
        examples=[0.5],
    )


class BiometriaVerificacaoResponse(_SchemaBase):
    """Resultado da verificação 1:1 imagem × vetor (Fases 1 → 5)."""

    sucesso: Literal[True] = Field(default=True)
    mensagem: str = Field(..., examples=["Biometria compatível com o vetor de referência."])
    resultado: MetricasBiometricasResponse
    tempo_total_ms: float = Field(..., ge=0, examples=[251.3])
