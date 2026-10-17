/**
 * ============================================================================
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * ARQUIVO DE CONFIGURAÇÃO: INTEGRAÇÃO FRONTEND (PYTHON) <-> BACKEND (MYSQL/DOCKER)
 * ============================================================================
 *
 * ARQUITETURA DO PROJETO:
 * - O Banco de Dados (MySQL) e o container Docker ficam no BACKEND (Python / FastAPI).
 * - Este FRONTEND será compactado e servido diretamente pelo Python posteriormente.
 * - NENHUM acesso ou credencial foi inventado neste arquivo.
 * - Abaixo estão apenas os comentários e a gramática fixa que serão necessários
 *   para configurar a comunicação quando o Backend Python + MySQL (Docker) estiverem prontos.
 */

// ============================================================================
// 1. GRAMÁTICA FIXA DE CONFIGURAÇÃO DA PONTE COM O BACKEND PYTHON (MYSQL/DOCKER)
// ============================================================================
const CONFIGURACAO_SISTEMA = {
  /*
   * [CONFIGURAR QUANDO O BACKEND PYTHON + DOCKER MYSQL ESTIVEREM DISPONÍVEIS]
   *
   * Como o Frontend será compactado para rodar junto ao Python:
   * - Se servido na mesma origem pelo FastAPI (StaticFiles / Templates):
   *   URL_BASE_API: '' (caminho relativo, ex: '/autenticar', '/toxinas')
   * - Se rodado separado em desenvolvimento apontando para o container Python/Docker:
   *   URL_BASE_API: 'http://localhost:8000'
   *
   * Variáveis que o Backend Python utilizará para conectar ao container MySQL no Docker
   * (apenas referência de gramática para alinhamento com o Backend):
   *   DB_HOST     = 'mysql_container' (ou 'localhost')
   *   DB_PORT     = 3306
   *   DB_NAME     = '<nome_do_banco_mysql>'
   *   DB_USER     = '<usuario_mysql>'
   *   DB_PASSWORD = '<senha_mysql>'
   */

  URL_BASE_API: null, // Preencher com '' (mesma origem no Python) ou 'http://localhost:8000'

  TEMPO_LIMITE_MS: 10000,

  // Chaves de sessão no navegador (preenchidas somente após retorno real do Python/MySQL)
  CHAVES_SESSAO: {
    TOKEN: 'faca_token',
    USUARIO: 'faca_usuario',
    NIVEL_ACESSO: 'faca_nivel_acesso'
  }
};

// ============================================================================
// 2. GRAMÁTICA FIXA DAS ROTAS DO BACKEND PYTHON (QUE CONSULTAM O MYSQL)
// ============================================================================
const ROTAS_API_PYTHON = {
  // Verificação de saúde da API Python + Container MySQL
  STATUS_SERVIDOR: '/ping',

  // Autenticação Etapa 1 (CPF e Senha validados pelo Python no MySQL)
  LOGIN_CREDENCIAIS: '/login',

  // Autenticação Etapa 2 (Biometria Facial processada no OpenCV e validada no MySQL)
  AUTENTICAR_BIOMETRIA: '/autenticar',

  // Rotas de Nível 1 (Relatórios)
  SINTESE_ESTATISTICAS: '/relatorios/estatisticas',
  PANORAMA_TOXINAS: '/relatorios/panorama-toxinas',
  HISTORICO_ALERTAS: '/relatorios/alertas',
  GERADOR_PDF: '/relatorios/gerar-pdf',

  // Rotas de Nível 2 (Cofre)
  STATUS_COFRE: '/cofre/status',
  INVENTARIO_TOXINAS: '/toxinas',

  // Rotas Exclusivas de Nível 3 (Auditoria Global e Monitoramento)
  SESSOES_ATIVAS: '/auditoria/sessoes-ativas',
  HISTORICO_ACESSOS: '/auditoria/historico-acessos',
  CADASTRAR_USUARIO: '/cadastrar',
  DESBLOQUEAR_CONTA: '/auditoria/desbloquear-conta'
};

// ============================================================================
// 3. REGRA CUMULATIVA DOS NÍVEIS DE ACESSO NO MENU LATERAL
// ============================================================================
/**
 * Regra de visibilidade do Menu Lateral por Role (vinda do MySQL via Python):
 * - Nível 1: Visualiza SOMENTE a parte do menu de Nível 1 (Relatórios).
 * - Nível 2: Visualiza TUDO do menu de Nível 2 e Nível 1 (Relatórios + Cofre).
 * - Nível 3: Visualiza TUDO daquele menu (Nível 1 + Nível 2 + Nível 3 Auditoria).
 */
const MATRIZ_NIVEIS_MENU = {
  1: {
    nivel: 1,
    descricao: 'Nível 1 - Somente Menu de Nível 1 (Relatórios)',
    menusLiberados: [1]
  },
  2: {
    nivel: 2,
    descricao: 'Nível 2 - Menu de Nível 2 e Nível 1 (Relatórios + Cofre)',
    menusLiberados: [1, 2]
  },
  3: {
    nivel: 3,
    descricao: 'Nível 3 - Todo o Menu (Nível 1 + Nível 2 + Nível 3 Auditoria)',
    menusLiberados: [1, 2, 3]
  }
};

// ============================================================================
// 4. GRAMÁTICA FIXA DOS DADOS ESPERADOS DO MYSQL (VIA PYTHON JSON)
// ============================================================================
/*
 * Quando o Backend Python retornar os dados do MySQL para a Tela de Nível 3,
 * a gramática esperada nos objetos JSON é:
 *
 * 1) Sessões Ativas (`sessoes_ativas`):
 *    [
 *      {
 *        "nome_usuario": "String (VARCHAR no MySQL)",
 *        "descricao":    "String (VARCHAR no MySQL)",
 *        "data_sessao":  "DD/MM/YYYY (DATE no MySQL)",
 *        "ultimo_acesso":"DD/MM/YYYY (DATE no MySQL)"
 *      }
 *    ]
 *
 * 2) Histórico de Acessos e Eventos (`historico_acessos`):
 *    [
 *      {
 *        "id_evento":          Number,
 *        "usuario_id":         Number,
 *        "data_hora":          "DD/MM/YYYY HH:mm:ss (DATETIME no MySQL)",
 *        "titulo_evento":      "String",
 *        "descricao_evento":   "String",
 *        "requer_desbloqueio": Boolean
 *      }
 *    ]
 *
 * 3) Indicadores Inferiores (Alertas, Panorama de Toxinas e Cofre):
 *    {
 *      "alertas_serie": [Number, ...], // Valores de 0 a 200
 *      "panorama_toxinas": {
 *        "dioxinas_pct": Number,       // 0 a 100
 *        "pfas_pct":     Number,       // 0 a 100
 *        "fosfatos_pct": Number        // 0 a 100
 *      },
 *      "cofre_ocupacao_pct": Number    // 0 a 100
 *    }
 */

window.FACA_CONFIG = {
  CONFIGURACAO_SISTEMA,
  ROTAS_API_PYTHON,
  MATRIZ_NIVEIS_MENU
};
