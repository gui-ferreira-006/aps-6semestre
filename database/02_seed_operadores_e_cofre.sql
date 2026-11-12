-- ==============================================================================
-- 02_seed_operadores_e_cofre.sql - F.A.C.A. (Frente de Autenticação e Controle de Acesso)
-- Script de Carga Inicial / Seeds (Operadores do Roteiro, Cofre de Toxinas e Documentos)
-- Executado automaticamente após 01_schema_base.sql
-- ==============================================================================

USE aps_biometria;

-- ------------------------------------------------------------------------------
-- 1. OPERADORES OFICIAIS DO ROTEIRO (MFA RBAC Níveis 1, 2 e 3)
-- Importante: Os operadores NÃO possuem registro na tabela biometria neste seed,
-- permitindo o enrollment biométrico 128D on-the-fly no primeiro acesso via webcam.
-- Hash gerado com PBKDF2-HMAC-SHA256 para a senha oficial: Faca@2026
-- ------------------------------------------------------------------------------

INSERT INTO usuario (
    id_usuario,
    matricula,
    cpf,
    nome,
    hash_senha,
    id_cargo,
    id_nivel_acesso,
    id_divisao,
    status_conta
) VALUES
(
    1,
    'MMA-2026-001',
    '12345678900',
    'Guilherme Ferreira',
    'pbkdf2_sha256$100000$facasalt20260000$61d3cafb71ca4a91bd52a791646d48172da5f4fcc547aec5062b68da49efc321',
    1, -- Administrador
    1, -- Nível 1 (Administrador básico)
    1, -- Toxicologia
    'ATIVA'
),
(
    2,
    'MMA-2026-002',
    '98765432100',
    'Dra. Júlia Fernandes',
    'pbkdf2_sha256$100000$facasalt20260000$61d3cafb71ca4a91bd52a791646d48172da5f4fcc547aec5062b68da49efc321',
    2, -- Diretor de divisao
    2, -- Nível 2 (Diretor de divisao)
    1, -- Toxicologia
    'ATIVA'
),
(
    3,
    'MMA-2026-003',
    '11122233344',
    'Ministro do Meio Ambiente',
    'pbkdf2_sha256$100000$facasalt20260000$61d3cafb71ca4a91bd52a791646d48172da5f4fcc547aec5062b68da49efc321',
    3, -- Ministro
    3, -- Nível 3 (Ministro)
    2, -- Documentacao
    'ATIVA'
),
(
    4,
    'MMA-TI-000',
    '00000000000',
    'Administrador Geral (T.I.)',
    'pbkdf2_sha256$100000$facasalt20260000$61d3cafb71ca4a91bd52a791646d48172da5f4fcc547aec5062b68da49efc321',
    1, -- Administrador
    3, -- Nível 3 (Acesso Total / T.I.)
    2, -- Documentacao / Governança
    'ATIVA'
);

-- ------------------------------------------------------------------------------
-- 2. COFRE DE TOXINAS (Amostras Biológicas e Químicas Controladas)
-- Pelo menos 4 substâncias classificadas por periculosidade e risco de contenção
-- ------------------------------------------------------------------------------

INSERT INTO toxina (
    id_toxina,
    nome,
    descricao,
    classificacao,
    observacoes,
    id_divisao_responsavel,
    id_criador
) VALUES
(
    1,
    'Toxina Botulínica (Amostra Controle)',
    'Neurotoxina bacteriana produzida por Clostridium botulinum. Bloqueia a liberação sináptica de acetilcolina.',
    'Nível 1 - Moderado / Monitorado',
    'Armazenamento em câmara criogênica a 4°C. Contenção BSL-2. Protocolo de neutralização: Autoclave 121°C por 30min ou solução de hipoclorito a 0.5%.',
    1, -- Toxicologia
    1  -- Guilherme Ferreira
),
(
    2,
    'Saxitoxina Sintetizada',
    'Neurotoxina paralisante potente purificada de florações de dinoflagelados marinhos. Bloqueadora seletiva de canais de sódio.',
    'Nível 2 - Crítico / Neurotoxina Paralisante',
    'Cofre Subterrâneo B-12. Temperatura de conservação: -20°C. Contenção BSL-3. Neutralização por agentes alcalinos concentrados sob agitação.',
    1, -- Toxicologia
    2  -- Dra. Júlia Fernandes
),
(
    3,
    'Ricina Altamente Purificada',
    'Toxalbumina citotóxica extraída de sementes de Ricinus communis. Inativação irreversível de ribossomos e síntese proteica.',
    'Nível 2 - Crítico / Citotoxina Letal',
    'Armazenada em dessecador com atmosfera inerte de nitrogênio. Contenção BSL-3. Neutralização por hipoclorito de sódio 5% durante 60 minutos.',
    1, -- Toxicologia
    2  -- Dra. Júlia Fernandes
),
(
    4,
    'Quimera Biológica FX-99 (Agente Letal Nível 4)',
    'Agente patogênico bioengenheirado com virulência aerossolizada e toxicidade multiorgânica catastrófica.',
    'Nível 3 - Catastrófico Global / Acesso Restrito Ministerial',
    'Câmara de Vácuo Central - Cofre Ômega (-80°C). Blindagem reforçada contra radiação e sismos. Autodestruição acionada exclusivamente por chave dupla ministerial.',
    1, -- Toxicologia
    3  -- Ministro do Meio Ambiente
);

-- ------------------------------------------------------------------------------
-- 3. DOCUMENTOS TÉCNICOS ASSOCIADOS AO COFRE E DIVISÕES
-- ------------------------------------------------------------------------------

INSERT INTO documento (
    id_documento,
    titulo,
    descricao,
    tipo_documento,
    local_arquivo,
    hash_arquivo,
    id_toxina,
    id_divisao_responsavel,
    id_criador
) VALUES
(
    1,
    'POP-TOX-001 - Protocolo de Contenção e Manuseio BSL-2',
    'Procedimento Operacional Padrão regulamentando amostragem e descontaminação de Toxina Botulínica.',
    'Procedimento Operacional Padrão',
    '/cofre/docs/pop_botulinica_v2.pdf',
    'a3c8e5d2b1f47890123456789abcdef0123456789abcdef0123456789abcdef0',
    1, -- Toxina Botulínica
    1, -- Toxicologia
    1  -- Guilherme Ferreira
),
(
    2,
    'Laudo Pericial de Cromatografia Líquida - Lote STX-2026',
    'Ensaio por HPLC-MS atestando conformidade estrutural e índice de pureza da Saxitoxina.',
    'Laudo Pericial',
    '/cofre/docs/laudo_saxitoxina_2026.pdf',
    'b4d9f6e3c2a5890123456789abcdef0123456789abcdef0123456789abcdef01',
    2, -- Saxitoxina
    1, -- Toxicologia
    2  -- Dra. Júlia Fernandes
),
(
    3,
    'Diretriz de Segurança Biológica e Mitigação de Vencimento - Ricina',
    'Diretriz técnica para armazenamento a seco, inspeção de frascos e plano de contingência para vazamentos acidentais.',
    'Diretriz Técnica',
    '/cofre/docs/diretriz_ricina_contencao.pdf',
    'c5e0a7f4d3b690123456789abcdef0123456789abcdef0123456789abcdef012',
    3, -- Ricina
    1, -- Toxicologia
    2  -- Dra. Júlia Fernandes
),
(
    4,
    'Dossiê Classificado Ômega - Protocolo de Defesa FX-99',
    'Documento ministerial sigiloso estipulando os códigos de neutralização por plasma e cadeia de comando de emergência.',
    'Dossiê Sigiloso',
    '/cofre/docs/omega_secret_fx99.enc',
    'd6f1b8a5e4c70123456789abcdef0123456789abcdef0123456789abcdef0123',
    4, -- Quimera FX-99
    2, -- Documentacao
    3  -- Ministro do Meio Ambiente
),
(
    5,
    'Normativa Ministerial MMA/GAB 04/2026 - Auditoria PIVC',
    'Regulamento geral de governança e custódia digital do sistema de autenticação biométrica F.A.C.A.',
    'Normativa Institucional',
    '/cofre/docs/normativa_faca_pivc.pdf',
    'e7a2c9b6f5d8123456789abcdef0123456789abcdef0123456789abcdef01234',
    NULL, -- Documento geral de governança (sem toxina específica)
    2, -- Documentacao
    3  -- Ministro do Meio Ambiente
);
