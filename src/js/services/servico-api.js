/**
 * ============================================================================
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Arquivo: src/js/services/servico-api.js
 * Descrição: Camada de serviço preparada com a gramática fixa comentada para
 *            integração com o Backend Python + Banco de Dados MySQL (Docker).
 * ============================================================================
 *
 * ATENÇÃO:
 * Nenhum acesso fictício está ativo. Os métodos abaixo contêm a estrutura
 * exata (gramática fixa de fetch, headers, payloads e retorno SQL) comentada,
 * pronta para ser descomentada assim que o container MySQL estiver rodando.
 */

const ServicoAPI = {
  /**
   * --------------------------------------------------------------------------
   * 1. AUTENTICAÇÃO POR CPF E SENHA (ETAPA 1 DO LOGIN)
   * --------------------------------------------------------------------------
   * Quando o MySQL estiver disponível no Docker, descomente o bloco fetch
   * abaixo para validar CPF e Senha diretamente na tabela `usuarios`.
   */
  async autenticarCredenciais(cpf, senha) {
    /*
    // === [DESCOMENTAR QUANDO O MYSQL / DOCKER ESTIVER ATIVO] ===
    const resposta = await fetch(`${window.CONFIGURACAO_BANCO.API_BASE_URL}${window.CONFIGURACAO_BANCO.ENDPOINTS_SQL.LOGIN_CPF_SENHA}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        cpf: cpf.replace(/\D/g, ''),
        senha: senha
      })
    });

    const dados = await resposta.json();
    if (!resposta.ok) {
      throw new Error(dados.mensagem || 'Credenciais inválidas no banco MySQL.');
    }

    // Salva a role retornada pelo MySQL (1, 2 ou 3) na sessão:
    // sessionStorage.setItem('faca_role_nivel', dados.usuario.nivel_acesso);
    // sessionStorage.setItem('faca_usuario_id', dados.usuario.id);
    return dados;
    */

    return {
      aguardandoSql: true,
      mensagem: 'Aguardando integração com o container MySQL (Docker).'
    };
  },

  /**
   * --------------------------------------------------------------------------
   * 2. VALIDAÇÃO BIOMÉTRICA FACIAL 1:1 (ETAPA 2 DO LOGIN)
   * --------------------------------------------------------------------------
   * Envia o frame Base64 capturado pela webcam para comparação com o vetor
   * facial armazenado no MySQL e redireciona conforme a Role (Nível 1, 2 ou 3).
   */
  async validarBiometriaFacial(cpf, senha, frameBase64) {
    /*
    // === [DESCOMENTAR QUANDO O MYSQL / DOCKER ESTIVER ATIVO] ===
    const base64Puro = frameBase64.replace(/^data:image\/[a-z]+;base64,/, '');

    const resposta = await fetch(`${window.CONFIGURACAO_BANCO.API_BASE_URL}/autenticar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        cpf: cpf.replace(/\D/g, ''),
        senha: senha,
        imagem_base64: base64Puro
      })
    });

    const dados = await resposta.json();
    if (!resposta.ok) {
      throw dados;
    }

    // Armazena Token JWT e Role vindos do banco MySQL
    sessionStorage.setItem('faca_token', dados.token);
    sessionStorage.setItem('faca_role_nivel', String(dados.usuario.nivel_acesso));
    sessionStorage.setItem('faca_usuario', JSON.stringify(dados.usuario));

    // Redirecionamento automático baseado na Role do usuário no MySQL:
    // Role 1 -> nivel1.html | Role 2 -> nivel2.html | Role 3 -> nivel3.html
    const destino = window.CONFIGURACAO_BANCO.ROLES_PERMISSOES[dados.usuario.nivel_acesso]?.paginaInicial || 'nivel1.html';
    window.location.href = destino;
    return dados;
    */

    return {
      aguardandoSql: true,
      mensagem: 'Módulo de validação biométrica aguardando conexão com banco MySQL.'
    };
  },

  /**
   * --------------------------------------------------------------------------
   * 3. CONSULTAS DO NÍVEL 3 — AUDITORIA GLOBAL E MONITORAMENTO
   * --------------------------------------------------------------------------
   */
  async carregarDadosNivel3() {
    /*
    // === [DESCOMENTAR QUANDO O MYSQL / DOCKER ESTIVER ATIVO] ===
    const token = sessionStorage.getItem('faca_token');
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };

    const [resSessoes, resHistorico] = await Promise.all([
      fetch(`${window.CONFIGURACAO_BANCO.API_BASE_URL}${window.CONFIGURACAO_BANCO.ENDPOINTS_SQL.NIVEL_3.SESSOES_ATIVAS}`, { headers }),
      fetch(`${window.CONFIGURACAO_BANCO.API_BASE_URL}${window.CONFIGURACAO_BANCO.ENDPOINTS_SQL.NIVEL_3.HISTORICO_ACESSOS}`, { headers })
    ]);

    return {
      sessoesAtivas: await resSessoes.json(),     // Popula #tabela-sessoes-ativas
      historicoAcessos: await resHistorico.json() // Popula #lista-timeline e #lista-eventos
    };
    */
    return null;
  },

  /**
   * --------------------------------------------------------------------------
   * 4. AÇÃO NÍVEL 3: ADICIONAR NOVO USUÁRIO (+ NOVO USUÁRIO / ADICIONAR)
   * --------------------------------------------------------------------------
   */
  async adicionarUsuarioMySQL(dadosNovoUsuario) {
    /*
    // === [DESCOMENTAR QUANDO O MYSQL / DOCKER ESTIVER ATIVO] ===
    // Query esperada no Backend:
    // INSERT INTO usuarios (nome, cpf, senha_hash, matricula, nivel_acesso, vetor_facial) VALUES (...)
    const token = sessionStorage.getItem('faca_token');
    const resposta = await fetch(`${window.CONFIGURACAO_BANCO.API_BASE_URL}${window.CONFIGURACAO_BANCO.ENDPOINTS_SQL.NIVEL_3.ADICIONAR_USUARIO}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        nome: dadosNovoUsuario.nome,
        cpf: dadosNovoUsuario.cpf,
        senha: dadosNovoUsuario.senha,
        matricula: dadosNovoUsuario.matricula,
        nivel_acesso: Number(dadosNovoUsuario.nivel_acesso),
        imagem_base64: dadosNovoUsuario.imagem_base64
      })
    });
    return await resposta.json();
    */
    return { aguardandoSql: true };
  },

  /**
   * --------------------------------------------------------------------------
   * 5. AÇÃO NÍVEL 3: DESBLOQUEAR CONTA (BOTÃO UNBLOCK)
   * --------------------------------------------------------------------------
   */
  async desbloquearContaMySQL(usuarioId) {
    /*
    // === [DESCOMENTAR QUANDO O MYSQL / DOCKER ESTIVER ATIVO] ===
    // Query esperada no Backend:
    // UPDATE usuarios SET bloqueado = 0, tentativas_falhas = 0 WHERE id = :usuarioId;
    const token = sessionStorage.getItem('faca_token');
    const resposta = await fetch(`${window.CONFIGURACAO_BANCO.API_BASE_URL}${window.CONFIGURACAO_BANCO.ENDPOINTS_SQL.NIVEL_3.DESBLOQUEAR_CONTA}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ usuario_id: usuarioId })
    });
    return await resposta.json();
    */
    return { aguardandoSql: true };
  },

  /**
   * --------------------------------------------------------------------------
   * 6. CONSULTAS DO NÍVEL 2 — COFRE E INVENTÁRIO DE TOXINAS
   * --------------------------------------------------------------------------
   */
  async carregarDadosNivel2() {
    /*
    // === [DESCOMENTAR QUANDO O MYSQL / DOCKER ESTIVER ATIVO] ===
    // Query esperada no Backend:
    // SELECT * FROM toxinas WHERE nivel_requerido <= 2;
    const token = sessionStorage.getItem('faca_token');
    const resposta = await fetch(`${window.CONFIGURACAO_BANCO.API_BASE_URL}${window.CONFIGURACAO_BANCO.ENDPOINTS_SQL.NIVEL_2.INVentario_TOXINAS}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    return await resposta.json();
    */
    return null;
  },

  /**
   * --------------------------------------------------------------------------
   * 7. CONSULTAS DO NÍVEL 1 — RELATÓRIOS E ESTATÍSTICAS
   * --------------------------------------------------------------------------
   */
  async carregarDadosNivel1() {
    /*
    // === [DESCOMENTAR QUANDO O MYSQL / DOCKER ESTIVER ATIVO] ===
    // Query esperada no Backend:
    // SELECT * FROM toxinas WHERE nivel_requerido = 1;
    const token = sessionStorage.getItem('faca_token');
    const resposta = await fetch(`${window.CONFIGURACAO_BANCO.API_BASE_URL}${window.CONFIGURACAO_BANCO.ENDPOINTS_SQL.NIVEL_1.ESTATISTICAS}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    return await resposta.json();
    */
    return null;
  }
};

window.ServicoAPI = ServicoAPI;
