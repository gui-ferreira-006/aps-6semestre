/**
 * ============================================================================
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Arquivo: src/js/config/configuracao-banco.js
 * Descrição: Configuração de conexão com o Banco de Dados MySQL 8.0 (Docker)
 *            integrado ao Backend FastAPI Python, definição do Administrador
 *            Geral (T.I.) e permissões RBAC por nível de acesso.
 * ============================================================================
 */

const CONFIGURACAO_BANCO = {
  // Status da integração com o banco MySQL 8.0 (Ativo e Integrado)
  SQL_ATIVO: true,

  // URL base dinâmica: usa a origem atual se estiver rodando via FastAPI/HTTP, ou localhost:8000 como fallback
  API_BASE_URL: (window.location.protocol.startsWith('http') && window.location.port === '8000')
    ? ''
    : 'http://localhost:8000',

  // ==========================================================================
  // 1. PARÂMETROS DE CONEXÃO MYSQL 8.0 / DOCKER (database/01_schema_base.sql)
  // ==========================================================================
  MYSQL_DOCKER_CONFIG: {
    HOST: 'localhost',
    PORT: 3307,
    DATABASE: 'aps_biometria',
    USER: 'faca_user'
  },

  // ==========================================================================
  // 2. CREDENCIAIS EXCLUSIVAS DO ADMINISTRADOR GERAL (EQUIPE DE T.I.)
  // Acesso direto sem necessidade de passar pelo reconhecimento facial
  // ==========================================================================
  ADM_GERAL_TI: {
    CPF: '00000000000',
    MATRICULA: 'MMA-TI-000',
    SENHA_PADRAO: 'AdmTI@2026',
    SENHA_ALTERNATIVA: 'Faca@2026',
    TOKEN_SESSAO: 'mock-jwt-faca-adm-ti-00000000000',
    USUARIO: {
      id: 4,
      nome: 'Administrador Geral (T.I.)',
      cpf: '00000000000',
      matricula: 'MMA-TI-000',
      cargo: 'Administrador Geral de T.I.',
      divisao: 'Tecnologia da Informação (T.I.)',
      nivel_acesso: 3,
      bypass_facial: true
    }
  },

  // ==========================================================================
  // 3. MAPEAMENTO DOS ENDPOINTS OFICIAIS DO BACKEND FASTAPI + MYSQL
  // ==========================================================================
  ENDPOINTS_SQL: {
    PING: '/ping',
    AUTENTICAR_MFA: '/autenticar',
    CADASTRAR_USUARIO: '/cadastrar',
    CONSULTAR_TOXINAS: '/toxinas',
    DESBLOQUEAR_USUARIO: (identificador) => `/usuarios/${encodeURIComponent(identificador)}/desbloquear`,
    DESBLOQUEAR_ALTERNATIVO: '/api/v1/nivel3/desbloquear',
    BIOMETRIA_STATUS: '/biometria/status',
    BIOMETRIA_EXTRAIR: '/biometria/extrair-vetor',
    BIOMETRIA_VERIFICAR: '/biometria/verificar-vetor'
  },

  // ==========================================================================
  // 4. DEFINIÇÃO DE ROLES E PERMISSÕES CUMULATIVAS DE MENU (RBAC)
  // ==========================================================================
  ROLES_PERMISSOES: {
    1: {
      role: 'NIVEL_1',
      nomeExibicao: 'Nível 1 (Relatórios)',
      niveisMenuPermitidos: [1],
      paginaInicial: 'nivel1.html'
    },
    2: {
      role: 'NIVEL_2',
      nomeExibicao: 'Nível 2 (Cofre)',
      niveisMenuPermitidos: [1, 2],
      paginaInicial: 'nivel2.html'
    },
    3: {
      role: 'NIVEL_3',
      nomeExibicao: 'Nível 3 (Auditoria)',
      niveisMenuPermitidos: [1, 2, 3],
      paginaInicial: 'nivel3.html'
    }
  }
};

window.CONFIGURACAO_BANCO = CONFIGURACAO_BANCO;
