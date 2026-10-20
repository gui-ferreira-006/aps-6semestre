# F.A.C.A - Frente de Autenticação e Controle de Acesso / APS 6° Semestre

![Status](https://img.shields.io/badge/status-em%20andamento-yellow?style=flat-square)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL_8.0-4479A1?style=flat-square&logo=mysql&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

---

> 🔐 **Sistema de Identificação e Autenticação Biométrica Multifator (MFA)**  
> Ciência da Computação · UNIP · 2026/2  
> Disciplina Principal: Processamento de Imagem e Visão Computacional (PIVC)

---

## 1. Informações Gerais

| Item | Detalhe |
|---|---|
| **Curso** | Ciência da Computação — 6º Semestre |
| **Semestre Letivo** | 2026/2 |
| **Disciplina Base** | Processamento de Imagem e Visão Computacional (PIVC) |
| **Tema Oficial** | Frente de Autenticação e Controle de Acesso — F.A.C.A. |
| **Branch de Trabalho** | `feat/backend-banco` |

### 👥 Equipe do Projeto

| Integrante | RA | Responsabilidade Principal |
|---|---|---|
| **Guilherme Ferreira** | G9483B2 | Backend (FastAPI), Visão Computacional (PIVC), Integração ORM & Infraestrutura |
| **Júlia Fernandes** | R101BF1 | Frontend (SPA, Design System, Scanner Facial) & Documentação |
| **Felipe** | R079CB0 | Modelagem do Banco de Dados Relacional (3FN, DDL/DML) & Documentação |

---

## 2. Visão Geral do Projeto

O sistema **F.A.C.A.** é uma solução de segurança de missão crítica desenvolvida para o cofre de segurança máxima do **Ministério do Meio Ambiente**.

O cofre armazena amostras biológicas e documentações confidenciais sobre toxinas perigosas capazes de deflagrar incidentes biológicos globais. O sistema atua como **última linha de defesa cibernética e física**: nenhum operador tem acesso liberado sem a validação simultânea de credenciais operacionais (CPF e Senha com salt PBKDF2) e reconhecimento facial biométrico em tempo real por meio das 5 fases clássicas de PIVC.

---

## 3. Objetivos e Regras de Negócio

### 🎚️ Níveis de Acesso Hierárquicos (RBAC Cumulativo)

O sistema implementa controle de acesso granular baseado em papéis:

| Nível | Função | Permissões no Sistema |
|:---:|---|---|
| **Nível 1** | Pesquisador / Operacional | Síntese de estatísticas, panorama geral de toxinas, histórico de alertas e emissão de relatórios PDF. |
| **Nível 2** | Diretor de Toxicologia | Todas as funções do Nível 1 + Gestão do Cofre Seguro (planta baixa, travas eletromecânicas), inventário completo de toxinas e autenticação facial específica para o cofre. |
| **Nível 3** | Ministro do Meio Ambiente | Todas as funções dos Níveis 1 e 2 + Auditoria Global de eventos de segurança, gestão e cadastro de novos operadores e desbloqueio emergencial de contas bloqueadas. |

### 🧪 Requisito Obrigatório: As 5 Fases do PIVC

Todo frame capturado pela câmera passa rigorosamente pelas cinco etapas formais de Visão Computacional:

1. **Aquisição:** Captura do quadro via webcam e decodificação Base64 para matriz BGR (OpenCV).
2. **Pré-processamento:** Redimensionamento bicúbico, equalização adaptativa de histograma CLAHE no canal L do espaço CIELAB e conversão para RGB contíguo.
3. **Segmentação:** Detecção da Região de Interesse (ROI) via HOG + Linear SVM com trava de segurança de face única (rejeição se 0 ou >1 rostos).
4. **Extração de Características:** Alinhamento facial por 5 marcos anatômicos e extração do vetor biométrico de 128 dimensões via rede neural profunda ResNet-34.
5. **Classificação e Tomada de Decisão:** Cálculo de distância euclidiana no espaço $\mathbb{R}^{128}$ contra o vetor cadastrado no banco relacional (limiar configurável $\le 0.50$).

### 🛡️ Políticas de Segurança e Salvaguardas

- **Enrollment On-the-Fly:** Os operadores iniciam sem biometria prévia (`biometria_cadastrada = FALSE`). No primeiro login bem-sucedido com CPF e senha, o rosto posicionado na câmera é automaticamente extraído e persistido na tabela `biometria` do MySQL.
- **Bloqueio por Ameaça:** 5 falhas consecutivas de senha ou biometria acionam bloqueio automático da conta por 15 minutos (`HTTP 403 ACCOUNT_LOCKED`), registrado na tabela `bloqueio_login`.
- **Salvaguarda de Apresentação:** Rota administrativa `POST /usuarios/{identificador}/desbloquear` para liberação imediata sem necessidade de intervenção direta no SQL.

---

## 4. Arquitetura e Tecnologias

| Camada | Tecnologia | Detalhes da Implementação |
|---|---|---|
| **Frontend Web** | HTML5, CSS3 cibernético, JS ES6 | Single Page Application (SPA) unificada, Canvas HUD, alternância Login/Dashboard sem erros 404. |
| **Cliente Desktop** | PyWebView | Janela nativa Desktop para totens de missão crítica e bancas avaliadoras (`launcher.py`). |
| **Backend & API** | Python 3.11+, FastAPI, Pydantic v2 | Arquitetura RESTful com endpoints tipados, injeção de dependência e CORS configurado. |
| **Visão Computacional** | OpenCV & dlib (ResNet-34) | Motor `biometria.py` desacoplado executando as 5 fases do PIVC. |
| **Persistência Relacional** | MySQL 8.0 & SQLAlchemy 2.0 | 10 tabelas normalizadas em 3FN, pool resiliente (`pool_pre_ping=True`, `pool_recycle=3600`). |
| **Infraestrutura** | Docker Compose | Contêineres `faca_mysql_db` (porta `3307`) e `faca_backend_api` (porta `8000`) em rede isolada. |

---

## 5. Como Executar o Projeto

### Pré-requisitos
- **Docker Desktop** (com Docker Compose v2)
- **Python 3.11+** com virtualenv configurada (ou ambiente Conda)
- Câmera/Webcam conectada para os testes de biometria real

### 🚀 Inicialização Rápida (Recomendada)

Execute o script de automação unificado no PowerShell:

```powershell
.\iniciar_faca.ps1
```

O script executa automaticamente:
1. Verificação e inicialização dos contêineres Docker (`docker compose up -d`).
2. Aguardo do health check do MySQL na porta `3307`.
3. Aplicação do DDL/DML caso seja a primeira inicialização.
4. Inicialização do servidor FastAPI (`http://localhost:8000`).
5. Abertura do cliente Desktop nativo (`launcher.py`) ou navegador.

### 🧪 Execução dos Testes Automatizados E2E

Para validar a integridade ponta a ponta do banco e da API contra o MySQL real:

```powershell
pytest tests/test_e2e_mysql.py -v
```

*Todos os 10 testes cobrem health check, falhas sucessivas, bloqueio temporário, desbloqueio de emergência, enrollment on-the-fly, autenticação recorrente, divergência facial e permissões RBAC do cofre.*

---

## 6. Trabalho Escrito (Dissertação) — 70% da Nota da APS

### 📐 Formatação Obrigatória (Manual UNIP)
- Fonte **Arial 12**, espaçamento entre linhas **1,5**, margens de **2,5 cm**, papel **A4**.
- Encadernação em **espiral com capa transparente**.

### 📑 Estrutura das Seções (ABNT/UNIP)

| Seção | Título | Limite de Páginas | Status |
|:---:|---|:---:|:---:|
| 1 | Capa (Curso, Tema, Alunos com Nome/RA) | 1 | ⏳ Pendente de compilação final |
| 2 | Índice | 1 | ⏳ Pendente de compilação final |
| 3 | Objetivo e Motivação do Trabalho | 1 a 2 | ⏳ Em elaboração |
| 4 | Introdução | 2 a 8 | ⏳ Em elaboração |
| 5 | Fundamentos das Principais Técnicas (PIVC) | 10 a 20 | ⏳ Em elaboração |
| 6 | Plano de Desenvolvimento da Aplicação | 5 a 15 | ⏳ Em elaboração |
| 7 | Projeto (Estrutura, Banco 3FN e Módulos) | 18 a 35 | ⏳ Em elaboração |
| 8 | Relatório de Código (linhas de código) | — | ⏳ Em elaboração |
| 9 | Bibliografia | — | ⏳ Em elaboração |
| 10 | Ficha de Atividades Práticas Supervisionadas | — | ⏳ Aguardando assinatura |

---

## 7. Status das Entregas e Próximos Passos

### ✅ Engenharia de Software e Desenvolvimento Técnico (Concluído):
- [x] **Banco de Dados 3FN:** 10 tabelas relacionais em `database/01_schema_base.sql`.
- [x] **Carga Oficial de Dados:** Seeds dos 3 operadores, toxinas e documentos em `database/02_seed_operadores_e_cofre.sql`.
- [x] **Infraestrutura Docker:** Orquestração do MySQL 8.0 e FastAPI via `docker-compose.yml`.
- [x] **Camada ORM SQLAlchemy 2.0:** Modelos tipados e pool resiliente em `database.py` e `models.py`.
- [x] **Lógica de Negócio e Repositório:** Controle de falhas, bloqueio de 15 minutos e enrollment em `crud.py`.
- [x] **Motor Biométrico PIVC:** Pipeline completo de 5 fases em `biometria.py`.
- [x] **API RESTful:** Rotas `/autenticar`, `/cadastrar`, `/toxinas`, `/usuarios/{id}/desbloquear` e `/ping` em `main.py`.
- [x] **Frontend SPA:** Single Page Application unificada com Login, Dashboard e 10 abas em `index.html`.
- [x] **Launcher Desktop:** Executável nativo com PyWebView em `launcher.py`.
- [x] **Testes Automatizados:** 10/10 testes passando em `tests/test_e2e_mysql.py`.
- [x] **Tipagem Estrita:** 0 erros e 0 alertas no Pyright.

### ⏳ Pendências Acadêmicas e de Apresentação (Em Andamento):
- [ ] **Redação do Relatório Escrito (70% da nota):** Preencher as seções 1 a 10 de acordo com as normas ABNT.
- [ ] **Alinhamento com Orientador:** Validação das entregas parciais no Microsoft Teams.
- [ ] **Ensaio da Apresentação Prática (30% da nota):** Ensaio com a banca demonstrando o enrollment facial real dos integrantes.
- [ ] *(Opcional / Polimento)* Descomentar integrações de formulários secundários no Frontend (`src/js/painel-nivel3.js`).
