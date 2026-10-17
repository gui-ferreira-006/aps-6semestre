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
- [x] Gramática fixa comentada para envio dos frames Base64 ao Backend Python (`src/js/services/servico-api.js`)
- [ ] Envio ativo dos frames após liberação do Backend Python / MySQL

---

### Etapa 5 — Motor de Biometria

![Pendente](https://img.shields.io/badge/status-pendente-lightgrey?style=flat-square)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white)

Desenvolvimento do motor de biometria (Extração e comparação de faces).

---

### Etapa 6 — Telas Web e Integração

![Em Andamento](https://img.shields.io/badge/status-em%20andamento-yellow?style=flat-square)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)

Desenvolvimento das telas Web finais, controle de menu por níveis e preparação para compactação no Python.
- [x] Interface cibernética/militar de segurança (F.A.C.A) concluída (`index.html`)
- [x] Fluxo em duas etapas: Login por CPF/Senha ➔ Reconhecimento Facial (sem acessos fictícios, aguardando SQL)
- [x] Malha holográfica 3D e simulação de escaneamento em Canvas (`src/js/scanner-facial.js`)
- [x] **Tela de Nível 3 — Auditoria Global e Monitoramento** (`nivel3.html`, `src/css/components/painel-nivel3.css`, `src/js/painel-nivel3.js`)
- [x] **Menu Lateral Cumulativo por Role/Nível** (`src/js/components/menu-niveis.js`):
  - **Nível 3:** exibe todo o menu (Nível 1 + Nível 2 + Nível 3)
  - **Nível 2:** exibe tudo do Nível 2 e Nível 1
  - **Nível 1:** exibe somente a parte do menu de Nível 1
- [x] Relatório de entrega atualizado em: [`docs/RELATORIO_FRONTEND.md`](docs/RELATORIO_FRONTEND.md)
- [ ] Compactação do Frontend junto ao Backend Python e ativação das rotas MySQL / Docker

---

### Etapa 7 — Testes e Documentação Final

![Pendente](https://img.shields.io/badge/status-pendente-lightgrey?style=flat-square)

Testes de segurança, usabilidade e documentação final.
