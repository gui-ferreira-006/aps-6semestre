"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)
Modelos ORM Tipados SQLAlchemy 2.0 (models.py)
==============================================================================

Espelha fielmente as 10 tabelas normalizadas em 3FN do schema oficial aps_biometria:
  1. divisao
  2. cargo
  3. nivel_acesso
  4. usuario
  5. toxina
  6. documento
  7. biometria
  8. tentativa_autenticacao
  9. bloqueio_login
  10. auditoria
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# =============================================================================
# 1. DIVISAO
# =============================================================================
class Divisao(Base):
    __tablename__ = "divisao"

    id_divisao: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    usuarios: Mapped[List[Usuario]] = relationship("Usuario", back_populates="divisao")
    toxinas: Mapped[List[Toxina]] = relationship("Toxina", back_populates="divisao")
    documentos: Mapped[List[Documento]] = relationship("Documento", back_populates="divisao")


# =============================================================================
# 2. CARGO
# =============================================================================
class Cargo(Base):
    __tablename__ = "cargo"

    id_cargo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relacionamentos
    usuarios: Mapped[List[Usuario]] = relationship("Usuario", back_populates="cargo")


# =============================================================================
# 3. NIVEL_ACESSO
# =============================================================================
class NivelAcesso(Base):
    __tablename__ = "nivel_acesso"

    id_nivel_acesso: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relacionamentos
    usuarios: Mapped[List[Usuario]] = relationship("Usuario", back_populates="nivel_acesso")


# =============================================================================
# 4. USUARIO
# =============================================================================
class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    matricula: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    hash_senha: Mapped[str] = mapped_column(String(255), nullable=False)

    id_cargo: Mapped[int] = mapped_column(BigInteger, ForeignKey("cargo.id_cargo"), nullable=False)
    id_nivel_acesso: Mapped[int] = mapped_column(SmallInteger, ForeignKey("nivel_acesso.id_nivel_acesso"), nullable=False)
    id_divisao: Mapped[int] = mapped_column(BigInteger, ForeignKey("divisao.id_divisao"), nullable=False)

    status_conta: Mapped[str] = mapped_column(
        Enum("ATIVA", "DESATIVADA", name="enum_usuario_status"),
        default="ATIVA",
        nullable=False,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos
    cargo: Mapped[Cargo] = relationship("Cargo", back_populates="usuarios")
    nivel_acesso: Mapped[NivelAcesso] = relationship("NivelAcesso", back_populates="usuarios")
    divisao: Mapped[Divisao] = relationship("Divisao", back_populates="usuarios")
    biometria: Mapped[Optional[Biometria]] = relationship(
        "Biometria",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
    )
    toxinas_criadas: Mapped[List[Toxina]] = relationship("Toxina", back_populates="criador")
    documentos_criados: Mapped[List[Documento]] = relationship("Documento", back_populates="criador")
    tentativas: Mapped[List[TentativaAutenticacao]] = relationship("TentativaAutenticacao", back_populates="usuario")
    auditorias: Mapped[List[Auditoria]] = relationship("Auditoria", back_populates="usuario")


# =============================================================================
# 5. TOXINA
# =============================================================================
class Toxina(Base):
    __tablename__ = "toxina"

    id_toxina: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    classificacao: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    id_divisao_responsavel: Mapped[int] = mapped_column(BigInteger, ForeignKey("divisao.id_divisao"), nullable=False)
    id_criador: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id_usuario"), nullable=False)

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos
    divisao: Mapped[Divisao] = relationship("Divisao", back_populates="toxinas")
    criador: Mapped[Usuario] = relationship("Usuario", back_populates="toxinas_criadas")
    documentos: Mapped[List[Documento]] = relationship("Documento", back_populates="toxina")


# =============================================================================
# 6. DOCUMENTO
# =============================================================================
class Documento(Base):
    __tablename__ = "documento"

    id_documento: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo_documento: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    local_arquivo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    hash_arquivo: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    id_toxina: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("toxina.id_toxina"), nullable=True)
    id_divisao_responsavel: Mapped[int] = mapped_column(BigInteger, ForeignKey("divisao.id_divisao"), nullable=False)
    id_criador: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id_usuario"), nullable=False)

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos
    toxina: Mapped[Optional[Toxina]] = relationship("Toxina", back_populates="documentos")
    divisao: Mapped[Divisao] = relationship("Divisao", back_populates="documentos")
    criador: Mapped[Usuario] = relationship("Usuario", back_populates="documentos_criados")


# =============================================================================
# 7. BIOMETRIA
# =============================================================================
class Biometria(Base):
    __tablename__ = "biometria"

    id_biometria: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id_usuario"), unique=True, nullable=False)
    modelo_facial: Mapped[Any] = mapped_column(JSON, nullable=False)
    versao_modelo: Mapped[str] = mapped_column(String(50), nullable=False)

    data_cadastro: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos
    usuario: Mapped[Usuario] = relationship("Usuario", back_populates="biometria")


# =============================================================================
# 8. TENTATIVA_AUTENTICACAO
# =============================================================================
class TentativaAutenticacao(Base):
    __tablename__ = "tentativa_autenticacao"

    id_tentativa: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("usuario.id_usuario"), nullable=True)

    tipo_identificador: Mapped[str] = mapped_column(
        Enum("CPF", "MATRICULA", name="enum_tentativa_tipo_id"),
        nullable=False,
    )
    identificador_protegido: Mapped[str] = mapped_column(String(255), nullable=False)

    etapa: Mapped[str] = mapped_column(
        Enum("CREDENCIAIS", "BIOMETRIA", "CONCLUSAO", name="enum_tentativa_etapa"),
        nullable=False,
    )
    resultado: Mapped[str] = mapped_column(
        Enum("SUCESSO", "FALHA", "NEGADO", "BLOQUEADO", name="enum_tentativa_resultado"),
        nullable=False,
    )
    motivo: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    data_hora: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos
    usuario: Mapped[Optional[Usuario]] = relationship("Usuario", back_populates="tentativas")
    bloqueios_originados: Mapped[List[BloqueioLogin]] = relationship("BloqueioLogin", back_populates="tentativa_origem")


# =============================================================================
# 9. BLOQUEIO_LOGIN
# =============================================================================
class BloqueioLogin(Base):
    __tablename__ = "bloqueio_login"

    id_bloqueio: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tipo_identificador: Mapped[str] = mapped_column(
        Enum("CPF", "MATRICULA", name="enum_bloqueio_tipo_id"),
        nullable=False,
    )
    identificador_protegido: Mapped[str] = mapped_column(String(255), nullable=False)

    data_hora_inicio: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    data_hora_fim: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    motivo: Mapped[str] = mapped_column(String(120), default="LIMITE_TENTATIVAS", nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    id_tentativa_origem: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("tentativa_autenticacao.id_tentativa"),
        nullable=True,
    )

    # Relacionamentos
    tentativa_origem: Mapped[Optional[TentativaAutenticacao]] = relationship(
        "TentativaAutenticacao",
        back_populates="bloqueios_originados",
    )


# =============================================================================
# 10. AUDITORIA
# =============================================================================
class Auditoria(Base):
    __tablename__ = "auditoria"

    id_auditoria: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("usuario.id_usuario"), nullable=True)

    acao: Mapped[str] = mapped_column(String(100), nullable=False)
    entidade_afetada: Mapped[str] = mapped_column(String(80), nullable=False)
    id_registro_afetado: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    resultado: Mapped[str] = mapped_column(
        Enum("SUCESSO", "FALHA", "NEGADO", name="enum_auditoria_resultado"),
        nullable=False,
    )
    detalhes: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    data_hora: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos
    usuario: Mapped[Optional[Usuario]] = relationship("Usuario", back_populates="auditorias")
