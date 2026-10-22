# Roadmap - APS (Atividades Práticas Supervisionadas)

![Status](https://img.shields.io/badge/status-em%20andamento-yellow?style=flat-square)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![MySQL 8.0](https://img.shields.io/badge/MySQL_8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

Roadmap oficial do projeto acadêmico **F.A.C.A. (Frente de Autenticação e Controle de Acesso)** baseado no Cronograma de Entregas da APS de Ciência da Computação (PIVC — 2026/2, UNIP).

---

### Etapa 1 — Formalização do Tema

![Concluído](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen?style=flat-square)

Formalização do tema com os professores e aprovação do escopo de segurança e visão computacional:
- [x] Definição do escopo: Sistema de identificação e autenticação biométrica multifator (MFA) para o cofre de segurança máxima do Ministério do Meio Ambiente.
- [x] Mapeamento dos 3 níveis hierárquicos RBAC (Nível 1 - Pesquisa/Operacional, Nível 2 - Diretoria de Toxicologia, Nível 3 - Gabinete Ministerial / T.I.).
- [x] Delimitação da obrigatoriedade das 5 fases clássicas do Processamento Digital de Imagens (PIVC).

---

### Etapa 2 — Configuração do Repositório & Padrões de Projeto

![Concluído](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen?style=flat-square)

Configuração do repositório no GitHub, governança e ferramentas de desenvolvimento:
- [x] Repositório estruturado com branches temáticas (ex: `feat/backend-banco`, `main`).
- [x] Arquivos de configuração de ambiente (`.env.example`, `.env`, `.gitignore`, `.dockerignore`).
- [x] Configuração de tipagem estrita com analisadores estáticos (`pyrightconfig.json`, `pyrefly.toml`).
- [x] Scripts de automação do ambiente hospedeiro (`iniciar_faca.ps1`, `iniciar_faca.bat`).

---

### Etapa 3 — Banco de Dados Relacional 3FN & Docker Compose (MySQL 8.0)

![Concluído](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen?style=flat-square)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

Modelagem normalizada em 3FN do banco de dados relacional e infraestrutura containerizada:
- [x] **Modelagem 3FN oficial (Felipe):** 10 tabelas relacionais em `database/01_schema_base.sql` (e espelhadas em `frontend-aps/database/01_schema_base.sql`) com concessão automática de privilégios (`GRANT ALL PRIVILEGES`) ao usuário `faca_user`.
- [x] **Script de Carga / Seeds (`database/02_seed_operadores_e_cofre.sql` e `frontend-aps/database/02_seed_operadores_e_cofre.sql`):** 3 operadores oficiais + **Administrador Geral (T.I.)** com status ativo e hash PBKDF2 (`Faca@2026`), 4 toxinas controladas e 5 documentos técnicos.
- [x] **Orquestração Docker Compose (`docker-compose.yml`):**
  - Serviço `db` com MySQL 8.0, porta publicada `3307`, volume persistente `faca_mysql_data` e inicialização automática via `/docker-entrypoint-initdb.d`.
  - Serviço `backend` FastAPI com hot-reload (`WatchFiles`), rede interna `faca_network` e health checks configurados.
- [x] **Camada ORM SQLAlchemy 2.0 (`database.py` e `models.py`):** pool resiliente com `pool_pre_ping=True`, `pool_recycle=3600`, modelos tipados (`Mapped`, `mapped_column`, `relationship`).
- [x] **Camada de Repositório (`crud.py`):** controle de 5 tentativas consecutivas, bloqueio temporário (15 min), auditoria com histórico e enrollment biométrico.

---

### Etapa 4 — Prova de Conceito (Captura de Vídeo & MFA)

![Concluído](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen?style=flat-square)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)

Prova de Conceito (PoC) da captura de vídeo em tempo real no Frontend e validação no Backend:
- [x] Módulo de captura de vídeo com retícula HUD, malha holográfica e escaneamento em Canvas (`src/js/scanner-facial.js`).
- [x] Integração completa entre o frame capturado via webcam em Base64 e o endpoint FastAPI (`POST /autenticar` e `POST /cadastrar`).
- [x] Suporte à alternância entre modo câmera real e malha holográfica demonstrativa.
- [x] Telemetria de latência das 5 fases de processamento retornada nos contratos Pydantic v2 (`schemas.py`).

---

### Etapa 5 — Motor de Biometria Facial (PIVC — 5 Fases)

![Concluído](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen?style=flat-square)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)

Desenvolvimento do motor biométrico desacoplado em `biometria.py` implementando rigorosamente o pipeline clássico de PIVC:
- [x] **Fase 1 (Aquisição):** decodificação Base64 com sanitização RFC 4648 para matriz BGR (OpenCV).
- [x] **Fase 2 (Pré-processamento):** redimensionamento com interpolação bicúbica, normalização adaptativa de contraste CLAHE (espaço CIELAB) e conversão para RGB contíguo.
- [x] **Fase 3 (Segmentação):** localização da Região de Interesse (ROI) via detector HOG + Linear SVM com regra de negócio estrita de face única (0 ou >1 rostos disparam exceções de captura HTTP 400 sem consumir tentativas).
- [x] **Fase 4 (Extração de Características):** alinhamento por 5 landmarks e extração do vetor descritor de 128 dimensões via rede neural profunda ResNet-34 (dlib).
- [x] **Fase 5 (Classificação):** cálculo de distância euclidiana no espaço $\mathbb{R}^{128}$ com limiar de tolerância configurável (padrão 0.50) e cálculo de confiança percentual.

---

### Etapa 6 — Telas Web, Integração Frontend-Banco, Controle de Rotas & Terminal Desktop

![Concluído](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen?style=flat-square)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

Desenvolvimento da interface cibernética militar do sistema F.A.C.A., conexão total dos botões do Frontend ao MySQL e proteção de rotas:
- [x] **SPA Unificada (`index.html`) e Pacote Sincronizado (`frontend-aps/`):** transita entre Login (`#spa-view-login`) e Dashboard (`#spa-view-dashboard`) somente após validação das credenciais no banco.
- [x] **Controle de Navegação e Proteção de Rotas (`src/js/painel-nivel3.js` e `src/js/services/servico-api.js`):**
  - Removidos todos os botões de pré-visualização antes do login (`#spa-top-switcher`, `#role-preview-switcher` e alternadores manuais do cofre).
  - Bloqueio de acesso direto via URL (`nivel1.html`, `nivel2.html`, `nivel3.html`, `?role=X` ou `#aba`) sem login ativo, redirecionando imediatamente para a tela de login.
- [x] **Usuário Administrador Geral — Equipe de T.I. (`src/js/config/configuracao-banco.js` e `src/js/principal.js`):**
  - Acesso exclusivo da equipe de T.I. (`CPF: 000.000.000-00` / `Senha: AdmTI@2026`) que entra diretamente no Nível 3 sem passar pelo reconhecimento facial.
- [x] **Validação Estrita dos Demais Usuários (`src/js/principal.js` e `src/js/services/servico-api.js`):**
  - Exige cadastro prévio no MySQL com dados pessoais e facial registrada (`POST /autenticar`), negando o acesso com mensagens claras caso não esteja cadastrado ou a biometria divirja.
- [x] **Botões e Formulários Conectados ao Banco de Dados (`src/js/painel-nivel3.js`):**
  - **Nível 1:** Gráficos, KPIs, Mapa de Calor com zoom, barras dinâmicas, Alertas e Gerador de PDF alimentados por `GET /toxinas`, novas toxinas adicionadas ao Cofre e logs de auditoria.
  - **Nível 2:** Acesso restrito somente a pessoas permitidas (Nível 2 e Nível 3 após confirmação facial ou ADM T.I.), botão **`+ ADICIONAR TOXINA`** dentro do Cofre (`#form-nova-toxina-cofre`) que salva no banco e atualiza automaticamente os dashboards do Nível 1, além do Inventário de Toxinas com filtro de risco conectado.
  - **Nível 3:** Cadastro de novo operador com captura facial na webcam/upload (`POST /cadastrar`), Histórico de Auditoria Global e Desbloqueio de Contas (`POST /usuarios/{identificador}/desbloquear`).
- [x] **Launcher Desktop Nativo (`launcher.py`):** aplicação empacotada com PyWebView em janela nativa de missão crítica.

---

### Etapa 7 — Testes Integrados, Documentação Final & Apresentação

![Em Andamento](https://img.shields.io/badge/status-em%20andamento-yellow?style=flat-square)

Fase de homologação, testes de segurança ponta a ponta e preparação da entrega acadêmica:
- [x] **Bateria de Testes E2E Automatizados (`tests/test_e2e_mysql.py`):** 10/10 testes passando com 100% de sucesso contra o contêiner MySQL real.
- [x] **Verificação de Tipagem Estrita (Pyright):** 0 erros, 0 avisos em todos os módulos Python do projeto.
- [x] **Documentação Técnica e Relatórios Atualizados:** [`docs/WALKTHROUGH_BANCO.md`](docs/WALKTHROUGH_BANCO.md), [`docs/RELATORIO_FRONTEND.md`](docs/RELATORIO_FRONTEND.md) e [`RESUMO_ATUALIZACAO.md`](RESUMO_ATUALIZACAO.md).
- [ ] **Redação da Dissertação Escrita (70% da nota da APS):** elaboração do relatório final em formato ABNT/UNIP (Seções 1 a 10: Capa, Introdução, PIVC, Arquitetura, Relatório de Código, Bibliografia e Ficha).
- [ ] **Alinhamento com o Orientador:** confirmação das entregas parciais no Microsoft Teams e validação do relatório.
- [ ] **Ensaio da Apresentação Prática (30% da nota):** demonstração ao vivo para a banca com o ADM Geral (T.I.) e os operadores testando seus rostos na webcam.
