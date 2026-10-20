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
- [x] Mapeamento dos 3 níveis hierárquicos RBAC (Nível 1 - Pesquisa/Operacional, Nível 2 - Diretoria de Toxicologia, Nível 3 - Gabinete Ministerial).
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
- [x] **Modelagem 3FN oficial (Felipe):** 10 tabelas relacionais em `database/01_schema_base.sql` (`divisao`, `cargo`, `nivel_acesso`, `usuario`, `toxina`, `documento`, `biometria`, `tentativa_autenticacao`, `bloqueio_login` e `auditoria`).
- [x] **Script de Carga / Seeds (`database/02_seed_operadores_e_cofre.sql`):** 3 operadores oficiais com status ativo e hash PBKDF2 (`Faca@2026`) sem biometria prévia para enrollment on-the-fly, 4 toxinas controladas e 5 documentos técnicos.
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
- [x] Integração completa entre o frame capturado via webcam em Base64 e o endpoint FastAPI (`POST /autenticar`).
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

### Etapa 6 — Telas Web, Design System & Terminal Desktop

![Concluído](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen?style=flat-square)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

Desenvolvimento da interface cibernética militar do sistema F.A.C.A., Single Page Application e cliente Desktop nativo:
- [x] **SPA Unificada (`index.html`):** elimina erros 404 e transita suavemente entre Login (`#spa-view-login`), Dashboard (`#spa-view-dashboard`) e barra superior de demonstração (`#spa-top-switcher`).
- [x] **Menu Lateral Cumulativo por Nível RBAC (`src/js/components/menu-niveis.js`):**
  - **Nível 1 (Pesquisa/Operacional):** visualiza Síntese de Estatísticas, Panorama de Toxinas, Histórico de Alertas e Gerador PDF.
  - **Nível 2 (Diretoria):** visualiza todo o Nível 1 + Cofre Seguro (Status com planta baixa e travas), Inventário de Toxinas e Autenticação Facial Nível 2.
  - **Nível 3 (Ministro):** visualiza todo o Nível 1 e 2 + Histórico de Auditoria Global, Gestão de Operadores e Desbloqueio de Contas.
- [x] **Launcher Desktop Nativo (`launcher.py`):** aplicação empacotada com PyWebView em janela nativa de missão crítica, com detecção de API offline e modo Totem/Kiosk.
- [x] **Rotas RESTful no Backend Integradas (`main.py`):**
  - `POST /autenticar`: MFA real com checagem de bloqueio, validação de senha PBKDF2, enrollment on-the-fly ou match 1:1 e logs no MySQL.
  - `POST /cadastrar`: cadastro de novos operadores e biometria 128D no banco relacional.
  - `GET /toxinas`: consulta ao cofre com filtro dinâmico de autorização por nível RBAC.
  - `POST /usuarios/{identificador}/desbloquear`: salvaguarda operacional administrativa.
  - `GET /ping`: health check com status de conexão física ao MySQL.

---

### Etapa 7 — Testes Integrados, Documentação Final & Apresentação

![Em Andamento](https://img.shields.io/badge/status-em%20andamento-yellow?style=flat-square)

Fase de homologação, testes de segurança ponta a ponta e preparação da entrega acadêmica:
- [x] **Bateria de Testes E2E Automatizados (`tests/test_e2e_mysql.py`):** 10/10 testes passando com 100% de sucesso contra o contêiner MySQL real (health check, 5 falhas, bloqueio ativo, desbloqueio de emergência, enrollment on-the-fly, login recorrente, divergência facial, cofre RBAC e cadastro de operador).
- [x] **Verificação de Tipagem Estrita (Pyright):** 0 erros, 0 avisos em todos os módulos Python do projeto.
- [x] **Walkthrough Técnico de Banco de Dados (`docs/WALKTHROUGH_BANCO.md`):** arquitetura e guia de execução para a banca.
- [ ] **Redação da Dissertação Escrita (70% da nota da APS):** elaboração do relatório final em formato ABNT/UNIP (Seções 1 a 10: Capa, Introdução, PIVC, Arquitetura, Relatório de Código, Bibliografia e Ficha).
- [ ] **Alinhamento com o Orientador:** confirmação das entregas parciais no Microsoft Teams e validação do relatório.
- [ ] **Ensaio da Apresentação Prática (30% da nota):** demonstração ao vivo para a banca com os 3 integrantes testando seus rostos na webcam com enrollment on-the-fly.
