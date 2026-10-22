# Documentação Resumida de Atualização — F.A.C.A. (Frontend & Banco de Dados Integrados)

Este documento registra o estado consolidado do sistema **F.A.C.A — Frente de Autenticação e Controle de Acesso**, com todos os botões, telas e formulários do Front-End (`/` e `frontend-aps/`) conectados ao Banco de Dados Relacional **MySQL 8.0 (`aps_biometria`)** via FastAPI Python, sem alterar os arquivos do backend.

---

## 1. Conexão Completa dos Botões do Frontend ao Banco de Dados MySQL

1. **Login e Controle de Acesso (`src/js/principal.js` + `src/js/services/servico-api.js`)**:
   - **Usuário Administrador Geral (Equipe de T.I.)**:
     - Credenciais: **CPF** `000.000.000-00` (ou Matrícula `MMA-TI-000`) | **Senha** `AdmTI@2026` (ou `Faca@2026`).
     - Entra diretamente no painel de **Nível 3** sem precisar passar pelo reconhecimento facial.
   - **Demais Usuários (Operadores Nível 1, 2 e 3)**:
     - Exigem cadastro prévio no banco de dados com dados pessoais e biometria facial 128D registrada.
     - O botão **`INICIAR RECONHECIMENTO`** (`#btn-start-scan`) captura o frame da webcam em Base64 e valida via `POST /autenticar` contra as tabelas `usuario`, `biometria`, `tentativa_autenticacao` e `bloqueio_login`.
     - Caso o usuário não esteja cadastrado ou a face não seja reconhecida, o acesso é negado (`HTTP 401`) com mensagem explícita, bloqueando a conta por 15 minutos após 5 tentativas falhas (`HTTP 403`).

2. **Controle de Navegação e Proteção de Rotas (`src/js/painel-nivel3.js` + `src/js/components/menu-niveis.js`)**:
   - Removidas todas as barras de pré-visualização antes do login (`#spa-top-switcher`, `#role-preview-switcher` e alternadores manuais do cofre).
   - Proteção de rotas ativa (`validarAcessoRota` / `protegerRotaAtual`): qualquer tentativa de acessar `nivel1.html`, `nivel2.html`, `nivel3.html`, `?role=X` ou `#aba` diretamente pela URL sem estar autenticado redireciona imediatamente para a tela de login.
   - O menu lateral cumulativo exibe apenas os níveis permitidos para o usuário logado e possui o botão **`ENCERRAR SESSÃO (Sair)`** (`#btn-sidebar-logout`).

3. **Operações Conectadas nas Abas de Nível 1, Nível 2 e Nível 3 (`src/js/painel-nivel3.js`)**:
   - **Nível 1 (`#tab-estatisticas`, `#tab-panorama`, `#tab-alertas`, `#tab-pdf`)**: consome `GET /toxinas` e `GET /ping` para popular KPIs (`Total de Amostras`, `Média Amostras`, etc.), gráficos, mapa de calor com botões de zoom (`+`/`−`), barras de toxinas com nomes dinâmicos, tabela de alertas e o botão **`GERAR RELATÓRIO PDF`** (`#btn-gerar-pdf`).
   - **Nível 2 (`#tab-cofre-status`, `#tab-inventario`, `#tab-autenticacao-facial`)**:
     - **Acesso Restrito ao Cofre**: somente operadores autorizados (**Nível 2** ou **Nível 3**) e após a liberação biométrica facial no botão **`INICIAR ESCANEAMENTO`** (`#btn-n2-start-scan` ➔ `POST /autenticar`, ou bypass do ADM Geral T.I.) podem visualizar o interior do Cofre e o Inventário de Toxinas. Operadores de Nível 1 são bloqueados.
     - **Botão `+ ADICIONAR TOXINA` dentro do Cofre (`#btn-cofre-abrir-form-toxina` e `#btn-inv-abrir-form-toxina`)**: permite que usuários autorizados cadastrem novas toxinas no cofre (`#form-nova-toxina-cofre` / **`SALVAR TOXINA NO COFRE`**), salvando no banco/persistência e **atualizando imediatamente todos os dashboards do Nível 1** (`Síntese de Estatísticas`, `Panorama de Toxinas`, `Histórico de Alertas` e `Gerador PDF`), além do Inventário Nível 2 e widgets do Nível 3.
   - **Nível 3 (`#tab-historico`, `#tab-adicionar`, `#tab-desbloquear`)**:
     - Aba **Adicionar Operador**: botões **`ATIVAR CÂMERA`**, **`CAPTURAR FACIAL`**, upload de imagem e **`CADASTRAR OPERADOR E FACIAL`** (`#btn-submit-novo-usuario`) conectados a `POST /cadastrar`.
     - Aba **Desbloquear Conta**: botão **`DESBLOQUEAR CONTA`** (`#btn-desbloquear-direto`) e botões **`DESBLOQUEAR / UNBLOCK`** nas tabelas conectados a `POST /usuarios/{identificador}/desbloquear`.

---

## 2. Problema Identificado no Banco de Dados (Docker) e Solução Aplicada

- **Problema Ocorrido:**
  1. Ao tentar cadastrar ou desbloquear um usuário com o banco sem privilégios inicializados, o backend retornava `500 Internal Server Error` em texto puro, o que gerava no navegador `Unexpected token 'I', "Internal S"... is not valid JSON`.
  2. Nos logs do contêiner `faca_backend_api`, foi identificado `OperationalError: (1044, "Access denied for user 'faca_user'@'%' to database 'aps_biometria'")` porque o volume do MySQL havia subido antes da criação e liberação de permissões do schema `aps_biometria`.
- **Solução Aplicada (Sem mexer no Backend Python):**
  1. Adicionado `lerRespostaJsonSegura()` em `src/js/services/servico-api.js` para tratar respostas HTTP não-JSON sem quebrar a interface.
  2. Adicionado `GRANT ALL PRIVILEGES ON aps_biometria.* TO 'faca_user'@'%'; FLUSH PRIVILEGES;` em `database/01_schema_base.sql` e importados os scripts `01_schema_base.sql` e `02_seed_operadores_e_cofre.sql` diretamente no contêiner `faca_mysql_db` com charset `utf8mb4`.

---

## 3. Sincronização com a Pasta `frontend-aps/`

Todos os arquivos HTML, CSS, JavaScript, scripts do Banco de Dados (`database/01_schema_base.sql` e `database/02_seed_operadores_e_cofre.sql`) e documentações (`ROADMAP.md`, `RESUMO_ATUALIZACAO.md` e `docs/RELATORIO_FRONTEND.md`) estão sincronizados tanto na raiz do projeto quanto dentro do diretório `frontend-aps/`.
