# Documentação Resumida de Atualização — Frontend F.A.C.A (`frontend-aps`)

Este diretório (`frontend-aps/`) contém **exclusivamente os arquivos de Front-End** criados e atualizados para o sistema **F.A.C.A — Frente de Autenticação e Controle de Acesso**, sem modificar nenhum arquivo Python (`main.py`, `biometria.py`, `schemas.py`).

---

## 1. Solução do Erro `{"detail":"Not Found"}` no FastAPI (`http://localhost:8000`)

### Causa
O servidor Python (`main.py`) serve apenas a rota raiz `/` (`index.html`) e os arquivos estáticos em `/src/*`. Quando o navegador tentava abrir `/nivel1.html`, `/nivel2.html` ou `/nivel3.html`, o FastAPI retornava `{"detail":"Not Found"}` por não existir rota para esses arquivos no `main.py`.

### Solução Implementada (100% no Front-End, sem tocar no Python)
O arquivo [`index.html`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/index.html) foi transformado em uma **Single Page Application (SPA)** completa:
- **`#spa-view-login`**: Contém a Etapa 1 (CPF/Senha) e Etapa 2 (Biometria Facial via Python `POST /autenticar`).
- **`#spa-view-dashboard`**: Contém o Menu Lateral Cumulativo por Role (`Nível 1`, `Nível 2`, `Nível 3`) e todas as **10 telas de abas** (`.tab-screen`) na própria rota `http://localhost:8000/`.
- **`#spa-top-switcher`**: Barra superior rápida para alternar entre **Tela de Login**, **Role Nível 1**, **Role Nível 2** e **Role Nível 3** instantaneamente sem recarregar a página ou gerar erro 404.

---

## 2. Estrutura de Arquivos em `frontend-aps/`

- [`index.html`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/index.html) — Aplicação unificada (Login + Painéis Nível 1, 2 e 3 + todas as 10 abas) funcionando diretamente em `http://localhost:8000/`.
- [`nivel1.html`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/nivel1.html), [`nivel2.html`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/nivel2.html), [`nivel3.html`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/nivel3.html) — Telas standalone caso queira servir via Live Server/Nginx.
- [`src/css/components/painel-nivel3.css`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/src/css/components/painel-nivel3.css) — Estilização completa das 10 abas, tabelas vazias pré-configuradas, Cofre Seguro, Biometria Nível 2 e modais.
- [`src/js/components/menu-niveis.js`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/src/js/components/menu-niveis.js) — Renderizador do menu cumulativo:
  - **Role Nível 1**: *Estatísticas, Documentos Públicos, Perfil Básico*.
  - **Role Nível 2**: *Menu Nível 1 + Cofre Seguro (Status), Autenticação Facial, Relatórios Setoriais*.
  - **Role Nível 3**: *Menu Nível 1 + Menu Nível 2 + Histórico de Acesso, Gerador de PDF, Gestão de Usuários, Configurações*.
- [`src/js/painel-nivel3.js`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/src/js/painel-nivel3.js) — Controlador SPA de abas, Roles e integração da aba **Autenticação Facial (Nível 2)** usando o mesmo endpoint Python `POST /autenticar` e `FaceScanner`.
- [`src/js/scanner-facial.js`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/src/js/scanner-facial.js) — Atualizado para suportar múltiplas instâncias de HUD (`face-mesh-canvas` no Login e `n2-face-mesh-canvas` no Nível 2).
- [`src/js/config/configuracao-banco.js`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/src/js/config/configuracao-banco.js) — Contrato de tabelas, colunas e queries SQL comentadas para quando o MySQL/Docker for conectado.
- [`src/js/services/servico-api.js`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/src/js/services/servico-api.js) — Funções `fetch` comentadas prontas para popular os IDs HTML assim que o banco MySQL estiver ativo.

---

## 3. O Que Atualizar Quando o Banco MySQL + Docker Estiver Pronto

1. **No Backend Python (`main.py`)**:
   - Criar as rotas REST que consultam o MySQL conforme documentado em [`src/js/config/configuracao-banco.js`](file:///c:/Users/cruzj/Downloads/aps-6semestre-dev/aps-6semestre-dev/frontend-aps/src/js/config/configuracao-banco.js):
     - `GET /api/v1/nivel1/estatisticas` e `GET /api/v1/nivel1/documentos-publicos`
     - `GET /api/v1/nivel2/cofre/status`, `GET /api/v1/nivel2/cofre/arquivos` e `GET /api/v1/nivel2/relatorios-setoriais`
     - `GET /api/v1/nivel3/historico-acessos`, `GET /api/v1/nivel3/usuarios`, `POST /api/v1/nivel3/usuarios` e `PUT /api/v1/nivel3/configuracoes`
2. **No Front-End (`src/js/services/servico-api.js` e `src/js/painel-nivel3.js`)**:
   - Descomentar os blocos marcados com `=== [DESCOMENTAR QUANDO O BANCO DE DADOS MYSQL ESTIVER CONECTADO] ===`.
