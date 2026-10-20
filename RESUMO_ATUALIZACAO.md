# Documentação Resumida de Atualização — F.A.C.A. (Frontend & Backend Integrados)

Este documento registra o estado atual do sistema **F.A.C.A — Frente de Autenticação e Controle de Acesso**, consolidando a evolução do Frontend SPA e sua integração definitiva com o Backend FastAPI, Motor Biométrico PIVC e Banco de Dados Relacional **MySQL 8.0** em Docker.

---

## 1. Arquitetura da Interface e Solução SPA

### Contexto
O servidor FastAPI (`main.py`) entrega a aplicação estática na rota raiz `/` (`index.html`) e os assets em `/src/*`. Para evitar erros `404 Not Found` ao navegar entre os níveis de acesso (Nível 1, Nível 2 e Nível 3), a interface opera como uma **Single Page Application (SPA)** nativa:

- **`#spa-view-login`**: Etapa 1 (Identificação por CPF e Senha) ➔ Transição para Etapa 2 (Captura de Frame facial da webcam via Canvas HUD e envio para `POST /autenticar`).
- **`#spa-view-dashboard`**: Painel dinâmico que renderiza o Menu Lateral Cumulativo por Nível e as **10 telas de abas** (`.tab-screen`) sem recarregar a página.
- **`#spa-top-switcher`**: Barra superior de demonstração para a banca avaliadora, permitindo alternar instantaneamente entre a **Tela de Login** e os painéis de **Nível 1**, **Nível 2** e **Nível 3**.

---

## 2. Conclusão da Integração com o Banco MySQL 8.0 em Docker

O Backend e o Banco de Dados Relacional estão **100% integrados e operacionais**, substituindo todos os controles fictícios/em memória anteriores por persistência relacional:

### 2.1. Scripts Oficiais em `database/`
- **`01_schema_base.sql`**: DDL com 10 tabelas normalizadas em 3FN (`divisao`, `cargo`, `nivel_acesso`, `usuario`, `toxina`, `documento`, `biometria`, `tentativa_autenticacao`, `bloqueio_login` e `auditoria`).
- **`02_seed_operadores_e_cofre.sql`**: Carga com os **3 operadores oficiais** (Guilherme Ferreira, Dra. Júlia Fernandes e Ministro do Meio Ambiente) utilizando hashes criptográficos `PBKDF2-HMAC-SHA256` para a senha `Faca@2026`, sem biometria prévia para viabilizar o *enrollment on-the-fly* na webcam, além de 4 toxinas controladas e 5 documentos técnicos.

### 2.2. Módulos do Backend
- **`database.py`**: Conexão SQLAlchemy 2.0 com pool resiliente (`pool_pre_ping=True`, `pool_recycle=3600`), injeção `get_db()` e health check `SELECT 1`.
- **`models.py`**: Modelagem ORM tipada das 10 tabelas relacionais com `Mapped`, `mapped_column` e relacionamentos bidirecionais.
- **`crud.py`**: Regras de negócio, busca com `joinedload`, verificação de senhas, política de bloqueio após 5 falhas consecutivas (janela de 15 minutos), logs em auditoria e gravação do vetor de 128 floats na tabela `biometria`.
- **`main.py`**: Endpoints RESTful conectados ao banco:
  - `POST /autenticar`: Autenticação multifator 1:1, checagem de bloqueio ativo, verificação facial com as 5 fases do PIVC e emissão de token de sessão.
  - `POST /cadastrar`: Registro de novos operadores e biometria 128D no MySQL.
  - `GET /toxinas`: Consulta protegida ao cofre com filtragem dinâmica por nível de acesso RBAC.
  - `POST /usuarios/{identificador}/desbloquear`: Rota administrativa de salvaguarda operacional.
  - `GET /ping`: Health check com diagnóstico físico de conectividade SQL.

---

## 3. Estado Atual dos Arquivos do Frontend

| Arquivo | Função / Estado de Integração |
|---|---|
| `index.html` | SPA unificada (Login + Dashboard + 10 abas) pronta e servida na rota raiz `http://localhost:8000/`. |
| `src/js/principal.js` | Conectado ao `POST /autenticar` consumindo respostas reais do MySQL (sucesso, bloqueio 403, falhas 401). |
| `src/js/scanner-facial.js` | Motor de captura com malha holográfica e suporte à webcam real. |
| `src/js/components/menu-niveis.js` | Menu lateral cumulativo por Role (Nível 3 vê 1+2+3; Nível 2 vê 1+2; Nível 1 vê apenas 1). |
| `src/js/painel-nivel3.js` | Controlador SPA das abas e da aba *Autenticação Facial Nível 2* (reutilizando `POST /autenticar`). |
| `src/js/config/configuracao-banco.js` | Dicionário de endpoints e gramática SQL de referência para consultas complementares. |
| `src/js/services/servico-api.js` | Funções de comunicação para formulários secundários e relatórios. |

---

## 4. O Que Já Foi Concluído vs. Próximos Passos

### ✅ Concluído com Sucesso:
1. **Infraestrutura Docker:** Contêineres `faca_mysql_db` (MySQL 8.0 na porta 3307) e `faca_backend_api` (FastAPI na porta 8000) orquestrados via `docker-compose.yml`.
2. **Autenticação Real com Banco:** Login por CPF, senha PBKDF2 e biometria facial gravando em `tentativa_autenticacao`, `bloqueio_login` e `auditoria`.
3. **Enrollment On-the-Fly:** Primeiro login de cada integrante diante da câmera extrai o vetor 128D via ResNet-34 e grava na tabela `biometria`.
4. **Proteção de Ameaça:** 5 falhas de senha ou divergência facial bloqueiam a conta por 15 minutos (HTTP 403 `ACCOUNT_LOCKED`).
5. **Salvaguarda de Apresentação:** Endpoint de desbloqueio de emergência funcional.
6. **Bateria de Testes Automatizados:** 10/10 testes aprovados em `tests/test_e2e_mysql.py` e 0 erros no Pyright.

### 📌 Próximos Passos (Pendências):
1. **Descomentar Chamadas Complementares no Frontend:**
   - Em `src/js/painel-nivel3.js` e `src/js/services/servico-api.js`, descomentar e ajustar o formulário `#form-novo-usuario-sql` para consumir diretamente `POST /cadastrar`.
   - Conectar a tabela de desbloqueio da aba Nível 3 à rota `POST /usuarios/{identificador}/desbloquear`.
   - Conectar a tabela de toxinas e inventário à rota protegida `GET /toxinas` enviando o `token` armazenado no `sessionStorage`.
2. **Elaboração da Dissertação Escrita da APS (70% da nota):**
   - Redigir o documento formal no modelo UNIP/ABNT (Introdução, PIVC, Arquitetura, Relatório de Código e Bibliografia).
3. **Ensaio da Apresentação Prática (30% da nota):**
   - Testar o fluxo presencial de apresentação com a banca utilizando `.\iniciar_faca.ps1` no terminal Desktop nativo.
