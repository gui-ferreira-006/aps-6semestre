"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)
Camada de Conexão com o Banco de Dados MySQL 8.0 (database.py)
==============================================================================

Módulo responsável pela configuração da engine SQLAlchemy 2.0, gerenciamento do
pool de conexões, classe base declarativa (DeclarativeBase), gerador de sessão
(get_db) para injeção de dependência no FastAPI e rotinas de health check SQL.
"""

from __future__ import annotations

import os
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Carrega variáveis de ambiente do arquivo .env local, se existir
load_dotenv()


def obter_database_url() -> str:
    """
    Constrói ou recupera a URL de conexão com o banco MySQL 8.0.
    Prioriza a variável de ambiente DATABASE_URL. Caso não esteja definida,
    monta a string a partir das variáveis individuais com fallback inteligente
    para o schema oficial aps_biometria e porta publicada 3307.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        # Garante o driver pymysql caso tenha sido informado mysql://
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        return url

    user = os.getenv("MYSQL_USER", "faca_user")
    password = os.getenv("MYSQL_PASSWORD", "faca_pass_2026")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3307")
    database = os.getenv("MYSQL_DATABASE", "aps_biometria")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


DATABASE_URL = obter_database_url()

# Engine SQLAlchemy 2.0 com configurações resilientes para contêineres Docker:
#   - pool_pre_ping: testa a conexão antes de entregá-la da pool, evitando erros
#     de "MySQL server has gone away" após ociosidade.
#   - pool_recycle: recicla conexões a cada 3600 segundos (1 hora).
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# Fábrica de sessões ORM configurada sem autoflush/autocommit antecipados
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Classe base declarativa padrão do SQLAlchemy 2.0."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Gerador de dependência FastAPI (Depends(get_db)).
    Abre uma sessão transacional limpa e garante seu fechamento seguro
    ao término de cada ciclo de requisição HTTP.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def testar_conexao_sql() -> bool:
    """
    Executa uma consulta leve (SELECT 1) para aferir a conectividade física
    e operacional com o contêiner MySQL 8.0. Utilizada no endpoint /ping
    e nos testes de integração.
    """
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def obter_instancia_banco() -> Optional[str]:
    """
    Retorna um identificador do "ciclo de vida" do banco aps_biometria: o
    instante de criação da tabela usuario (muda a cada `docker compose down -v`
    + recriação do volume). O frontend compara esse valor com o que guardou no
    localStorage para descartar caches locais de uma instância anterior do banco
    (dados residuais de testes), garantindo o "Estado Dia Zero" na interface.
    """
    try:
        with engine.connect() as conexao:
            criado_em = conexao.execute(
                text(
                    "SELECT CREATE_TIME FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'usuario'"
                )
            ).scalar()
        if criado_em is not None and hasattr(criado_em, "isoformat"):
            return str(criado_em.isoformat())
        return str(criado_em) if criado_em is not None else None
    except Exception:
        return None
