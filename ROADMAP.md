# Roadmap - APS (Atividades Práticas Supervisionadas)

![Status](https://img.shields.io/badge/status-em%20andamento-yellow?style=flat-square)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)

Roadmap baseado no Cronograma de Entregas do Documento de Planejamento (Seção 7 — A Preencher).

---

### Etapa 1 — Formalização do Tema

![Pendente](https://img.shields.io/badge/status-pendente-lightgrey?style=flat-square)

Formalização do tema com os professores e aprovação do escopo.

---

### Etapa 2 — Configuração do Repositório

![Pendente](https://img.shields.io/badge/status-pendente-lightgrey?style=flat-square)

Configuração do repositório no GitHub (Privado, com acesso compartilhado).

---

### Etapa 3 — Banco de Dados & Docker Compose Base (Backend Python)

![Em Construção](https://img.shields.io/badge/status-em%20constru%C3%A7%C3%A3o-orange?style=flat-square)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

Modelagem do Banco de Dados MySQL e containerização no Docker para o Backend Python (onde o Frontend será compactado posteriormente).
- [x] Estrutura de configuração e gramática fixa comentada no Frontend (`src/js/config/configuracao-banco.js` e `src/js/services/servico-api.js`) pronta para receber a conexão do Backend Python + MySQL
- [ ] Disponibilização do banco MySQL e container Docker no Backend

---

### Etapa 4 — Prova de Conceito (Captura de Vídeo)

![Em Andamento](https://img.shields.io/badge/status-em%20andamento-yellow?style=flat-square)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)

Prova de Conceito (PoC) da captura de vídeo no JS e envio para o Python.
- [x] Módulo de captura de vídeo e retícula HUD em JavaScript (`src/js/scanner-facial.js`)
- [x] Integração JS com a configuração Python da facial (`POST /autenticar`) tanto no Login (`src/js/principal.js`) quanto na aba **Autenticação Facial do Nível 2** (`src/js/painel-nivel3.js`)
- [x] Gramática fixa comentada para consultas ao MySQL (`src/js/services/servico-api.js`)
- [ ] Integração final com banco de dados MySQL em Docker

---

### Etapa 5 — Motor de Biometria

![Concluído](https://img.shields.io/badge/status-conclu%C3%ADdo-brightgreen?style=flat-square)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)

Desenvolvimento do motor de biometria (Extração e comparação de faces nas 5 fases do PIVC em `biometria.py`).

---

### Etapa 6 — Telas Web e Integração

![Em Andamento](https://img.shields.io/badge/status-em%20andamento-yellow?style=flat-square)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

Desenvolvimento das telas Web finais para cada Role e cada aba do menu (sem dados fictícios, pré-configuradas para o MySQL), controle de menu cumulativo por níveis e empacotamento em `frontend-aps/`:
- [x] Interface cibernética/militar de segurança (F.A.C.A) concluída (`index.html`)
- [x] Fluxo em duas etapas: Login por CPF/Senha ➔ Reconhecimento Facial
- [x] Malha holográfica 3D e escaneamento em Canvas (`src/js/scanner-facial.js`)
- [x] **Menu Lateral Cumulativo por Role/Nível** (`src/js/components/menu-niveis.js`):
  - **Role Nível 3:** exibe todo o menu (Nível 1 + Nível 2 + Nível 3)
  - **Role Nível 2:** exibe tudo do Nível 2 e Nível 1
  - **Role Nível 1:** exibe somente a parte do menu de Nível 1
- [x] **Telas de Nível 1 — Relatórios (`nivel1.html`)** (pré-configuradas para receber o MySQL, sem dados):
  - Aba `Síntese de Estatísticas` (gráficos de detecção/amostras e 4 KPIs)
  - Aba `Panorama de Toxinas` (mapa de calor, gráficos de rosca e barras por toxina)
  - Aba `Histórico de Alertas` (tabela de ocorrências aguardando SQL)
  - Aba `Gerador PDF` (filtros de data/seções e folha de pré-visualização PDF)
- [x] **Telas de Nível 2 — Cofre (`nivel2.html`)** (pré-configuradas para receber o MySQL, sem dados):
  - Aba `Cofre Seguro (Status)` com os 2 estados: *Estado 1: Acesso Negado / Cofre Bloqueado* e *Estado 2: Cofre Desbloqueado — Status Geral e Planta Baixa*
  - Aba `Inventário de Toxinas` (filtros, temperatura interna, quantidade e tabela aguardando SQL)
  - Aba `Autenticação Facial` (`Sistema de Autenticação Facial — Liberação de Acesso ao Cofre`, usando a mesma configuração Python da facial no JS)
- [x] **Telas de Nível 3 — Auditoria (`nivel3.html`)** (pré-configuradas para receber o MySQL, sem dados):
  - Aba `Histórico de Acessos` (`Nível 3 — Auditoria Global e Monitoramento` com Sessões Ativas, Timeline, Eventos e widgets inferiores)
  - Aba `Adicionar` (formulário de novo operador preparado para `INSERT INTO usuarios`)
  - Aba `Desbloquear Conta` (tabela preparada para `UPDATE usuarios SET bloqueado = 0`)
- [x] Pacote isolado do Frontend gerado em `frontend-aps/` com guia resumido de integração em [`frontend-aps/RESUMO_ATUALIZACAO.md`](frontend-aps/RESUMO_ATUALIZACAO.md) e [`docs/RELATORIO_FRONTEND.md`](docs/RELATORIO_FRONTEND.md)
- [ ] Compactação final do Frontend junto ao container MySQL / Docker quando liberado

---

### Etapa 7 — Testes e Documentação Final

![Pendente](https://img.shields.io/badge/status-pendente-lightgrey?style=flat-square)

Testes de segurança, usabilidade e documentação final.
