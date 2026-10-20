# Relatório de Desenvolvimento do Frontend — F.A.C.A

**Projeto:** F.A.C.A - Frente de Autenticação e Controle de Acesso  
**Instituição:** Ministério do Meio Ambiente / UNIP - APS 6° Semestre  
**Responsável Frontend:** Júlia Fernandes  
**Data de Atualização:** 17/10/2026  

---

## 📌 Enquadramento no ROADMAP e Arquitetura

Este pacote de entregas cobre:

### 🎯 **Etapa 6 — Telas Web e Integração** (Aba Principal)
- **Status atual no Roadmap:** Em Andamento — Interface de Login/Biometria e **Tela de Nível 3 (Auditoria Global e Monitoramento)** concluídas com 100% da nomenclatura em **PT-BR**.
- **Empacotamento Futuro:** O Frontend foi estruturado de forma modular para ser **compactado e servido diretamente pelo Backend em Python** posteriormente.

### 🗄️ **Etapa 3 — Preparação para Banco de Dados MySQL & Docker (Backend)**
- **Diretriz de Integração:** O banco de dados **MySQL** e a containerização em **Docker** pertencem à infraestrutura do **Backend Python**.
- **Sem Acessos Inventados:** Nenhuma credencial ou sessão falsa foi inserida em produção. Todos os pontos onde entrarão os dados do MySQL possuem apenas **comentários explicativos e a gramática fixa** pronta para descomentar assim que o acesso ao banco for disponibilizado.

---

## 📋 Resumo de Tudo o que Foi Implementado

### 1. Estrutura e Interface de Identificação (`index.html`)
- **Cabeçalho Institucional F.A.C.A:**
  - Emblema vetorial (SVG) com escudo poligonal metálico, conexões de circuito eletrônico e núcleo central avermelhado com cadeado de alta segurança.
  - Tipografia de alta precisão com os títulos `F.A.C.A` e `MINISTÉRIO DO MEIO AMBIENTE`.
- **Anotações de HUD nos Quatro Cantos da Tela:**
  - *Superior Esquerdo:* `SEGURANÇA / INFORMAÇÃO / PRESERVAÇÃO / UM FUTURO MAIS SEGURO`.
  - *Superior Direito:* `ACESSO RESTRITO` com indicador de linha laser.
  - *Inferior Esquerdo:* `TECNOLOGIA A SERVIÇO DA CONSERVAÇÃO`.
  - *Inferior Direito:* Marcador em formato de estrela e `NATUREZA / DADOS / RESULTADOS`.
- **Nomenclatura 100% em PT-BR** para todos os arquivos e componentes do projeto.

---

### 2. Fluxo Sequencial de Autenticação (Login ➔ Leitura Biométrica)

Sistema em etapas (*step-by-step*) preparado para validação real no MySQL via Python:

#### **Etapa 1: Acesso por CPF e Senha**
- **Card de Autenticação:** Painel translúcido escuro em *glassmorphism* com bordas finas e iluminação avermelhada.
- **Campo de CPF:** Máscara dinâmica `000.000.000-00`.
- **Campo de Senha:** Botão interativo para alternar visualização da senha.
- **Integração Comentada:** Gramática pronta em `principal.js` e `servico-api.js` aguardando o banco MySQL.

#### **Etapa 2: Reconhecimento Facial (Biometria)**
- **Visor do Scanner Facial:** 4 retículas angulares, mira cartesiana e linha laser vermelha.
- **Malha Holográfica 3D (`scanner-facial.js`):** Renderização em tempo real de malha facial tridimensional em Canvas e suporte à webcam real (`getUserMedia`).
- **Validação de Role sem Dados Inventados:** Após a captura, o código possui o bloco comentado com a gramática fixa para receber o `nivel_acesso` (`1`, `2` ou `3`) vindo do MySQL pelo Python.

---

### 3. Tela de Nível 3 — Auditoria Global e Monitoramento (`nivel3.html`)

Desenvolvida fielmente à referência visual do sistema:

- **Menu Lateral Cumulativo por Role (`src/js/components/menu-niveis.js`):**
  - **Usuários com Role de Nível 3:** visualizam **tudo daquele menu** (`NÍVEL 1 (Relatórios)` + `NÍVEL 2 (Cofre)` + `NÍVEL 3 (Auditoria)`).
  - **Usuários com Role de Nível 2:** visualizam **tudo do Nível 2 e Nível 1** (`NÍVEL 1 (Relatórios)` + `NÍVEL 2 (Cofre)`).
  - **Usuários com Role de Nível 1:** visualizam **somente a parte do menu de Nível 1** (`NÍVEL 1 (Relatórios)`).
  - *Nota:* Inclui seletor rápido no topo direito da tela (`ROLE NÍVEL 3 | ROLE NÍVEL 2 | ROLE NÍVEL 1`) para testar visualmente a regra de exibição do menu antes da conexão com o SQL.
- **Painel Principal de Auditoria (`NÍVEL 3 — AUDITORIA GLOBAL E MONITORAMENTO`):**
  - **Coluna Esquerda — `SESSÕES ATIVAS`:** botão `+ NOVO USUÁRIO` e tabela estruturada (`NAME`, `DESCRIÇÃO`, `DATA`, `ULTM`) com slots aguardando o SQL e gramática `<tr>` comentada.
  - **Coluna Direita — `HISTÓRICO DE ACESSOS`:** botão `+ NOVO USUÁRIO`, trilha vertical `TIMELINE` com nós luminosos e card `EVENTO` com botões `UNBLOCK`, prontos para receber registros da tabela de auditoria do MySQL.
- **Widgets Inferiores de Monitoramento:**
  - **Card `ALERTAS`:** gráfico em linha/área vermelha brilhante com eixo vertical (`0` a `200`).
  - **Card `PANORAMA DE TOXINAS`:** barras de progresso luminosas para `DIOXINAS`, `PFAS` e `FOSFATOS`.
  - **Card `COFRE`:** medidor circular em arco (*gauge*) indicando o percentual do cofre.

---

### 4. Configuração Comentada e Gramática Fixa (Backend Python + MySQL/Docker)

- **`src/js/config/configuracao-banco.js`:**
  - Centraliza a gramática fixa de `URL_BASE_API` (preparada tanto para quando o Frontend for compactado na mesma origem do Python quanto para servidor local), rotas da API Python (`ROTAS_API_PYTHON`), matriz cumulativa de níveis (`MATRIZ_NIVEIS_MENU`) e contratos JSON das colunas do MySQL.
- **`src/js/services/servico-api.js`:**
  - Contém as funções assíncronas com os blocos `fetch` comentados (`validarCredenciais`, `autenticarBiometria`, `obterDadosAuditoriaNivel3`, `cadastrarNovoUsuario`, `desbloquearContaUsuario`).

---

## 📂 Mapa de Arquivos do Projeto (100% em PT-BR)

| Arquivo | Localização | Descrição |
|---|---|---|
| `index.html` | `/index.html` | Tela inicial de Login (CPF/Senha) e Reconhecimento Facial |
| `nivel3.html` | `/nivel3.html` | Tela de Nível 3 (Auditoria Global e Monitoramento) e Menu por Níveis |
| `estilo.css` | `/src/css/estilo.css` | Folha de estilos base, variáveis, HUD e animações |
| `painel-nivel3.css` | `/src/css/components/painel-nivel3.css` | Estilos exclusivos da Tela de Nível 3, menu lateral, tabelas e gráficos |
| `configuracao-banco.js` | `/src/js/config/configuracao-banco.js` | Gramática fixa comentada para integração com o Backend Python e MySQL/Docker |
| `servico-api.js` | `/src/js/services/servico-api.js` | Camada de serviço com chamadas comentadas para as rotas Python/MySQL |
| `menu-niveis.js` | `/src/js/components/menu-niveis.js` | Lógica cumulativa do menu lateral por role (Nível 1, Nível 2 e Nível 3) |
| `painel-nivel3.js` | `/src/js/painel-nivel3.js` | Controlador da Tela de Nível 3 com funções de renderização SQL comentadas |
| `principal.js` | `/src/js/principal.js` | Controle das etapas de login e biometria sem acessos inventados |
| `scanner-facial.js` | `/src/js/scanner-facial.js` | Renderizador da malha 3D facial, HUD de biometria e controle de câmera |
| `particulas.js` | `/src/js/particulas.js` | Rede neural animada de fundo com partículas conectadas |

---

## 🚀 Como Executar e Testar

1. Abra [`index.html`](../index.html) no navegador para visualizar o fluxo de Login ➔ Biometria (ou clique em **`[Estrutura Tela Nível 3 →]`** no rodapé do card).
2. Abra [`nivel3.html`](../nivel3.html) para visualizar a **Tela de Nível 3 — Auditoria Global e Monitoramento** e utilize os botões no canto superior direito para testar o comportamento do menu nas roles de **Nível 3**, **Nível 2** e **Nível 1**.
