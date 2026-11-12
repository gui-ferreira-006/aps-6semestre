"""
==============================================================================
F.A.C.A. — Frente de Autenticação e Controle de Acesso
Processamento de Imagem e Visão Computacional (PIVC) — APS 2026/2 (UNIP)
Bateria de Testes E2E com MySQL 8.0 Real no Docker (test_e2e_mysql.py)
==============================================================================

Valida ponta a ponta todas as regras de negócio e persistência exigidas:
  1. Health check da API com verificação de conectividade SQL;
  2. Consulta protegida ao cofre sem token (401);
  3. 5 tentativas falhas consecutivas de credenciais gerando bloqueio temporário (403);
  4. Bloqueio ativo persistido na tabela bloqueio_login e evento em auditoria;
  5. Desbloqueio administrativo de emergência (POST /usuarios/{cpf}/desbloquear);
  6. Login bem-sucedido com enrollment biométrico 128D on-the-fly na tabela biometria;
  7. Segundo login com o mesmo rosto (verificação 1:1 contra o modelo facial persistido);
  8. Tentativa com rosto divergente gerando 401 FACE_NOT_RECOGNIZED;
  9. Consulta ao cofre de toxinas com filtragem hierárquica RBAC (Níveis 1, 2 e 3);
  10. Cadastro de novo servidor público e biometria 128D (POST /cadastrar).
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Adiciona a raiz do projeto ao sys.path
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import database
import models

API_URL = "http://localhost:8000"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
IMG_OPERADOR1 = ASSETS_DIR / "face_operador1.jpg"
IMG_DIVERGENTE = ASSETS_DIR / "face_divergente.jpg"


def _carregar_base64(caminho: Path) -> str:
    with open(caminho, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _requisicao_http(
    metodo: str,
    endpoint: str,
    payload: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Executa requisição HTTP retornando status_code e corpo JSON decodificado."""
    url = f"{API_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=metodo)

    try:
        with urllib.request.urlopen(req) as resp:
            corpo = resp.read().decode("utf-8")
            return resp.status, json.loads(corpo) if corpo else {}
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8")
        try:
            dados = json.loads(corpo)
        except Exception:
            dados = {"erro_bruto": corpo}
        return e.code, dados


def test_1_health_check_mysql() -> None:
    print("\n[TESTE 1] Health Check da API e Conectividade MySQL...")
    status, dados = _requisicao_http("GET", "/ping")
    assert status == 200, f"Esperado status 200, recebido {status}"
    assert dados.get("status") == "ok", "Status do ping deve ser 'ok'"
    assert "MySQL conectado" in dados.get("mensagem", ""), "Mensagem deve confirmar MySQL conectado"
    print("  -> OK: /ping respondeu 200 com 'MySQL conectado'.")


def test_2_cofre_sem_token() -> None:
    print("\n[TESTE 2] Consulta ao Cofre sem Token (Autenticação Obrigatória)...")
    status, dados = _requisicao_http("GET", "/toxinas")
    assert status == 401, f"Esperado status 401, recebido {status}"
    assert dados.get("erro", {}).get("codigo") == "TOKEN_INVALID_OR_EXPIRED"
    print("  -> OK: /toxinas bloqueou acesso não autenticado com 401 TOKEN_INVALID_OR_EXPIRED.")


def test_3_cinco_falhas_e_bloqueio_automatico() -> None:
    print("\n[TESTE 3] 5 Falhas de Senha Consecutivas e Bloqueio Automático...")
    cpf = "12345678900"
    b64_foto = _carregar_base64(IMG_OPERADOR1)

    # Garante que não há bloqueios residuais de execuções anteriores
    _requisicao_http("POST", f"/usuarios/{cpf}/desbloquear")

    # 4 falhas consecutivas de senha -> HTTP 401
    for i in range(1, 5):
        status, dados = _requisicao_http(
            "POST",
            "/autenticar",
            {"cpf": cpf, "senha": f"SenhaErrada_{i}", "imagem_base64": b64_foto},
        )
        assert status == 401, f"Tentativa {i}: esperado 401, recebido {status}: {dados}"
        assert dados.get("bloqueado") is False
        assert dados.get("tentativas_restantes") == (5 - i)
        print(f"  -> Tentativa {i}/5 falhou corretamente: {dados.get('tentativas_restantes')} restantes.")

    # 5ª falha -> Gatilho de Bloqueio Automático -> HTTP 403
    status, dados = _requisicao_http(
        "POST",
        "/autenticar",
        {"cpf": cpf, "senha": "SenhaErrada_5", "imagem_base64": b64_foto},
    )
    assert status == 403, f"5ª tentativa deve retornar 403, recebido {status}: {dados}"
    assert dados.get("bloqueado") is True
    assert dados.get("erro", {}).get("codigo") == "ACCOUNT_LOCKED"
    print("  -> OK: 5ª falha disparou 403 ACCOUNT_LOCKED.")

    # Validação Direta no Banco de Dados MySQL
    db = database.SessionLocal()
    try:
        bloqueios = (
            db.query(models.BloqueioLogin)
            .filter(models.BloqueioLogin.ativo.is_(True))
            .all()
        )
        assert len(bloqueios) >= 1, "Deve existir ao menos um registro ativo na tabela bloqueio_login"

        auditorias = (
            db.query(models.Auditoria)
            .filter(models.Auditoria.acao == "BLOQUEIO_CONTA")
            .all()
        )
        assert len(auditorias) >= 1, "Deve existir log na tabela auditoria com acao='BLOQUEIO_CONTA'"
        print("  -> OK: Registro em bloqueio_login e auditoria confirmados no MySQL.")
    finally:
        db.close()


def test_4_tentativa_durante_bloqueio() -> None:
    print("\n[TESTE 4] Tentativa de Autenticação com Conta Bloqueada...")
    cpf = "12345678900"
    b64_foto = _carregar_base64(IMG_OPERADOR1)

    # Mesmo com a senha correta, a conta está bloqueada!
    status, dados = _requisicao_http(
        "POST",
        "/autenticar",
        {"cpf": cpf, "senha": "Faca@2026", "imagem_base64": b64_foto},
    )
    assert status == 403, f"Conta bloqueada deve receber 403, recebido {status}"
    assert dados.get("bloqueado") is True
    print("  -> OK: Acesso barrado preventivamente (403) durante período de bloqueio.")


def test_5_desbloqueio_administrativo() -> None:
    print("\n[TESTE 5] Desbloqueio Administrativo de Emergência...")
    cpf = "12345678900"
    status, dados = _requisicao_http("POST", f"/usuarios/{cpf}/desbloquear")
    assert status == 200, f"Esperado 200 no desbloqueio, recebido {status}: {dados}"
    assert dados.get("sucesso") is True
    assert dados.get("bloqueios_desativados", 0) >= 1

    # Validação no MySQL
    db = database.SessionLocal()
    try:
        bloqueio_recente = (
            db.query(models.BloqueioLogin)
            .order_by(models.BloqueioLogin.id_bloqueio.desc())
            .first()
        )
        assert bloqueio_recente is not None
        assert bloqueio_recente.ativo is False, "O bloqueio deve estar desativado (ativo=False)"

        auditoria_desbloqueio = (
            db.query(models.Auditoria)
            .filter(models.Auditoria.acao == "DESBLOQUEIO_CONTA")
            .first()
        )
        assert auditoria_desbloqueio is not None, "Auditoria de desbloqueio deve existir"
        print("  -> OK: Bloqueio desativado no MySQL e log registrado em auditoria.")
    finally:
        db.close()


def test_6_enrollment_onthefly_e_login_sucesso() -> str:
    print("\n[TESTE 6] Primeiro Login do Operador 1 com Enrollment Biométrico On-the-Fly...")
    cpf = "12345678900"
    b64_foto = _carregar_base64(IMG_OPERADOR1)

    # Valida estado prévio no MySQL: biometria deve ser None no seed
    db = database.SessionLocal()
    try:
        u = db.query(models.Usuario).filter_by(cpf=cpf).first()
        assert u is not None
        # Remove biometria anterior se houver
        if u.biometria:
            db.delete(u.biometria)
            db.commit()
    finally:
        db.close()

    status, dados = _requisicao_http(
        "POST",
        "/autenticar",
        {"cpf": cpf, "senha": "Faca@2026", "imagem_base64": b64_foto},
    )
    assert status == 200, f"Esperado status 200, recebido {status}: {dados}"
    assert dados.get("sucesso") is True
    assert "Biometria de referência vinculada" in dados.get("mensagem", "")

    token = dados.get("token")
    assert token and token.startswith("mock-jwt-faca-"), "Deve emitir token de sessão"

    usuario = dados.get("usuario", {})
    assert usuario.get("nome") == "Guilherme Ferreira"
    assert usuario.get("cargo") == "Administrador"
    assert usuario.get("nivel_acesso") == 1
    print(f"  -> OK: Operador 1 autenticado com sucesso! Token: {token[:25]}...")

    # Validação Direta no Banco de Dados MySQL: biometria persistida
    db = database.SessionLocal()
    try:
        u = db.query(models.Usuario).filter_by(cpf=cpf).first()
        assert u is not None
        assert u.biometria is not None, "Tabela biometria DEVE conter o registro do operador após o 1º login"
        assert len(u.biometria.modelo_facial) == 128, "Modelo facial gravado deve ter 128 floats"
        assert u.biometria.versao_modelo == "dlib_resnet34_v1"

        auditoria_enroll = (
            db.query(models.Auditoria)
            .filter(models.Auditoria.acao == "ENROLLMENT_BIOMETRICO")
            .first()
        )
        assert auditoria_enroll is not None, "Log de ENROLLMENT_BIOMETRICO deve estar gravado no MySQL"
        print("  -> OK: Vetor 128D e log de enrollment gravados com sucesso na tabela biometria do MySQL.")
    finally:
        db.close()

    return token


def test_7_segundo_login_mesmo_rosto() -> None:
    print("\n[TESTE 7] Segundo Login do Operador 1 (Verificação 1:1 contra Modelo no MySQL)...")
    cpf = "12345678900"
    b64_foto = _carregar_base64(IMG_OPERADOR1)

    status, dados = _requisicao_http(
        "POST",
        "/autenticar",
        {"cpf": cpf, "senha": "Faca@2026", "imagem_base64": b64_foto},
    )
    assert status == 200, f"Esperado status 200, recebido {status}: {dados}"
    assert dados.get("sucesso") is True

    bio = dados.get("biometria", {})
    dist = bio.get("distancia_euclidiana", 1.0)
    conf = bio.get("confianca_percentual", 0.0)
    assert bio.get("reconhecido") is True
    assert dist < 0.20, f"Distância euclidiana com mesmo rosto deve ser baixa ({dist})"
    print(f"  -> OK: Match facial 1:1 confirmado! Distância: {dist:.4f} | Confiança: {conf:.1f}%")


def test_8_login_rosto_divergente() -> None:
    print("\n[TESTE 8] Tentativa de Login com Rosto Divergente (Acesso Negado)...")
    cpf = "12345678900"
    b64_divergente = _carregar_base64(IMG_DIVERGENTE)

    status, dados = _requisicao_http(
        "POST",
        "/autenticar",
        {"cpf": cpf, "senha": "Faca@2026", "imagem_base64": b64_divergente},
    )
    assert status == 401, f"Rosto divergente deve retornar 401, recebido {status}: {dados}"
    assert dados.get("erro", {}).get("codigo") == "FACE_NOT_RECOGNIZED"

    # Confirma tentativa gravada no MySQL
    db = database.SessionLocal()
    try:
        tentativa = (
            db.query(models.TentativaAutenticacao)
            .filter(models.TentativaAutenticacao.resultado == "NEGADO")
            .order_by(models.TentativaAutenticacao.id_tentativa.desc())
            .first()
        )
        assert tentativa is not None
        assert tentativa.etapa == "BIOMETRIA"
        print("  -> OK: Rosto divergente rejeitado com 401 FACE_NOT_RECOGNIZED e gravado no MySQL.")
    finally:
        db.close()


def test_9_consulta_cofre_rbac(token_n1: str) -> None:
    print("\n[TESTE 9] Consulta ao Cofre de Toxinas com Filtragem RBAC...")

    # 1. Consulta com Token de Nível 1 (Guilherme Ferreira)
    status, dados_n1 = _requisicao_http("GET", "/toxinas", token=token_n1)
    assert status == 200, f"Esperado status 200, recebido {status}: {dados_n1}"
    assert dados_n1.get("usuario_solicitante", {}).get("nivel_acesso") == 1
    itens_n1 = dados_n1.get("itens", [])
    assert len(itens_n1) == 1, f"Nível 1 deve ver exatamente 1 toxina, recebido {len(itens_n1)}"
    assert itens_n1[0]["detalhes_confidenciais"] is None, "Dados confidenciais devem ser None para Nível 1"
    print(f"  -> OK: Operador Nível 1 visualizou apenas {len(itens_n1)} toxina de Nível 1 sem segredos.")

    # 2. Autentica Operador Nível 2 (Dra. Júlia Fernandes)
    b64_foto = _carregar_base64(IMG_DIVERGENTE)
    status, resp_n2 = _requisicao_http(
        "POST",
        "/autenticar",
        {"cpf": "98765432100", "senha": "Faca@2026", "imagem_base64": b64_foto},
    )
    assert status == 200, f"Falha no login Nível 2: {resp_n2}"
    token_n2 = resp_n2.get("token")

    status, dados_n2 = _requisicao_http("GET", "/toxinas", token=token_n2)
    assert status == 200
    itens_n2 = dados_n2.get("itens", [])
    assert len(itens_n2) == 3, f"Nível 2 deve ver toxinas de nível 1 e 2 (total 3), recebido {len(itens_n2)}"
    assert itens_n2[1]["detalhes_confidenciais"] is not None, "Nível 2 deve ver detalhes de toxinas de nível 2"
    print(f"  -> OK: Diretora Nível 2 visualizou {len(itens_n2)} toxinas (Nível 1 + Nível 2 com detalhes).")

    # 3. Autentica Operador Nível 3 (Ministro do Meio Ambiente)
    status, resp_n3 = _requisicao_http(
        "POST",
        "/autenticar",
        {"cpf": "11122233344", "senha": "Faca@2026", "imagem_base64": b64_foto},
    )
    assert status == 200, f"Falha no login Nível 3: {resp_n3}"
    token_n3 = resp_n3.get("token")

    status, dados_n3 = _requisicao_http("GET", "/toxinas", token=token_n3)
    assert status == 200
    itens_n3 = dados_n3.get("itens", [])
    assert len(itens_n3) == 4, f"Nível 3 deve ver todas as 4 toxinas do cofre, recebido {len(itens_n3)}"
    assert itens_n3[3]["detalhes_confidenciais"] is not None
    print(f"  -> OK: Ministro Nível 3 tem acesso total às {len(itens_n3)} toxinas do cofre (incluindo Quimera FX-99).")


def test_10_cadastro_novo_servidor() -> None:
    print("\n[TESTE 10] Cadastro de Novo Servidor e Biometria no MySQL...")
    cpf_novo = "55566677788"
    mat_nova = "MMA-2026-999"
    b64_foto = _carregar_base64(IMG_OPERADOR1)

    # Limpa eventual usuário de teste anterior
    db = database.SessionLocal()
    try:
        existente = db.query(models.Usuario).filter_by(cpf=cpf_novo).first()
        if existente:
            db.delete(existente)
            db.commit()
    finally:
        db.close()

    status, dados = _requisicao_http(
        "POST",
        "/cadastrar",
        {
            "nome": "Agente Teste PIVC",
            "cpf": cpf_novo,
            "senha": "Faca@2026",
            "matricula": mat_nova,
            "cargo_id": 1,
            "divisao_id": 1,
            "nivel_acesso": 1,
            "imagem_base64": b64_foto,
        },
    )
    assert status == 201, f"Esperado 201 Created, recebido {status}: {dados}"
    assert dados.get("sucesso") is True
    novo_id = dados.get("usuario", {}).get("id")
    print(f"  -> OK: Novo servidor cadastrado com sucesso! ID: {novo_id}")

    # Validação no MySQL
    db = database.SessionLocal()
    try:
        user_db = db.query(models.Usuario).filter_by(id_usuario=novo_id).first()
        assert user_db is not None
        assert user_db.biometria is not None
        assert len(user_db.biometria.modelo_facial) == 128
        print("  -> OK: Dados do novo servidor e vetor biométrico 128D confirmados no MySQL.")
    finally:
        db.close()

    # Tentativa de duplicidade de CPF -> HTTP 409
    status, dados_duplicado = _requisicao_http(
        "POST",
        "/cadastrar",
        {
            "nome": "Agente Duplicado",
            "cpf": cpf_novo,
            "senha": "Faca@2026",
            "matricula": "OUTRA-MATRICULA",
            "cargo_id": 1,
            "divisao_id": 1,
            "nivel_acesso": 1,
            "imagem_base64": b64_foto,
        },
    )
    assert status == 409, f"Duplicação de CPF deve retornar 409, recebido {status}"
    assert dados_duplicado.get("erro", {}).get("codigo") == "CPF_ALREADY_EXISTS"
    print("  -> OK: Conflito de unicidade de CPF validado com 409 CPF_ALREADY_EXISTS.")


def executar_bateria_completa() -> None:
    print("=" * 78)
    print("BATERIA DE TESTES E2E — INTEGRAÇÃO F.A.C.A. + MYSQL 8.0 DOCKER")
    print("=" * 78)

    inicio = time.time()
    test_1_health_check_mysql()
    test_2_cofre_sem_token()
    test_3_cinco_falhas_e_bloqueio_automatico()
    test_4_tentativa_durante_bloqueio()
    test_5_desbloqueio_administrativo()
    token_n1 = test_6_enrollment_onthefly_e_login_sucesso()
    test_7_segundo_login_mesmo_rosto()
    test_8_login_rosto_divergente()
    test_9_consulta_cofre_rbac(token_n1)
    test_10_cadastro_novo_servidor()

    duracao = time.time() - inicio
    print("\n" + "=" * 78)
    print(f"TODOS OS 10 TESTES DE INTEGRAÇÃO PASSARAM COM SUCESSO! (Tempo: {duracao:.2f}s)")
    print("=" * 78)


if __name__ == "__main__":
    executar_bateria_completa()
