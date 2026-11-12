# Relatório de Desenvolvimento do Frontend — F.A.C.A (Integrado ao Banco MySQL 8.0)

**Projeto:** F.A.C.A - Frente de Autenticação e Controle de Acesso  
**Instituição:** Ministério do Meio Ambiente / UNIP - APS 6° Semestre (PIVC — 2026/2)  
**Responsável Frontend:** Júlia Fernandes  
**Data de Atualização:** 21/10/2026  

---

## 📌 Enquadramento no ROADMAP e Status Atual

### 🎯 **Etapa 6 — Telas Web, Segurança de Rotas e Integração com Banco de Dados MySQL**
- **Status atual no Roadmap:** **Concluído (100% Integrado)** — Todas as telas, botões e formulários do Frontend (`index.html`, `nivel1.html`, `nivel2.html`, `nivel3.html` e pacote em `frontend-aps/`) estão conectados às operações do banco de dados **MySQL 8.0 (`aps_biometria`)** através do Backend FastAPI Python, sem necessidade de alterações no backend.
- **Controle Estrito de Acesso e Navegação:**
  - Removidos todos os botões de pré-visualização que permitiam pular etapas antes do login (`#spa-top-switcher`, `#role-preview-switcher` e alternadores manuais do cofre).
  - Implementado guardião de rotas (`protegerRotaAtual` e `validarAcessoRota`): tentativas de acesso direto via URL (`nivel1.html`, `nivel2.html`, `nivel3.html`, `?role=X` ou `#aba`) sem sessão autenticada redirecionam imediatamente para a tela de login.
- **Usuário Administrador Geral (Equipe de T.I.):**
  - Criado o acesso exclusivo da equipe de T.I. (`CPF: 000.000.000-00` / `Matrícula: MMA-TI-000`), que entra diretamente no painel de Nível 3 **sem passar pelo reconhecimento facial**.
- **Validação Obrigatória para os Demais Usuários:**
  - Só entra no sistema quem estiver cadastrado no banco de dados com dados pessoais e biometria facial 128D registrada (`POST /autenticar`).
  - Se o usuário não estiver cadastrado ou a facial não for reconhecida, o acesso é negado (`HTTP 401`) com mensagem clara na interface, bloqueando a conta automaticamente na 5ª tentativa falha consecutiva (`HTTP 403`).

---

## 📋 Resumo de Tudo o que Foi Implementado e Conectado ao Banco

### 1. Mapeamento dos Botões Conectados ao Banco de Dados (`MySQL 8.0`)

| Tela / Aba | Botão / Controle | Operação Executada no Banco de Dados |
|---|---|---|
| **Login — Etapa 1 (`#step-login`)** | `ENTRAR` (`#btn-entrar`) | Identifica o **ADM Geral (T.I.)** para acesso imediato sem facial (`Nível 3`), ou valida o CPF de 11 dígitos dos demais operadores para avançar à validação biométrica obrigatória. |
| **Login — Etapa 2 (`#step-biometrics`)** | `INICIAR RECONHECIMENTO` (`#btn-start-scan`) | Captura o frame da webcam em Base64 e envia `POST /autenticar` para validar CPF, hash de senha PBKDF2 e vetor facial 128D nas tabelas `usuario`, `biometria`, `tentativa_autenticacao` e `bloqueio_login`. |
| **Menu Lateral Cumulativo** | Abas (`[data-spa-tab]`) e `ENCERRAR SESSÃO` (`#btn-sidebar-logout`) | Libera apenas as seções permitidas pelo `nivel_acesso` (1, 2 ou 3) validado no login, sincroniza `GET /toxinas` + `GET /ping` e realiza logout limpando a sessão. |
| **Nível 1 — Panorama (`#tab-panorama`)** | Botões `+` e `−` (`.btn-map-zoom`) | Controlam o zoom do mapa de calor alimentado pelas amostras reais retornadas de `GET /toxinas`. |
| **Nível 1 — Gerador PDF (`#tab-pdf`)** | `GERAR RELATÓRIO PDF` (`#btn-gerar-pdf`) | Consulta os registros filtrados por RBAC no MySQL (`GET /toxinas`) e logs de auditoria, preenchendo a folha de pré-visualização (`#tbody-pdf-preview`). |
| **Nível 2 — Cofre Seguro (`#tab-cofre-status`)** | `IR PARA AUTENTICAÇÃO FACIAL` (`#btn-ir-autenticacao-facial`) e `+ ADICIONAR TOXINA` (`#btn-cofre-abrir-form-toxina`) | Direciona para o scanner facial do Nível 2 para desbloqueio autenticado do cofre e, após liberado (somente para Nível 2 e Nível 3), permite abrir o formulário de cadastro de nova toxina. |
| **Nível 2 — Formulário do Cofre (`#form-nova-toxina-cofre`)** | `SALVAR TOXINA NO COFRE` (`#btn-salvar-toxina-cofre`) | Exclusivo para operadores permitidos (`Nível 2` ou `Nível 3` com cofre desbloqueado): salva a nova toxina no banco e atualiza imediatamente os dashboards do **Nível 1** (`Síntese de Estatísticas`, `Panorama de Toxinas`, `Histórico de Alertas` e `Gerador PDF`) e o **Inventário Nível 2**. |
| **Nível 2 — Inventário (`#tab-inventario`)** | `Filtros de Busca` (`#sql-filtro-inventario`) e `+ ADICIONAR TOXINA` (`#btn-inv-abrir-form-toxina`) | Protegido contra acesso sem desbloqueio do cofre; filtra dinamicamente os registros de toxinas por nível de risco e permite adicionar novas toxinas ao cofre. |
| **Nível 2 — Facial do Cofre (`#tab-autenticacao-facial`)** | `INICIAR ESCANEAMENTO` (`#btn-n2-start-scan`) | Executa `POST /autenticar` com o frame da webcam para confirmar a biometria e o nível de permissão (`Nível >= 2`), liberando o acesso ao **Cofre Desbloqueado** e ao **Inventário**. |
| **Nível 3 — Auditoria (`#tab-historico`)** | `+ NOVO USUÁRIO` e `UNBLOCK` (`[data-unblock-cpf]`) | Abre a aba de cadastro ou executa `POST /usuarios/{cpf}/desbloquear` diretamente a partir do alerta de conta bloqueada. |
| **Nível 3 — Adicionar Operador (`#tab-adicionar`)** | `ATIVAR CÂMERA`, `CAPTURAR FACIAL`, Upload e `CADASTRAR OPERADOR E FACIAL` | Captura a face do novo operador e envia `POST /cadastrar`, gravando os dados pessoais na tabela `usuario`, o vetor 128D na tabela `biometria` e o log em `auditoria`. |
| **Nível 3 — Desbloquear Conta (`#tab-desbloquear`)** | `DESBLOQUEAR CONTA` (`#btn-desbloquear-direto`) e botões da tabela | Envia `POST /usuarios/{identificador}/desbloquear` para desativar bloqueios na tabela `bloqueio_login` e zerar falhas consecutivas. |

---

### 2. Credenciais de Acesso para Testes

#### A) Usuário Administrador Geral (Equipe de T.I. — Sem Reconhecimento Facial)
- **CPF:** `000.000.000-00` *(ou `00000000000` / Matrícula: `MMA-TI-000`)*
- **Senha:** `AdmTI@2026` *(ou `Faca@2026`)*
- **Comportamento:** Entra diretamente no painel de **Nível 3 (Auditoria Global, Cadastro de Operadores e Desbloqueio)** sem passar pela câmera/reconhecimento facial.

#### B) Operadores Cadastrados no Banco MySQL (Exigem Reconhecimento Facial)
| Operador | CPF | Senha | Nível RBAC | Divisão |
|---|---|---|---|---|
| **Guilherme Ferreira** | `123.456.789-00` | `Faca@2026` | Nível 1 (Relatórios) | Toxicologia |
| **Dra. Júlia Fernandes** | `987.654.321-00` | `Faca@2026` | Nível 2 (Cofre + Relatórios) | Toxicologia |
| **Ministro do Meio Ambiente** | `111.222.333-44` | `Faca@2026` | Nível 3 (Auditoria Completa) | Documentação |

---

## 🛠️ Diagnóstico de Incidentes e Soluções Aplicadas (Troubleshooting)

Durante a integração e homologação das operações de cadastro e desbloqueio com o banco de dados MySQL 8.0 no Docker, dois problemas encadeados foram identificados e solucionados **sem alterar nenhuma linha do backend Python**:

### 1. Erro `SyntaxError: Unexpected token 'I', "Internal S"... is not valid JSON`
- **Causa do Problema:** Quando o servidor FastAPI encontrava uma falha de conexão com o banco de dados e retornava um erro `500 Internal Server Error` em texto puro (`"Internal Server Error"`), o método `resposta.json()` no JavaScript tentava interpretar a letra `"I"` de `"Internal..."` como JSON, disparando a exceção de sintaxe na tela.
- **Como foi Solucionado:** Foi implementado o método [`ServicoAPI.lerRespostaJsonSegura(resposta)`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/src/js/services/servico-api.js#L39-L53) em `src/js/services/servico-api.js`, que lê a resposta como texto (`resposta.text()`) e realiza `JSON.parse()` dentro de um bloco `try/catch`, exibindo uma mensagem clara e amigável na interface caso o banco retorne erro interno.

### 2. Erro `Falha interna no servidor` / `OperationalError (1044): Access denied for user 'faca_user'@'%' to database 'aps_biometria'`
- **Causa do Problema:** Embora o contêiner Docker `faca_mysql_db` estivesse em execução, o volume persistente do MySQL havia sido inicializado anteriormente sem o banco `aps_biometria` importado e sem a concessão de privilégios (`GRANT ALL PRIVILEGES`) para o usuário da aplicação (`faca_user`). Com isso, o SQLAlchemy no backend recebia `ERROR 1049 (Unknown database 'aps_biometria')` / `ERROR 1044 (Access denied)`.
- **Como foi Solucionado (Sem alterar o Backend):**
  1. Foi adicionada a instrução `GRANT ALL PRIVILEGES ON aps_biometria.* TO 'faca_user'@'%'; FLUSH PRIVILEGES;` diretamente no script de schema [`database/01_schema_base.sql`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/database/01_schema_base.sql#L7-L14).
  2. Os scripts [`01_schema_base.sql`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/database/01_schema_base.sql) e [`02_seed_operadores_e_cofre.sql`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/database/02_seed_operadores_e_cofre.sql) foram importados diretamente no contêiner ativo `faca_mysql_db` com codificação `utf8mb4`, criando as 10 tabelas 3FN, os 4 operadores iniciais (incluindo o ADM Geral de T.I.) e as 4 toxinas iniciais, restabelecendo imediatamente o status `200 OK` / `201 Created` em todas as rotas.

---

## 📂 Mapa de Arquivos do Frontend e Banco (`/` e `/frontend-aps/`)

| Arquivo | Localização | Descrição |
|---|---|---|
| `index.html` | `/index.html` e `/frontend-aps/index.html` | SPA unificada com Login (Etapa 1 e 2), Cofre com botão `+ ADICIONAR TOXINA` e 10 abas protegidas |
| `nivel1.html` | `/nivel1.html` e `/frontend-aps/nivel1.html` | Painel Nível 1 com proteção de rota e dashboards atualizados em tempo real pelas toxinas do Cofre |
| `nivel2.html` | `/nivel2.html` e `/frontend-aps/nivel2.html` | Painel Nível 2 restrito a usuários permitidos (Nível 2/3), com desbloqueio facial e botão `+ ADICIONAR TOXINA` |
| `nivel3.html` | `/nivel3.html` e `/frontend-aps/nivel3.html` | Painel Nível 3 com auditoria, cadastro com captura facial e desbloqueio de contas |
| `01_schema_base.sql` | `/database/01_schema_base.sql` e `/frontend-aps/database/01_schema_base.sql` | Schema relacional 3FN de 10 tabelas com `GRANT ALL PRIVILEGES` para `faca_user` |
| `02_seed_operadores_e_cofre.sql` | `/database/02_seed_operadores_e_cofre.sql` e `/frontend-aps/database/02_seed_operadores_e_cofre.sql` | Carga inicial com Operadores Níveis 1, 2, 3, Administrador Geral (T.I.) e Toxinas do Cofre |
| `configuracao-banco.js` | `/src/js/config/configuracao-banco.js` | Configuração ativa do MySQL, endpoints FastAPI, matriz RBAC e credenciais do ADM Geral (T.I.) |
| `servico-api.js` | `/src/js/services/servico-api.js` | Serviço completo de comunicação HTTP (`fetch`), parse seguro de JSON, adição de toxinas e guardião de rotas |
| `menu-niveis.js` | `/src/js/components/menu-niveis.js` | Renderizador do menu lateral cumulativo restrito ao nível do usuário logado e botão de Logout |
| `painel-nivel3.js` | `/src/js/painel-nivel3.js` | Controlador das abas, proteção de URLs, gráficos/tabelas dinâmicas e formulários de Nível 1, 2 e 3 |
| `principal.js` | `/src/js/principal.js` | Controle do login, bypass facial para o ADM Geral (T.I.) e validação MFA 1:1 para os demais usuários |
| `scanner-facial.js` | `/src/js/scanner-facial.js` | Renderizador da malha 3D facial, HUD de biometria e captura de frames em Base64 |
| `particulas.js` | `/src/js/particulas.js` | Rede neural animada de fundo com partículas conectadas |
