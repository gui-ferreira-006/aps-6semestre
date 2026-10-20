/**
 * ============================================================================
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Arquivo: src/js/config/configuracao-banco.js
 * Descrição: Gramática fixa e estrutura de configuração para futura conexão
 *            com o Banco de Dados MySQL (via Docker + Backend Python).
 * ============================================================================
 *
 * IMPORTANTE:
 * O banco de dados MySQL está em construção e será disponibilizado via Docker.
 * Nenhum acesso ou credencial foi inventado neste arquivo.
 * Quando o contêiner MySQL estiver ativo, basta descomentar e preencher
 * os parâmetros abaixo conforme o arquivo docker-compose.yml / .env.
 */

const CONFIGURACAO_BANCO = {
  // Status da integração com o banco MySQL (manter false até receber o container Docker)
  SQL_ATIVO: false,

  // URL base onde o Backend Python (FastAPI/Flask) responderá conectado ao MySQL no Docker
  API_BASE_URL: 'http://localhost:8000',

  // ==========================================================================
  // 1. GRAMÁTICA FIXA DE CONEXÃO MYSQL / DOCKER (PARA CONFIGURAÇÃO FUTURA)
  // ==========================================================================
  /*
  MYSQL_DOCKER_CONFIG: {
    HOST: 'localhost',          // Nome do serviço no docker-compose: 'db' ou 'faca_mysql_db'
    PORT: 3306,                 // Porta padrão exposta pelo container MySQL
    DATABASE: 'faca_db',        // Nome do schema principal criado no MySQL
    USER: 'PREENCHER_USUARIO',  // Definir quando receber o acesso do banco
    PASSWORD: 'PREENCHER_SENHA' // Definir quando receber o acesso do banco
  },
  */

  // ==========================================================================
  // 2. MAPEAMENTO DAS ROTAS QUE CONSUMIRÃO O MYSQL (POR ROLE / NÍVEL)
  // ==========================================================================
  ENDPOINTS_SQL: {
    // Autenticação e Login (index.html)
    LOGIN_CPF_SENHA: '/api/v1/auth/login',           // SELECT usuario WHERE cpf = ? AND senha_hash = ?
    VALIDAR_BIOMETRIA: '/api/v1/auth/biometria',     // SELECT vetor_facial_128d WHERE usuario_id = ?

    // Nível 1 — Relatórios (Role >= 1)
    NIVEL_1: {
      ESTATISTICAS: '/api/v1/nivel1/estatisticas',   // SELECT indicadores gerais
      PANORAMA_TOXINAS: '/api/v1/nivel1/toxinas',    // SELECT * FROM toxinas WHERE nivel_requerido = 1
      HISTORICO_ALERTAS: '/api/v1/nivel1/alertas',   // SELECT * FROM alertas WHERE nivel_visibilidade >= 1
      GERADOR_PDF: '/api/v1/nivel1/relatorio-pdf'    // Gera relatório com dados do MySQL
    },

    // Nível 2 — Cofre (Role >= 2: acessa Nível 1 + Nível 2)
    NIVEL_2: {
      COFRE_STATUS: '/api/v1/nivel2/cofre-status',   // SELECT status_contencao, ocupacao FROM cofre_status
      INVentario_TOXINAS: '/api/v1/nivel2/toxinas',  // SELECT * FROM toxinas WHERE nivel_requerido <= 2
      AUTENTICACAO_FACIAL: '/api/v1/nivel2/biometria'// Telemetria PIVC vinculada ao operador Nível 2
    },

    // Nível 3 — Auditoria Global e Monitoramento (Role == 3: acessa Nível 1 + 2 + 3)
    NIVEL_3: {
      SESSOES_ATIVAS: '/api/v1/nivel3/sessoes',      // SELECT * FROM sessoes_ativas ORDER BY data_acesso DESC
      HISTORICO_ACESSOS: '/api/v1/nivel3/auditoria', // SELECT * FROM logs_auditoria ORDER BY data_hora DESC
      ADICIONAR_USUARIO: '/api/v1/nivel3/usuarios',  // INSERT INTO usuarios (...) VALUES (...)
      DESBLOQUEAR_CONTA: '/api/v1/nivel3/desbloquear'// UPDATE usuarios SET bloqueado = 0, tentativas = 0 WHERE id = ?
    }
  },

  // ==========================================================================
  // 3. GRAMÁTICA SQL DE REFERÊNCIA (QUERIES ESPERADAS NO BACKEND PYTHON)
  // ==========================================================================
  /*
   * -- [AUTENTICAÇÃO E ROLE]
   * SELECT u.id, u.nome, u.cpf, u.nivel_acesso AS role_nivel, n.descricao
   * FROM usuarios u
   * INNER JOIN niveis_acesso n ON u.nivel_acesso = n.id
   * WHERE u.cpf = :cpf AND u.senha_hash = :senha_hash AND u.bloqueado = 0;
   *
   * -- [NÍVEL 3: SESSÕES ATIVAS]
   * SELECT s.id, u.nome AS name, n.descricao, s.data_inicio AS data, s.ultimo_acesso AS litm
   * FROM sessoes_ativas s
   * INNER JOIN usuarios u ON s.usuario_id = u.id
   * INNER JOIN niveis_acesso n ON u.nivel_acesso = n.id
   * ORDER BY s.ultimo_acesso DESC;
   *
   * -- [NÍVEL 3: HISTÓRICO DE ACESSOS / TIMELINE E EVENTOS]
   * SELECT l.id, l.data_hora AS timeline, l.titulo_evento, l.descricao_evento, l.conta_bloqueada, l.usuario_id
   * FROM logs_auditoria l
   * ORDER BY l.data_hora DESC;
   *
   * -- [NÍVEL 3: DESBLOQUEAR CONTA (BOTÃO UNBLOCK)]
   * UPDATE usuarios SET bloqueado = 0, tentativas_falhas = 0 WHERE id = :usuario_id;
   *
   * -- [NÍVEL 3: ADICIONAR NOVO USUÁRIO (+ NOVO USUÁRIO)]
   * INSERT INTO usuarios (nome, cpf, senha_hash, matricula, nivel_acesso, vetor_facial)
   * VALUES (:nome, :cpf, :senha_hash, :matricula, :nivel_acesso, :vetor_facial);
   *
   * -- [PANORAMA DE TOXINAS / COFRE]
   * SELECT codigo_amostra, nome_comum, percentual_contencao, nivel_requerido, status_contencao
   * FROM toxinas
   * WHERE nivel_requerido <= :role_usuario;
   */

  // ==========================================================================
  // 4. DEFINIÇÃO DE ROLES E PERMISSÕES CUMULATIVAS DE MENU
  // ==========================================================================
  ROLES_PERMISSOES: {
    1: {
      role: 'NIVEL_1',
      nomeExibicao: 'Nível 1 (Relatórios)',
      niveisMenuPermitidos: [1], // Vê apenas o menu de Nível 1
      paginaInicial: 'nivel1.html'
    },
    2: {
      role: 'NIVEL_2',
      nomeExibicao: 'Nível 2 (Cofre)',
      niveisMenuPermitidos: [1, 2], // Vê tudo do Nível 1 e Nível 2
      paginaInicial: 'nivel2.html'
    },
    3: {
      role: 'NIVEL_3',
      nomeExibicao: 'Nível 3 (Auditoria)',
      niveisMenuPermitidos: [1, 2, 3], // Vê todo o menu (Nível 1, 2 e 3)
      paginaInicial: 'nivel3.html'
    }
  }
};

window.CONFIGURACAO_BANCO = CONFIGURACAO_BANCO;
