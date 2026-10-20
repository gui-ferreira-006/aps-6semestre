"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)
Camada de Repositório e Regras de Persistência (crud.py)
==============================================================================

Encapsula todas as operações de banco de dados do sistema com SQLAlchemy 2.0:
  - Busca de usuários com eager loading (joinedload);
  - Hashing seguro de senhas com PBKDF2-HMAC-SHA256 (compatível com SHA256);
  - Controle de tentativas de autenticação e bloqueio temporário (15 min);
  - Registro de auditoria em conformidade com as diretrizes do Ministério;
  - Enrollment biométrico on-the-fly e cadastro de novos operadores;
  - Consultas e cadastros no cofre de toxinas e documentos técnicos.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session, joinedload

from models import (
    Auditoria,
    Biometria,
    BloqueioLogin,
    Cargo,
    Divisao,
    Documento,
    NivelAcesso,
    TentativaAutenticacao,
    Toxina,
    Usuario,
)
from schemas import MAX_TENTATIVAS_AUTENTICACAO, mascarar_cpf


# =============================================================================
# 1. HASHING E VERIFICAÇÃO DE SENHAS (PBKDF2-HMAC-SHA256 / SHA-256)
# =============================================================================

def gerar_hash_senha(senha: str) -> str:
    """
    Gera hash criptográfico seguro com salt aleatório de 16 bytes e 100.000
    iterações de PBKDF2-HMAC-SHA256. Formato: pbkdf2_sha256$100000$salt$hash.
    """
    salt = secrets.token_hex(16)
    kdf = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"pbkdf2_sha256$100000${salt}${kdf.hex()}"


def verificar_senha(senha_plana: str, hash_armazenado: str) -> bool:
    """
    Verifica se a senha informada confere com o hash armazenado no banco.
    Suporta:
      1. PBKDF2-HMAC-SHA256 com salt (padrão de produção);
      2. SHA-256 puro em hexadecimal (64 caracteres);
      3. Comparação de tempo constante (secrets.compare_digest).
    """
    if not hash_armazenado:
        return False

    # 1. PBKDF2
    if hash_armazenado.startswith("pbkdf2_sha256$"):
        try:
            partes = hash_armazenado.split("$")
            if len(partes) == 4:
                _, iter_str, salt, hash_hex = partes
                iteracoes = int(iter_str)
                kdf = hashlib.pbkdf2_hmac(
                    "sha256",
                    senha_plana.encode("utf-8"),
                    salt.encode("utf-8"),
                    iteracoes,
                )
                return secrets.compare_digest(kdf.hex(), hash_hex)
        except Exception:
            return False

    # 2. SHA-256 puro (64 caracteres hexadecimais)
    if len(hash_armazenado) == 64 and all(c in "0123456789abcdefABCDEF" for c in hash_armazenado):
        hash_calc = hashlib.sha256(senha_plana.encode("utf-8")).hexdigest().lower()
        return secrets.compare_digest(hash_calc, hash_armazenado.lower())

    # 3. Fallback defensivo para texto plano (ambientes de teste legados)
    return secrets.compare_digest(senha_plana, hash_armazenado)


# =============================================================================
# 2. SANITIZAÇÃO E PROTEÇÃO DE IDENTIFICADORES (LGPD)
# =============================================================================

def obter_identificador_protegido(identificador: str) -> str:
    """
    Gera a representação protegida do identificador para log e auditoria:
    se for CPF (11 dígitos numéricos), aplica máscara LGPD e sufixo hash
    para evitar colisões; caso contrário, normaliza a matrícula institucional.
    """
    digitos = re.sub(r"\D", "", identificador)
    if len(digitos) == 11:
        sufixo = hashlib.sha256(digitos.encode("utf-8")).hexdigest()[:8]
        return f"{mascarar_cpf(digitos)} [{sufixo}]"
    return identificador.strip().upper()


def extrair_tipo_identificador(identificador: str) -> str:
    """Determina se o identificador informado é um 'CPF' ou uma 'MATRICULA'."""
    digitos = re.sub(r"\D", "", identificador)
    return "CPF" if len(digitos) == 11 else "MATRICULA"


# =============================================================================
# 3. BUSCA E CONSULTA DE USUÁRIOS
# =============================================================================

def buscar_usuario(db: Session, identificador: str) -> Optional[Usuario]:
    """
    Localiza o servidor público no MySQL por CPF (limpo, 11 dígitos) ou Matrícula
    institucional, realizando eager loading (joinedload) das tabelas cargo,
    divisao, nivel_acesso e biometria para evitar queries N+1.
    """
    digitos = re.sub(r"\D", "", identificador)
    termo = identificador.strip()

    query = (
        db.query(Usuario)
        .options(
            joinedload(Usuario.cargo),
            joinedload(Usuario.divisao),
            joinedload(Usuario.nivel_acesso),
            joinedload(Usuario.biometria),
        )
    )

    if len(digitos) == 11:
        # Busca prioritária por CPF de 11 dígitos
        usuario = query.filter(Usuario.cpf == digitos).first()
        if usuario:
            return usuario

    # Busca por matrícula institucional ou correspondência exata
    return query.filter(Usuario.matricula == termo).first()


def buscar_usuario_por_id(db: Session, id_usuario: int) -> Optional[Usuario]:
    """Recupera usuário por chave primária interna id_usuario com relacionamentos."""
    return (
        db.query(Usuario)
        .options(
            joinedload(Usuario.cargo),
            joinedload(Usuario.divisao),
            joinedload(Usuario.nivel_acesso),
            joinedload(Usuario.biometria),
        )
        .filter(Usuario.id_usuario == id_usuario)
        .first()
    )


# =============================================================================
# 4. CONTROLE DE BLOQUEIO DE LOGIN E REGISTRO DE TENTATIVAS
# =============================================================================

def verificar_bloqueio_ativo(
    db: Session,
    identificador_protegido: str,
) -> Optional[BloqueioLogin]:
    """
    Verifica se há bloqueio ativo (ativo=True e data_hora_fim > agora) para o
    identificador protegido informado. Caso exista bloqueio que já tenha expirado,
    desativa-o automaticamente e confirma no banco.
    """
    agora = datetime.utcnow()
    bloqueio = (
        db.query(BloqueioLogin)
        .filter(
            BloqueioLogin.identificador_protegido == identificador_protegido,
            BloqueioLogin.ativo.is_(True),
        )
        .order_by(BloqueioLogin.data_hora_fim.desc())
        .first()
    )

    if not bloqueio:
        return None

    if bloqueio.data_hora_fim <= agora:
        bloqueio.ativo = False
        db.commit()
        return None

    return bloqueio


def registrar_tentativa(
    db: Session,
    tipo_identificador: str,
    identificador_protegido: str,
    etapa: str,
    resultado: str,
    motivo: Optional[str] = None,
    id_usuario: Optional[int] = None,
) -> TentativaAutenticacao:
    """
    Registra uma ocorrência na tabela tentativa_autenticacao.
    Permite registrar tentativas tanto de usuários cadastrados quanto anônimos.
    """
    tentativa = TentativaAutenticacao(
        id_usuario=id_usuario,
        tipo_identificador=tipo_identificador,
        identificador_protegido=identificador_protegido,
        etapa=etapa,
        resultado=resultado,
        motivo=motivo,
        data_hora=datetime.utcnow(),
    )
    db.add(tentativa)
    db.commit()
    db.refresh(tentativa)
    return tentativa


def contar_falhas_consecutivas(
    db: Session,
    identificador_protegido: str,
) -> int:
    """
    Contabiliza as falhas consecutivas recentes (FALHA ou NEGADO) para o
    identificador protegido desde o último sucesso ou último desbloqueio.
    """
    tentativas = (
        db.query(TentativaAutenticacao)
        .filter(TentativaAutenticacao.identificador_protegido == identificador_protegido)
        .order_by(TentativaAutenticacao.data_hora.desc(), TentativaAutenticacao.id_tentativa.desc())
        .limit(20)
        .all()
    )

    falhas = 0
    for t in tentativas:
        if t.resultado == "SUCESSO" or t.resultado == "BLOQUEADO":
            break
        if t.resultado in ("FALHA", "NEGADO"):
            falhas += 1

    return falhas


def aplicar_bloqueio_se_necessario(
    db: Session,
    tipo_identificador: str,
    identificador_protegido: str,
    tentativa_origem: Optional[TentativaAutenticacao] = None,
    id_usuario: Optional[int] = None,
    minutos_bloqueio: int = 15,
) -> Optional[BloqueioLogin]:
    """
    Avalia a sequência de falhas consecutivas. Ao atingir o limiar oficial
    (5 falhas consecutivas), insere um registro na tabela bloqueio_login com
    janela de 15 minutos e grava o evento correspondente na tabela auditoria.
    """
    falhas = contar_falhas_consecutivas(db, identificador_protegido)
    if falhas < MAX_TENTATIVAS_AUTENTICACAO:
        return None

    agora = datetime.utcnow()
    bloqueio_ate = agora + timedelta(minutes=minutos_bloqueio)

    bloqueio = BloqueioLogin(
        tipo_identificador=tipo_identificador,
        identificador_protegido=identificador_protegido,
        data_hora_inicio=agora,
        data_hora_fim=bloqueio_ate,
        motivo="LIMITE_TENTATIVAS",
        ativo=True,
        id_tentativa_origem=tentativa_origem.id_tentativa if tentativa_origem else None,
    )
    db.add(bloqueio)
    db.flush()

    registrar_auditoria(
        db,
        id_usuario=id_usuario,
        acao="BLOQUEIO_CONTA",
        entidade_afetada="usuario",
        id_registro_afetado=str(id_usuario) if id_usuario else identificador_protegido,
        resultado="NEGADO",
        detalhes={
            "motivo": "LIMITE_TENTATIVAS",
            "identificador_protegido": identificador_protegido,
            "tentativas_falhas": falhas,
            "bloqueado_ate": bloqueio_ate.isoformat(),
        },
    )

    db.commit()
    db.refresh(bloqueio)
    return bloqueio


def desbloquear_usuario(
    db: Session,
    identificador: str,
    admin_id: Optional[int] = None,
) -> int:
    """
    Desativa todos os bloqueios ativos para o CPF ou Matrícula informado.
    Zera a sequência de falhas registrando tentativa de desbloqueio e log
    de auditoria. Retorna o total de bloqueios desativados.
    """
    ident_prot = obter_identificador_protegido(identificador)
    digitos = re.sub(r"\D", "", identificador)
    usuario = buscar_usuario(db, identificador)

    bloqueios = (
        db.query(BloqueioLogin)
        .filter(
            BloqueioLogin.ativo.is_(True),
            (
                (BloqueioLogin.identificador_protegido == ident_prot)
                | (BloqueioLogin.identificador_protegido.like(f"%{mascarar_cpf(digitos)}%"))
                | (BloqueioLogin.identificador_protegido == identificador.strip().upper())
            ),
        )
        .all()
    )

    qtd = len(bloqueios)
    for b in bloqueios:
        b.ativo = False

    # Registra tentativa de sucesso de desbloqueio para zerar a contagem de falhas consecutivas
    registrar_tentativa(
        db,
        tipo_identificador=extrair_tipo_identificador(identificador),
        identificador_protegido=ident_prot,
        etapa="CONCLUSAO",
        resultado="SUCESSO",
        motivo="Desbloqueio administrativo de emergência",
        id_usuario=usuario.id_usuario if usuario else None,
    )

    registrar_auditoria(
        db,
        id_usuario=admin_id or (usuario.id_usuario if usuario else None),
        acao="DESBLOQUEIO_CONTA",
        entidade_afetada="bloqueio_login",
        id_registro_afetado=str(usuario.id_usuario if usuario else identificador),
        resultado="SUCESSO",
        detalhes={
            "identificador_solicitado": identificador,
            "bloqueios_desativados": qtd,
        },
    )

    db.commit()
    return qtd


# =============================================================================
# 5. AUDITORIA E LOGS DE SEGURANÇA
# =============================================================================

def registrar_auditoria(
    db: Session,
    acao: str,
    entidade_afetada: str,
    resultado: str,
    id_usuario: Optional[int] = None,
    id_registro_afetado: Optional[str] = None,
    detalhes: Optional[Dict[str, Any]] = None,
) -> Auditoria:
    """
    Insere registro na tabela auditoria.
    Regra de segurança: NÃO armazena senhas nem vetores faciais nos detalhes.
    """
    registro = Auditoria(
        id_usuario=id_usuario,
        acao=acao,
        entidade_afetada=entidade_afetada,
        id_registro_afetado=id_registro_afetado,
        resultado=resultado,
        detalhes=detalhes,
        data_hora=datetime.utcnow(),
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def listar_auditorias(db: Session, limite: int = 50) -> List[Auditoria]:
    """Lista as ocorrências mais recentes de auditoria do sistema."""
    return (
        db.query(Auditoria)
        .order_by(Auditoria.data_hora.desc())
        .limit(limite)
        .all()
    )


def listar_tentativas(db: Session, limite: int = 50) -> List[TentativaAutenticacao]:
    """Lista as tentativas mais recentes de autenticação."""
    return (
        db.query(TentativaAutenticacao)
        .order_by(TentativaAutenticacao.data_hora.desc())
        .limit(limite)
        .all()
    )


# =============================================================================
# 6. ENROLLMENT BIOMÉTRICO ON-THE-FLY E CADASTRO
# =============================================================================

def salvar_biometria_usuario(
    db: Session,
    id_usuario: int,
    vetor_128d: List[float],
    versao_modelo: str = "dlib_resnet34_v1",
) -> Biometria:
    """
    Grava ou atualiza o modelo facial de 128 dimensões na tabela biometria,
    vinculado unicamente ao id_usuario (UNIQUE), e registra na auditoria.
    """
    biometria = db.query(Biometria).filter(Biometria.id_usuario == id_usuario).first()
    acao_auditoria = "ATUALIZACAO_BIOMETRIA" if biometria else "ENROLLMENT_BIOMETRICO"

    if biometria:
        biometria.modelo_facial = vetor_128d
        biometria.versao_modelo = versao_modelo
        biometria.data_atualizacao = datetime.utcnow()
    else:
        biometria = Biometria(
            id_usuario=id_usuario,
            modelo_facial=vetor_128d,
            versao_modelo=versao_modelo,
            data_cadastro=datetime.utcnow(),
            data_atualizacao=datetime.utcnow(),
        )
        db.add(biometria)

    db.flush()

    registrar_auditoria(
        db,
        id_usuario=id_usuario,
        acao=acao_auditoria,
        entidade_afetada="biometria",
        id_registro_afetado=str(biometria.id_biometria),
        resultado="SUCESSO",
        detalhes={
            "versao_modelo": versao_modelo,
            "dimensoes_vetor": len(vetor_128d),
        },
    )

    db.commit()
    db.refresh(biometria)
    return biometria


def criar_novo_usuario(
    db: Session,
    nome: str,
    cpf: str,
    senha_plana: str,
    matricula: str,
    cargo_id: int,
    divisao_id: int,
    nivel_acesso: int,
    vetor_biometrico: Optional[List[float]] = None,
) -> Usuario:
    """
    Cadastra um novo servidor na tabela usuario e, opcionalmente, persiste
    seu vetor facial de 128D na tabela biometria.
    """
    cpf_limpo = re.sub(r"\D", "", cpf)

    existente_cpf = db.query(Usuario).filter(Usuario.cpf == cpf_limpo).first()
    if existente_cpf:
        raise ValueError("CPF_ALREADY_EXISTS")

    existente_mat = db.query(Usuario).filter(Usuario.matricula == matricula.strip()).first()
    if existente_mat:
        raise ValueError("MATRICULA_ALREADY_EXISTS")

    hash_senha = gerar_hash_senha(senha_plana)
    usuario = Usuario(
        nome=nome.strip(),
        cpf=cpf_limpo,
        hash_senha=hash_senha,
        matricula=matricula.strip(),
        id_cargo=cargo_id,
        id_divisao=divisao_id,
        id_nivel_acesso=nivel_acesso,
        status_conta="ATIVA",
    )
    db.add(usuario)
    db.flush()

    if vetor_biometrico:
        biometria = Biometria(
            id_usuario=usuario.id_usuario,
            modelo_facial=vetor_biometrico,
            versao_modelo="dlib_resnet34_v1",
        )
        db.add(biometria)
        db.flush()

    registrar_auditoria(
        db,
        id_usuario=usuario.id_usuario,
        acao="CADASTRO_USUARIO",
        entidade_afetada="usuario",
        id_registro_afetado=str(usuario.id_usuario),
        resultado="SUCESSO",
        detalhes={
            "matricula": usuario.matricula,
            "id_cargo": cargo_id,
            "id_divisao": divisao_id,
            "nivel_acesso": nivel_acesso,
            "biometria_cadastrada": vetor_biometrico is not None,
        },
    )

    db.commit()
    return buscar_usuario_por_id(db, usuario.id_usuario) or usuario


# =============================================================================
# 7. OPERAÇÕES DO COFRE DE TOXINAS E DOCUMENTOS TÉCNICOS
# =============================================================================

def extrair_nivel_requerido_toxina(classificacao: Optional[str]) -> int:
    """Infere o nível de acesso requerido (1, 2 ou 3) a partir da classificação da toxina."""
    if not classificacao:
        return 1
    c = classificacao.lower()
    if "3" in c or "catastr" in c or "ministerial" in c:
        return 3
    if "2" in c or "cr" in c or "paralisante" in c:
        return 2
    return 1


def listar_toxinas(
    db: Session,
    nivel_usuario: int,
) -> List[Toxina]:
    """
    Retorna a lista de toxinas do cofre com eager loading da divisão e criador,
    filtradas conforme o nível hierárquico RBAC do usuário solicitante:
      - Nível 1: toxinas de nível 1;
      - Nível 2: toxinas de nível 1 e 2;
      - Nível 3: todas as toxinas (níveis 1, 2 e 3).
    """
    todas = (
        db.query(Toxina)
        .options(
            joinedload(Toxina.divisao),
            joinedload(Toxina.criador),
        )
        .order_by(Toxina.id_toxina.asc())
        .all()
    )

    resultado: List[Toxina] = []
    for t in todas:
        nivel_req = extrair_nivel_requerido_toxina(t.classificacao)
        if nivel_req <= nivel_usuario:
            resultado.append(t)

    return resultado


def cadastrar_toxina(
    db: Session,
    nome: str,
    descricao: Optional[str],
    classificacao: Optional[str],
    observacoes: Optional[str],
    id_divisao_responsavel: int,
    id_criador: int,
) -> Toxina:
    """Insere um novo registro de substância controlada na tabela toxina."""
    toxina = Toxina(
        nome=nome.strip(),
        descricao=descricao,
        classificacao=classificacao,
        observacoes=observacoes,
        id_divisao_responsavel=id_divisao_responsavel,
        id_criador=id_criador,
    )
    db.add(toxina)
    db.flush()

    registrar_auditoria(
        db,
        id_usuario=id_criador,
        acao="CADASTRO_TOXINA",
        entidade_afetada="toxina",
        id_registro_afetado=str(toxina.id_toxina),
        resultado="SUCESSO",
        detalhes={"nome": toxina.nome, "classificacao": toxina.classificacao},
    )

    db.commit()
    db.refresh(toxina)
    return toxina


def listar_documentos(
    db: Session,
    id_toxina: Optional[int] = None,
) -> List[Documento]:
    """Lista documentos técnicos associados ao cofre e suas divisões."""
    query = db.query(Documento).options(
        joinedload(Documento.divisao),
        joinedload(Documento.criador),
        joinedload(Documento.toxina),
    )
    if id_toxina is not None:
        query = query.filter(Documento.id_toxina == id_toxina)
    return query.order_by(Documento.id_documento.asc()).all()


def cadastrar_documento(
    db: Session,
    titulo: str,
    descricao: Optional[str],
    tipo_documento: Optional[str],
    local_arquivo: Optional[str],
    hash_arquivo: Optional[str],
    id_divisao_responsavel: int,
    id_criador: int,
    id_toxina: Optional[int] = None,
) -> Documento:
    """Insere documento técnico no banco de dados e registra auditoria."""
    doc = Documento(
        titulo=titulo.strip(),
        descricao=descricao,
        tipo_documento=tipo_documento,
        local_arquivo=local_arquivo,
        hash_arquivo=hash_arquivo,
        id_toxina=id_toxina,
        id_divisao_responsavel=id_divisao_responsavel,
        id_criador=id_criador,
    )
    db.add(doc)
    db.flush()

    registrar_auditoria(
        db,
        id_usuario=id_criador,
        acao="CADASTRO_DOCUMENTO",
        entidade_afetada="documento",
        id_registro_afetado=str(doc.id_documento),
        resultado="SUCESSO",
        detalhes={"titulo": doc.titulo, "id_toxina": id_toxina},
    )

    db.commit()
    db.refresh(doc)
    return doc
