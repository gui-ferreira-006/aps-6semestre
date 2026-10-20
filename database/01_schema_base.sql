-- ==============================================================================
-- 01_schema_base.sql - F.A.C.A. (Frente de Autenticação e Controle de Acesso)
-- Script Base Oficial do Banco de Dados aps_biometria (Modelagem 3FN)
-- Executado automaticamente no primeiro boot do contêiner MySQL 8.0
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS aps_biometria
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;

USE aps_biometria;

-- 1. DIVISOES
CREATE TABLE divisao (
    id_divisao BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao VARCHAR(255),
    ativa BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- 2. CARGOS
-- Cargo e nivel de acesso sao conceitos diferentes.
CREATE TABLE cargo (
    id_cargo BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao VARCHAR(255),
    ativo BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- 3. NIVEIS DE ACESSO
CREATE TABLE nivel_acesso (
    id_nivel_acesso TINYINT UNSIGNED PRIMARY KEY,
    nome VARCHAR(50) NOT NULL UNIQUE,
    descricao VARCHAR(255),
    CONSTRAINT chk_nivel
        CHECK (id_nivel_acesso IN (1, 2, 3))
) ENGINE=InnoDB;

-- 4. USUARIOS
-- O ID interno e a chave primaria.
-- Matricula e CPF possuem unicidade.
CREATE TABLE usuario (
    id_usuario BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    matricula VARCHAR(30) NOT NULL UNIQUE,
    cpf CHAR(11) NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL,
    hash_senha VARCHAR(255) NOT NULL,

    id_cargo BIGINT UNSIGNED NOT NULL,
    id_nivel_acesso TINYINT UNSIGNED NOT NULL,
    id_divisao BIGINT UNSIGNED NOT NULL,

    status_conta ENUM('ATIVA', 'DESATIVADA')
        NOT NULL DEFAULT 'ATIVA',

    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuario_cargo
        FOREIGN KEY (id_cargo)
        REFERENCES cargo(id_cargo)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT fk_usuario_nivel
        FOREIGN KEY (id_nivel_acesso)
        REFERENCES nivel_acesso(id_nivel_acesso)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT fk_usuario_divisao
        FOREIGN KEY (id_divisao)
        REFERENCES divisao(id_divisao)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    INDEX idx_usuario_divisao (id_divisao),
    INDEX idx_usuario_nivel (id_nivel_acesso),
    INDEX idx_usuario_status (status_conta)
) ENGINE=InnoDB;

-- 5. TOXINAS
-- A autoria e a divisao responsavel sao independentes.
CREATE TABLE toxina (
    id_toxina BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    classificacao VARCHAR(100),
    observacoes TEXT,

    id_divisao_responsavel BIGINT UNSIGNED NOT NULL,
    id_criador BIGINT UNSIGNED NOT NULL,

    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_toxina_divisao
        FOREIGN KEY (id_divisao_responsavel)
        REFERENCES divisao(id_divisao)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT fk_toxina_criador
        FOREIGN KEY (id_criador)
        REFERENCES usuario(id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    INDEX idx_toxina_divisao (id_divisao_responsavel),
    INDEX idx_toxina_criador (id_criador),
    INDEX idx_toxina_nome (nome)
) ENGINE=InnoDB;

-- 6. DOCUMENTOS
-- Cada documento pode estar associado a zero ou uma toxina.
-- A divisao responsavel e independente da toxina associada.
CREATE TABLE documento (
    id_documento BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    tipo_documento VARCHAR(80),
    local_arquivo VARCHAR(500),
    hash_arquivo CHAR(64),

    id_toxina BIGINT UNSIGNED NULL,
    id_divisao_responsavel BIGINT UNSIGNED NOT NULL,
    id_criador BIGINT UNSIGNED NOT NULL,

    data_criacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_documento_toxina
        FOREIGN KEY (id_toxina)
        REFERENCES toxina(id_toxina)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT fk_documento_divisao
        FOREIGN KEY (id_divisao_responsavel)
        REFERENCES divisao(id_divisao)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    CONSTRAINT fk_documento_criador
        FOREIGN KEY (id_criador)
        REFERENCES usuario(id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    INDEX idx_documento_toxina (id_toxina),
    INDEX idx_documento_divisao (id_divisao_responsavel),
    INDEX idx_documento_criador (id_criador)
) ENGINE=InnoDB;

-- 7. BIOMETRIA
-- Um usuario pode ter zero ou uma biometria atual.
-- UNIQUE em id_usuario impede duas linhas para o mesmo usuario.
CREATE TABLE biometria (
    id_biometria BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_usuario BIGINT UNSIGNED NOT NULL UNIQUE,
    modelo_facial JSON NOT NULL,
    versao_modelo VARCHAR(50) NOT NULL,

    data_cadastro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_biometria_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- 8. TENTATIVAS DE AUTENTICACAO
-- Tambem permite registrar tentativas com identificadores
-- que nao correspondem a usuarios cadastrados.
CREATE TABLE tentativa_autenticacao (
    id_tentativa BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_usuario BIGINT UNSIGNED NULL,

    tipo_identificador ENUM('CPF', 'MATRICULA') NOT NULL,
    identificador_protegido VARCHAR(255) NOT NULL,

    etapa ENUM(
        'CREDENCIAIS',
        'BIOMETRIA',
        'CONCLUSAO'
    ) NOT NULL,

    resultado ENUM(
        'SUCESSO',
        'FALHA',
        'NEGADO',
        'BLOQUEADO'
    ) NOT NULL,

    motivo VARCHAR(120),
    data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_tentativa_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    INDEX idx_tentativa_usuario_data (id_usuario, data_hora),
    INDEX idx_tentativa_identificador (
        identificador_protegido, data_hora
    ),
    INDEX idx_tentativa_resultado (resultado, data_hora)
) ENGINE=InnoDB;

-- 9. BLOQUEIOS TEMPORARIOS DE LOGIN
-- O backend controla as cinco falhas consecutivas e o prazo.
CREATE TABLE bloqueio_login (
    id_bloqueio BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    tipo_identificador ENUM('CPF', 'MATRICULA') NOT NULL,
    identificador_protegido VARCHAR(255) NOT NULL,

    data_hora_inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_hora_fim DATETIME NOT NULL,

    motivo VARCHAR(120) NOT NULL DEFAULT 'LIMITE_TENTATIVAS',
    ativo BOOLEAN NOT NULL DEFAULT TRUE,

    id_tentativa_origem BIGINT UNSIGNED NULL,

    CONSTRAINT chk_bloqueio_periodo
        CHECK (data_hora_fim > data_hora_inicio),

    CONSTRAINT fk_bloqueio_tentativa
        FOREIGN KEY (id_tentativa_origem)
        REFERENCES tentativa_autenticacao(id_tentativa)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    INDEX idx_bloqueio_consulta (
        identificador_protegido, ativo, data_hora_fim
    )
) ENGINE=InnoDB;

-- 10. AUDITORIA
-- Registra alteracoes e operacoes relevantes.
-- Nao armazene senhas nem modelos faciais nos detalhes.
CREATE TABLE auditoria (
    id_auditoria BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_usuario BIGINT UNSIGNED NULL,

    acao VARCHAR(100) NOT NULL,
    entidade_afetada VARCHAR(80) NOT NULL,
    id_registro_afetado VARCHAR(80),

    resultado ENUM('SUCESSO', 'FALHA', 'NEGADO') NOT NULL,
    detalhes JSON,

    data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_auditoria_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario(id_usuario)
        ON DELETE RESTRICT ON UPDATE RESTRICT,

    INDEX idx_auditoria_usuario_data (id_usuario, data_hora),
    INDEX idx_auditoria_acao_data (acao, data_hora),
    INDEX idx_auditoria_entidade (
        entidade_afetada, id_registro_afetado
    )
) ENGINE=InnoDB;

-- 11. DADOS INICIAIS DE REFERENCIA
INSERT INTO nivel_acesso
    (id_nivel_acesso, nome, descricao)
VALUES
    (1, 'Administrador basico',
     'Consulta dashboards, estatisticas e relatorios.'),
    (2, 'Diretor de divisao',
     'Consulta e gerencia registros da propria divisao.'),
    (3, 'Ministro',
     'Gerencia usuarios, niveis de acesso e auditoria.');

INSERT INTO divisao (nome, descricao)
VALUES
    ('Toxicologia', 'Responsavel por registros de toxinas.'),
    ('Documentacao', 'Responsavel por documentos tecnicos.');

INSERT INTO cargo (nome, descricao)
VALUES
    ('Administrador', 'Cargo administrativo.'),
    ('Diretor de divisao', 'Cargo de direcao.'),
    ('Ministro', 'Cargo de autoridade maxima.');
