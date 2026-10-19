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
  1. Imports e Configurações Base
  2. Schemas do Health Check (/ping)
  3. Schemas de Autenticação Biométrica (/autenticar)
  4. Schemas de Cadastro de Usuário (/cadastrar)
  5. Schemas do Cofre de Toxinas (/toxinas)
  6. Schemas Genéricos de Erro
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "mensagem": "Servidor F.A.C.A. operacional",
                "versao": "1.0.0",
                "timestamp": "2026-09-06T20:50:00Z",
            }
        }
    )


# =============================================================================
# 3. SCHEMAS DE AUTENTICAÇÃO BIOMÉTRICA — POST /autenticar
# =============================================================================
# Fluxo PIVC: o Frontend captura o frame da webcam, converte para Base64 puro
# (sem prefixo data:image/...) e envia ao backend, que submete a imagem ao
# pipeline de detecção, extração de features e classificação. Em caso de
# match com confiança suficiente, o backend devolve os dados do usuário e um
# token JWT de sessão.
# =============================================================================

class AutenticacaoRequest(_SchemaBase):
    """
    Payload de entrada do endpoint de autenticação facial (POST /autenticar).

    O campo `imagem_base64` deve conter **exclusivamente** a string Base64 pura
    da captura JPEG/PNG — sem o prefixo ``data:image/...;base64,``.
    """

    imagem_base64: str = Field(
        ...,
        min_length=1,
        description=(
            "String Base64 pura da captura facial (JPEG ou PNG). "
            "NÃO incluir o prefixo 'data:image/...;base64,'."
        ),
        examples=["/9j/4AAQSkZJRgABAQEASABIAAD..."],
    )

    @field_validator("imagem_base64")
    @classmethod
    def _rejeitar_prefixo_data_url(cls, valor: str) -> str:
        """
        Valida que a string Base64 NÃO contém o cabeçalho Data URL.
        Rejeita proativamente payloads incorretos vindos do Frontend,
        conforme a regra documentada na Seção 2 do API.md.
        """
        if valor.startswith("data:"):
            raise ValueError(
                "O campo 'imagem_base64' não deve conter o prefixo "
                "'data:image/...;base64,'. Envie apenas a string Base64 pura."
            )
        return valor

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "imagem_base64": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP..."
            }
        }
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
    Resposta retornada quando a autenticação biométrica é bem-sucedida
    (HTTP 200). Contém o token JWT, metadados de expiração e os dados
    completos do usuário identificado.
    """

    sucesso: Literal[True] = Field(
        default=True,
        description="Indicador booleano de sucesso da operação.",
    )
    mensagem: str = Field(
        ...,
        description="Mensagem explicativa do resultado da autenticação.",
        examples=["Identificação biométrica concluída com sucesso."],
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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sucesso": True,
                "mensagem": "Identificação biométrica concluída com sucesso.",
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
            }
        }
    )


# =============================================================================
# 4. SCHEMAS DE CADASTRO DE USUÁRIO — POST /cadastrar
# =============================================================================
# Permite registrar um novo servidor público no sistema, associando seus
# dados funcionais a um vetor de características faciais extraído da foto
# de referência de alta qualidade enviada em Base64 puro.
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
    imagem_base64: str = Field(
        ...,
        min_length=1,
        description=(
            "Foto de referência nítida da face em Base64 puro para "
            "extração do vetor de características biométricas. "
            "NÃO incluir o prefixo 'data:image/...;base64,'."
        ),
        examples=["/9j/4AAQSkZJRgABAQEASABIAAD..."],
    )

    @field_validator("imagem_base64")
    @classmethod
    def _rejeitar_prefixo_data_url(cls, valor: str) -> str:
        """Reusa a mesma regra de rejeição de Data URL do endpoint /autenticar."""
        if valor.startswith("data:"):
            raise ValueError(
                "O campo 'imagem_base64' não deve conter o prefixo "
                "'data:image/...;base64,'. Envie apenas a string Base64 pura."
            )
        return valor

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Júlia Fernandes",
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
            "(ex: NO_FACE_DETECTED, MULTIPLE_FACES_DETECTED, "
            "FACE_NOT_RECOGNIZED, TOKEN_INVALID_OR_EXPIRED, "
            "INSUFFICIENT_PRIVILEGES, MATRICULA_ALREADY_EXISTS, VALIDATION_ERROR)."
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
    Utilizado em respostas HTTP 400, 401, 403, 409 e 422.
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
                        "codigo": "FACE_NOT_RECOGNIZED",
                        "mensagem": (
                            "Acesso Negado: Rosto não identificado na base "
                            "de funcionários autorizados."
                        ),
                        "detalhes": {
                            "confianca": 0.42,
                            "limiar_minimo": 0.75,
                        },
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
