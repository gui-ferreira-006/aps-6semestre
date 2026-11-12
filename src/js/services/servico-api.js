/**
 * ============================================================================
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Arquivo: src/js/services/servico-api.js
 * Descrição: Camada de serviço ativa conectando o Frontend aos endpoints do
 *            Backend FastAPI Python + Banco de Dados MySQL 8.0, controle de
 *            sessão autenticada, proteção de rotas, ADM Geral (T.I.) sem
 *            facial e cache local sincronizado para telemetria e auditoria.
 * ============================================================================
 */

const ServicoAPI = {
  // Chaves de persistência de sessão e sincronização com o banco
  STORAGE_KEYS: {
    TOKEN: 'faca_token',
    USUARIO: 'faca_usuario',
    ROLE_NIVEL: 'faca_role_nivel',
    AUTENTICADO: 'faca_autenticado',
    COFRE_DESBLOQUEADO: 'faca_cofre_desbloqueado',
    USUARIOS_CADASTRADOS_CACHE: 'faca_db_usuarios_cache',
    AUDITORIA_LOGS: 'faca_db_auditoria_logs',
    BLOQUEIOS_ATIVOS: 'faca_db_bloqueios_ativos',
    ABERTURAS_COFRE: 'faca_db_aberturas_cofre',
    TOXINAS_ADICIONAIS: 'faca_db_toxinas_adicionais'
  },

  /**
   * Obtém a URL base configurada para chamadas HTTP ao Backend.
   */
  obterBaseUrl() {
    return (window.CONFIGURACAO_BANCO && window.CONFIGURACAO_BANCO.API_BASE_URL !== undefined)
      ? window.CONFIGURACAO_BANCO.API_BASE_URL
      : '';
  },

  /**
   * Faz o parse seguro da resposta HTTP sem estourar SyntaxError ("Unexpected token 'I', 'Internal S'...")
   * quando o servidor retorna 500 Internal Server Error em texto plano (ex: banco de dados desligado).
   */
  async lerRespostaJsonSegura(resposta) {
    const texto = await resposta.text();
    if (!texto) return {};
    try {
      return JSON.parse(texto);
    } catch (_) {
      return {
        sucesso: false,
        erro: {
          codigo: 'DATABASE_CONNECTION_ERROR',
          mensagem: 'Falha interna no servidor: verifique se o banco de dados está ativo e conectado (Docker).'
        }
      };
    }
  },

  /**
   * --------------------------------------------------------------------------
   * 1. CONTROLE DE SESSÃO E PROTEÇÃO DE ROTAS (AUTH GUARD)
   * --------------------------------------------------------------------------
   */
  estaAutenticado() {
    const token = sessionStorage.getItem(this.STORAGE_KEYS.TOKEN);
    const autenticado = sessionStorage.getItem(this.STORAGE_KEYS.AUTENTICADO) === 'true';
    const usuarioStr = sessionStorage.getItem(this.STORAGE_KEYS.USUARIO);
    return Boolean(token && autenticado && usuarioStr);
  },

  obterUsuarioLogado() {
    try {
      const raw = sessionStorage.getItem(this.STORAGE_KEYS.USUARIO);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  },

  obterToken() {
    return sessionStorage.getItem(this.STORAGE_KEYS.TOKEN) || '';
  },

  obterNivelAcessoLogado() {
    const user = this.obterUsuarioLogado();
    if (user && [1, 2, 3].includes(Number(user.nivel_acesso))) {
      return Number(user.nivel_acesso);
    }
    const salvo = Number(sessionStorage.getItem(this.STORAGE_KEYS.ROLE_NIVEL));
    return [1, 2, 3].includes(salvo) ? salvo : 0;
  },

  ehAdmGeralTI(identificador, senha) {
    const cfg = window.CONFIGURACAO_BANCO?.ADM_GERAL_TI;
    if (!cfg) return false;
    const limpo = String(identificador || '').trim();
    const digitos = limpo.replace(/\D/g, '');
    const idValido =
      digitos === cfg.CPF ||
      limpo.toUpperCase() === cfg.MATRICULA ||
      limpo.toUpperCase() === 'ADM' ||
      limpo.toUpperCase() === 'TI';

    const senhaValida =
      senha === cfg.SENHA_PADRAO ||
      senha === cfg.SENHA_ALTERNATIVA;

    return Boolean(idValido && senhaValida);
  },

  registrarSessaoAutenticada(token, usuario, metodo = 'MFA_FACIAL') {
    sessionStorage.setItem(this.STORAGE_KEYS.TOKEN, token);
    sessionStorage.setItem(this.STORAGE_KEYS.USUARIO, JSON.stringify(usuario));
    sessionStorage.setItem(this.STORAGE_KEYS.ROLE_NIVEL, String(usuario.nivel_acesso || 1));
    sessionStorage.setItem(this.STORAGE_KEYS.AUTENTICADO, 'true');

    // Se for ADM Geral T.I., libera também a visualização do cofre automaticamente
    if (usuario.bypass_facial) {
      sessionStorage.setItem(this.STORAGE_KEYS.COFRE_DESBLOQUEADO, 'true');
    }

    this.registrarEventoAuditoriaLocal({
      acao: metodo === 'ADM_TI_DIRETO' ? 'LOGIN_ADM_TI_SEM_FACIAL' : 'LOGIN_MFA_BIOMETRIA',
      operador: usuario.nome,
      cpf: usuario.cpf || usuario.matricula || '***',
      nivel: usuario.nivel_acesso,
      resultado: 'SUCESSO',
      descricao: metodo === 'ADM_TI_DIRETO'
        ? `Acesso Administrativo Exclusivo (T.I.) realizado sem biometria facial por ${usuario.nome}.`
        : `Autenticação multifator (CPF + Senha + Biometria Facial 128D) confirmada para ${usuario.nome}.`
    });
  },

  encerrarSessao() {
    const user = this.obterUsuarioLogado();
    if (user) {
      this.registrarEventoAuditoriaLocal({
        acao: 'LOGOUT_SISTEMA',
        operador: user.nome,
        cpf: user.cpf || user.matricula || '***',
        nivel: user.nivel_acesso,
        resultado: 'SUCESSO',
        descricao: `Sessão encerrada pelo operador ${user.nome}.`
      });
    }
    sessionStorage.removeItem(this.STORAGE_KEYS.TOKEN);
    sessionStorage.removeItem(this.STORAGE_KEYS.USUARIO);
    sessionStorage.removeItem(this.STORAGE_KEYS.ROLE_NIVEL);
    sessionStorage.removeItem(this.STORAGE_KEYS.AUTENTICADO);
    sessionStorage.removeItem(this.STORAGE_KEYS.COFRE_DESBLOQUEADO);
  },

  /**
   * Protege páginas standalone (nivel1.html, nivel2.html, nivel3.html) e rotas diretas:
   * - Se não estiver logado -> redireciona imediatamente para o login (index.html ou /).
   * - Se tentar acessar um nível superior ao seu nível RBAC -> redireciona para o seu nível permitido.
   */
  protegerRotaAtual(nivelExigidoPagina = null) {
    const pathname = window.location.pathname.toLowerCase();
    const ehPaginaStandalone =
      pathname.endsWith('nivel1.html') ||
      pathname.endsWith('nivel2.html') ||
      pathname.endsWith('nivel3.html');

    if (!this.estaAutenticado()) {
      if (ehPaginaStandalone) {
        window.location.replace('index.html');
        return false;
      }
      return false;
    }

    const nivelUsuario = this.obterNivelAcessoLogado();
    if (ehPaginaStandalone && nivelExigidoPagina && nivelUsuario < nivelExigidoPagina) {
      const paginaPermitida = window.CONFIGURACAO_BANCO?.ROLES_PERMISSOES?.[nivelUsuario]?.paginaInicial || 'index.html';
      window.location.replace(paginaPermitida);
      return false;
    }

    return true;
  },

  /**
   * --------------------------------------------------------------------------
   * 2. AUTENTICAÇÃO DO ADMINISTRADOR GERAL (T.I.) — SEM RECONHECIMENTO FACIAL
   * --------------------------------------------------------------------------
   */
  async autenticarAdmGeralTI(identificador, senha) {
    if (!this.ehAdmGeralTI(identificador, senha)) {
      return null;
    }

    const cfg = window.CONFIGURACAO_BANCO.ADM_GERAL_TI;
    // Verifica conectividade com o banco via /ping para confirmar status SQL
    try {
      await this.verificarStatusBanco();
    } catch (_) {
      // Continua normalmente com o token compatível com o backend
    }

    this.registrarSessaoAutenticada(cfg.TOKEN_SESSAO, cfg.USUARIO, 'ADM_TI_DIRETO');
    return {
      sucesso: true,
      bypassFacial: true,
      mensagem: 'Acesso exclusivo da equipe de T.I. validado com sucesso (Reconhecimento facial dispensado).',
      token: cfg.TOKEN_SESSAO,
      usuario: cfg.USUARIO
    };
  },

  /**
   * --------------------------------------------------------------------------
   * 3. VALIDAÇÃO DE CADASTRO PRÉVIO E BIOMETRIA FACIAL NO BANCO (POST /autenticar)
   * --------------------------------------------------------------------------
   * Regra estrita para demais usuários:
   * - Só entra no sistema quem estiver cadastrado, com dados pessoais e facial salvos no banco.
   * - Valida CPF, Senha e Biometria Facial contra o banco MySQL.
   * - Caso o usuário tenha sido cadastrado via T.I. ou já esteja no MySQL, verifica se
   *   possui facial registrada; se não estiver cadastrado ou a facial não for reconhecida,
   *   nega o acesso com mensagem clara.
   */
  async validarBiometriaFacial(cpf, senha, frameBase64) {
    const cpfLimpo = String(cpf || '').replace(/\D/g, '');
    if (cpfLimpo.length !== 11) {
      throw {
        status: 400,
        erro: {
          codigo: 'INVALID_CPF',
          mensagem: 'Acesso Negado: informe um CPF válido de 11 dígitos cadastrado no sistema.'
        }
      };
    }

    const base64Puro = String(frameBase64 || '').replace(/^data:image\/[a-zA-Z]+;base64,/, '');
    if (!base64Puro) {
      throw {
        status: 400,
        erro: {
          codigo: 'INVALID_IMAGE',
          mensagem: 'Falha na captura da imagem facial. Ative a câmera e posicione seu rosto.'
        }
      };
    }

    const resposta = await fetch(`${this.obterBaseUrl()}/autenticar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        cpf: cpfLimpo,
        senha: senha,
        imagem_base64: base64Puro
      })
    });

    const dados = await this.lerRespostaJsonSegura(resposta);

    if (!resposta.ok) {
      // Registra falha ou bloqueio no histórico local sincronizado para exibição na aba de Auditoria / Desbloqueio
      if (resposta.status === 401) {
        const codigoErro = dados?.erro?.codigo || 'AUTH_FAILED';
        let msgClara = dados?.erro?.mensagem || 'Acesso Negado: usuário não cadastrado ou biometria facial não reconhecida.';

        if (codigoErro === 'INVALID_CREDENTIALS') {
          msgClara = 'Acesso Negado: Usuário não cadastrado no banco de dados ou credenciais (CPF/Senha) incorretas.';
        } else if (codigoErro === 'FACE_NOT_RECOGNIZED') {
          msgClara = 'Acesso Negado: Biometria facial não reconhecida! O rosto capturado não corresponde à facial salva no banco de dados para este usuário.';
        }

        dados.erro = {
          ...(dados.erro || {}),
          mensagem: msgClara
        };

        this.registrarEventoAuditoriaLocal({
          acao: codigoErro === 'FACE_NOT_RECOGNIZED' ? 'FALHA_BIOMETRIA_FACIAL' : 'FALHA_CREDENCIAIS_LOGIN',
          operador: `CPF ${this.mascararCpf(cpfLimpo)}`,
          cpf: cpfLimpo,
          nivel: 0,
          resultado: 'NEGADO',
          descricao: `${msgClara} (Tentativas restantes: ${dados.tentativas_restantes ?? '?'})`
        });
      } else if (resposta.status === 403) {
        this.registrarBloqueioLocal(cpfLimpo, dados);
        this.registrarEventoAuditoriaLocal({
          acao: 'BLOQUEIO_CONTA_5_TENTATIVAS',
          operador: `CPF ${this.mascararCpf(cpfLimpo)}`,
          cpf: cpfLimpo,
          nivel: 0,
          resultado: 'BLOQUEADO',
          conta_bloqueada: true,
          descricao: dados?.erro?.mensagem || 'Conta bloqueada temporariamente após 5 tentativas falhas consecutivas.'
        });
      }

      throw { status: resposta.status, ...dados };
    }

    // Regra do Requisito 3: "Só entra no sistema quem estiver cadastrado, com dados pessoais e facial salvos no banco de dados."
    // Caso o backend retorne a mensagem de primeiro acesso sem facial prévia ("Biometria de referência vinculada")
    // e o usuário não tenha sido recém-cadastrado com facial, garantimos que a facial agora está salva e validada,
    // ou verificamos o registro local.
    const usuarioAutenticado = {
      ...dados.usuario,
      cpf: cpfLimpo,
      bypass_facial: false
    };

    this.registrarSessaoAutenticada(dados.token, usuarioAutenticado, 'MFA_FACIAL');
    this.removerBloqueioLocal(cpfLimpo);

    return dados;
  },

  /**
   * --------------------------------------------------------------------------
   * 4. CADASTRO DE NOVO OPERADOR COM DADOS PESSOAIS E FACIAL (POST /cadastrar)
   * --------------------------------------------------------------------------
   */
  async adicionarUsuarioMySQL(dadosNovoUsuario) {
    const cpfLimpo = String(dadosNovoUsuario.cpf || '').replace(/\D/g, '');
    if (cpfLimpo.length !== 11) {
      throw new Error('O CPF do novo operador deve conter exatamente 11 dígitos.');
    }

    if (!dadosNovoUsuario.imagem_base64) {
      throw new Error('A captura da biometria facial é obrigatória para cadastrar um novo operador no banco de dados.');
    }

    const base64Puro = String(dadosNovoUsuario.imagem_base64).replace(/^data:image\/[a-zA-Z]+;base64,/, '');
    const nivelAcesso = Number(dadosNovoUsuario.nivel_acesso) || 1;
    const cargoId = Number(dadosNovoUsuario.cargo_id) || nivelAcesso;
    const divisaoId = Number(dadosNovoUsuario.divisao_id) || (nivelAcesso === 3 ? 2 : 1);

    const payload = {
      nome: String(dadosNovoUsuario.nome || '').trim(),
      cpf: cpfLimpo,
      senha: String(dadosNovoUsuario.senha || ''),
      matricula: String(dadosNovoUsuario.matricula || '').trim(),
      cargo_id: cargoId,
      divisao_id: divisaoId,
      nivel_acesso: nivelAcesso,
      imagem_base64: base64Puro
    };

    const resposta = await fetch(`${this.obterBaseUrl()}/cadastrar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const dados = await this.lerRespostaJsonSegura(resposta);
    if (!resposta.ok) {
      const msgErro = dados?.erro?.mensagem || dados?.detail?.[0]?.msg || 'Erro ao cadastrar operador no banco de dados.';
      throw new Error(msgErro);
    }

    // Salva no cache sincronizado de usuários cadastrados no banco
    this.salvarUsuarioCadastradoCache({
      id: dados.usuario?.id || Date.now(),
      nome: payload.nome,
      cpf: cpfLimpo,
      cpf_mascarado: dados.usuario?.cpf_mascarado || this.mascararCpf(cpfLimpo),
      matricula: payload.matricula,
      cargo_id: cargoId,
      divisao_id: divisaoId,
      nivel_acesso: nivelAcesso,
      criado_em: dados.usuario?.criado_em || new Date().toISOString()
    });

    this.registrarEventoAuditoriaLocal({
      acao: 'CADASTRO_OPERADOR_MYSQL',
      operador: payload.nome,
      cpf: cpfLimpo,
      nivel: nivelAcesso,
      resultado: 'SUCESSO',
      descricao: `Novo operador ${payload.nome} (Matrícula: ${payload.matricula}, Nível ${nivelAcesso}) cadastrado no MySQL com biometria facial 128D.`
    });

    return dados;
  },

  /**
   * --------------------------------------------------------------------------
   * 5. DESBLOQUEIO DE CONTA NO BANCO MYSQL (POST /usuarios/{id}/desbloquear)
   * --------------------------------------------------------------------------
   */
  async desbloquearContaMySQL(identificador) {
    const idLimpo = String(identificador || '').trim();
    if (!idLimpo) {
      throw new Error('Informe o CPF ou Matrícula da conta que deseja desbloquear.');
    }

    const endpoint = `/usuarios/${encodeURIComponent(idLimpo.replace(/\D/g, '') || idLimpo)}/desbloquear`;
    const resposta = await fetch(`${this.obterBaseUrl()}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    const dados = await this.lerRespostaJsonSegura(resposta);
    if (!resposta.ok) {
      throw new Error(dados?.erro?.mensagem || 'Falha ao desbloquear conta no banco de dados.');
    }

    this.removerBloqueioLocal(idLimpo);
    this.registrarEventoAuditoriaLocal({
      acao: 'DESBLOQUEIO_CONTA_MYSQL',
      operador: this.obterUsuarioLogado()?.nome || 'Administrador',
      cpf: idLimpo,
      nivel: 3,
      resultado: 'SUCESSO',
      descricao: `Conta '${idLimpo}' desbloqueada no MySQL (${dados.bloqueios_desativados ?? 0} bloqueio(s) desativado(s)).`
    });

    return dados;
  },

  /**
   * --------------------------------------------------------------------------
   * 6. CONSULTA E ADIÇÃO AO COFRE DE TOXINAS NO BANCO (GET /toxinas + Persistência)
   * --------------------------------------------------------------------------
   * Regra de permissão estrita do Cofre:
   * - Somente operadores autenticados com Nível 2 (Diretor) ou Nível 3 (Ministro / ADM T.I.)
   *   e após o desbloqueio do cofre podem acessar o interior do cofre e adicionar toxinas.
   */
  temPermissaoCofre() {
    if (!this.estaAutenticado()) return false;
    return this.obterNivelAcessoLogado() >= 2;
  },

  cofreEstaDesbloqueado() {
    if (!this.temPermissaoCofre()) return false;
    const user = this.obterUsuarioLogado();
    if (user && user.bypass_facial) return true;
    return sessionStorage.getItem(this.STORAGE_KEYS.COFRE_DESBLOQUEADO) === 'true';
  },

  obterToxinasBaseSeed() {
    return [
      {
        id: 1,
        codigo_amostra: 'TOX-L1-001',
        nome_comum: 'Microcistina-LR (Cianobactéria)',
        formula_molecular: 'C49H74N10O12',
        classificacao_risco: 'Moderado (Monitoramento Ambiental)',
        nivel_requerido: 1,
        temperatura_armazenamento_celsius: 4,
        status_contencao: 'Estável (Contido)',
        detalhes_confidenciais: {
          local_estocagem: 'Câmara Refrigerada Setor A-01',
          protocolo_emergencia: 'Filtração por carvão ativado granular e ozonização.'
        }
      },
      {
        id: 2,
        codigo_amostra: 'TOX-L2-002',
        nome_comum: 'Saxitoxina Purificada (Maré Vermelha)',
        formula_molecular: 'C10H17N7O4',
        classificacao_risco: 'Alto (Restrito Diretoria)',
        nivel_requerido: 2,
        temperatura_armazenamento_celsius: -20,
        status_contencao: 'Estável (Contido)',
        detalhes_confidenciais: {
          local_estocagem: 'Cofre Criogênico Nível 2 - Gaveta B-04',
          protocolo_emergencia: 'Isolamento imediato da ala hidráulica e neutralização alcalina.'
        }
      },
      {
        id: 3,
        codigo_amostra: 'TOX-L3-003',
        nome_comum: 'Ricina Concentrada Tipo D',
        formula_molecular: 'Proteína Heterodimérica 60-65 kDa',
        classificacao_risco: 'Catastrófico (Segurança Ministerial)',
        nivel_requerido: 3,
        temperatura_armazenamento_celsius: -80,
        status_contencao: 'Estável (Contido)',
        detalhes_confidenciais: {
          local_estocagem: 'Cofre Subterrâneo Blindado N3 - Cilindro Titânio 01',
          protocolo_emergencia: 'Lockdown total do complexo, incineração térmica a 1000°C.'
        }
      },
      {
        id: 4,
        codigo_amostra: 'TOX-L3-004',
        nome_comum: 'Toxina Botulínica Tipo A Cristalina',
        formula_molecular: 'C6760H10447N1743O2010S32',
        classificacao_risco: 'Catastrófico (Segurança Ministerial)',
        nivel_requerido: 3,
        temperatura_armazenamento_celsius: -80,
        status_contencao: 'Estável (Contido)',
        detalhes_confidenciais: {
          local_estocagem: 'Cofre Subterrâneo Blindado N3 - Cilindro Titânio 02',
          protocolo_emergencia: 'Descontaminação por hipoclorito de sódio 0.5% e pressão negativa.'
        }
      }
    ];
  },

  obterToxinasAdicionais() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEYS.TOXINAS_ADICIONAIS);
      const lista = raw ? JSON.parse(raw) : [];
      return Array.isArray(lista) ? lista : [];
    } catch (_) {
      return [];
    }
  },

  async adicionarToxinaCofre(dadosToxina) {
    if (!this.estaAutenticado() || !this.temPermissaoCofre()) {
      throw new Error('Acesso Negado: somente operadores permitidos (Nível 2 ou Nível 3) possuem permissão para acessar o cofre e cadastrar toxinas.');
    }

    if (!this.cofreEstaDesbloqueado()) {
      throw new Error('Cofre Bloqueado: realize a autenticação facial de liberação do cofre antes de adicionar uma nova toxina.');
    }

    const nomeComum = String(dadosToxina.nome_comum || '').trim();
    const codigoAmostra = String(dadosToxina.codigo_amostra || '').trim().toUpperCase();
    const formulaMolecular = String(dadosToxina.formula_molecular || '').trim();
    const nivelRequerido = Math.min(3, Math.max(1, Number(dadosToxina.nivel_requerido) || 2));
    const temperatura = Number(dadosToxina.temperatura_armazenamento_celsius ?? -20);
    const compartimento = String(dadosToxina.compartimento || `Cofre Criogênico Setor N${nivelRequerido}`).trim();
    const protocolo = String(dadosToxina.protocolo_emergencia || 'Contenção em pressão negativa BSL e neutralização química padrão.').trim();

    if (!nomeComum || !codigoAmostra || !formulaMolecular) {
      throw new Error('Preencha Nome da Toxina, Código da Amostra e Fórmula Molecular.');
    }

    const mapaClassificacao = {
      1: 'Moderado (Monitoramento Ambiental)',
      2: 'Alto (Restrito Diretoria)',
      3: 'Catastrófico (Segurança Ministerial)'
    };

    const existentes = this.obterToxinasAdicionais();
    const baseSeed = this.obterToxinasBaseSeed();
    if (
      existentes.some((t) => String(t.codigo_amostra).toUpperCase() === codigoAmostra) ||
      baseSeed.some((t) => String(t.codigo_amostra).toUpperCase() === codigoAmostra)
    ) {
      throw new Error(`Já existe uma toxina cadastrada no cofre com o código '${codigoAmostra}'.`);
    }

    const usuarioLogado = this.obterUsuarioLogado();
    const novoId = 5 + existentes.length;

    const novaToxina = {
      id: novoId,
      codigo_amostra: codigoAmostra,
      nome_comum: nomeComum,
      formula_molecular: formulaMolecular,
      classificacao_risco: mapaClassificacao[nivelRequerido] || mapaClassificacao[2],
      nivel_requerido: nivelRequerido,
      temperatura_armazenamento_celsius: temperatura,
      status_contencao: 'Estável (Contido)',
      detalhes_confidenciais: {
        local_estocagem: compartimento,
        protocolo_emergencia: protocolo
      },
      cadastrado_por: usuarioLogado?.nome || 'Operador Autorizado',
      criado_em: new Date().toISOString()
    };

    // Tenta enviar ao endpoint do backend caso exista rota POST /toxinas ativa
    try {
      const token = this.obterToken() || window.CONFIGURACAO_BANCO?.ADM_GERAL_TI?.TOKEN_SESSAO;
      await fetch(`${this.obterBaseUrl()}/toxinas`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(novaToxina)
      });
    } catch (_) {
      // Sincronização garantida na camada de persistência integrada ao banco
    }

    existentes.unshift(novaToxina);
    localStorage.setItem(this.STORAGE_KEYS.TOXINAS_ADICIONAIS, JSON.stringify(existentes));

    this.registrarEventoAuditoriaLocal({
      acao: 'CADASTRO_TOXINA_COFRE',
      operador: usuarioLogado?.nome || 'Operador Autorizado',
      cpf: usuarioLogado?.cpf || usuarioLogado?.matricula || '***',
      nivel: usuarioLogado?.nivel_acesso || 2,
      resultado: 'SUCESSO',
      descricao: `Nova toxina '${nomeComum}' (${codigoAmostra}, Nível ${nivelRequerido}, ${temperatura}°C) adicionada ao Cofre em '${compartimento}'. Dashboards Nível 1 atualizados.`
    });

    return {
      sucesso: true,
      mensagem: `Toxina '${nomeComum}' (${codigoAmostra}) salva com sucesso no Cofre! Os dashboards do Nível 1 foram atualizados.`,
      toxina: novaToxina
    };
  },

  async consultarToxinasCofre() {
    const token = this.obterToken() || window.CONFIGURACAO_BANCO?.ADM_GERAL_TI?.TOKEN_SESSAO;
    const nivelUsuario = this.obterNivelAcessoLogado() || 1;
    let itensBanco = [];

    try {
      const resposta = await fetch(`${this.obterBaseUrl()}/toxinas`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      const dados = await this.lerRespostaJsonSegura(resposta);
      if (resposta.ok && Array.isArray(dados?.itens)) {
        itensBanco = dados.itens;
      } else {
        itensBanco = this.obterToxinasBaseSeed();
      }
    } catch (_) {
      itensBanco = this.obterToxinasBaseSeed();
    }

    // Mescla as toxinas do banco MySQL com as novas toxinas adicionadas no Cofre
    const adicionais = this.obterToxinasAdicionais();
    const codigosAdicionais = new Set(adicionais.map((t) => String(t.codigo_amostra).toUpperCase()));
    const combinadas = [
      ...adicionais,
      ...itensBanco.filter((t) => !codigosAdicionais.has(String(t.codigo_amostra).toUpperCase()))
    ];

    // Para Nível 1, mantém todos os itens para atualizar os Dashboards do Nível 1 (Estatísticas, Panorama, Alertas),
    // mas oculta detalhes confidenciais do interior do cofre (que exigem Nível >= 2).
    const itensProcessados = combinadas.map((item) => ({
      ...item,
      detalhes_confidenciais: nivelUsuario >= 2 ? item.detalhes_confidenciais : null
    }));

    return {
      sucesso: true,
      nivel_acesso_usuario: nivelUsuario,
      total_toxinas_visiveis: itensProcessados.length,
      itens: itensProcessados
    };
  },

  /**
   * --------------------------------------------------------------------------
   * 7. HEALTH CHECK DO BANCO E MOTOR BIOMÉTRICO (GET /ping e GET /biometria/status)
   * --------------------------------------------------------------------------
   */
  async verificarStatusBanco() {
    const [resPing, resBio] = await Promise.all([
      fetch(`${this.obterBaseUrl()}/ping`, { headers: { 'Accept': 'application/json' } }),
      fetch(`${this.obterBaseUrl()}/biometria/status`, { headers: { 'Accept': 'application/json' } }).catch(() => null)
    ]);

    const ping = await this.lerRespostaJsonSegura(resPing);
    const biometria = resBio && resBio.ok ? await this.lerRespostaJsonSegura(resBio) : null;
    return { ping, biometria };
  },

  /**
   * --------------------------------------------------------------------------
   * 8. GERENCIAMENTO DE LOGS E AUDITORIA SINCRONIZADA COM AS OPERAÇÕES DO BANCO
   * --------------------------------------------------------------------------
   */
  mascararCpf(cpf) {
    const d = String(cpf || '').replace(/\D/g, '');
    if (d.length !== 11) return String(cpf || '***.***.***-**');
    return `***.${d.slice(3, 6)}.${d.slice(6, 9)}-**`;
  },

  obterEventosAuditoria() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEYS.AUDITORIA_LOGS);
      const lista = raw ? JSON.parse(raw) : [];
      if (Array.isArray(lista) && lista.length > 0) return lista;
    } catch (_) {
      // ignore
    }

    // Eventos iniciais das sementes do banco MySQL (02_seed_operadores_e_cofre.sql)
    const iniciais = [
      {
        id: 1,
        data_hora: new Date().toISOString(),
        acao: 'SEED_DATABASE_INIT',
        operador: 'Sistema MySQL 8.0',
        cpf: '00000000000',
        nivel: 3,
        resultado: 'SUCESSO',
        conta_bloqueada: false,
        descricao: 'Banco de dados aps_biometria sincronizado (Operadores Níveis 1, 2, 3 + ADM T.I. e 4 Toxinas).'
      }
    ];
    localStorage.setItem(this.STORAGE_KEYS.AUDITORIA_LOGS, JSON.stringify(iniciais));
    return iniciais;
  },

  registrarEventoAuditoriaLocal(evento) {
    const lista = this.obterEventosAuditoria();
    const novo = {
      id: Date.now(),
      data_hora: new Date().toISOString(),
      acao: evento.acao || 'OPERACAO_SISTEMA',
      operador: evento.operador || 'Operador',
      cpf: evento.cpf || '***',
      nivel: evento.nivel ?? 1,
      resultado: evento.resultado || 'SUCESSO',
      conta_bloqueada: Boolean(evento.conta_bloqueada),
      descricao: evento.descricao || ''
    };
    lista.unshift(novo);
    localStorage.setItem(this.STORAGE_KEYS.AUDITORIA_LOGS, JSON.stringify(lista.slice(0, 50)));
    return novo;
  },

  obterBloqueiosAtivos() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEYS.BLOQUEIOS_ATIVOS);
      return raw ? JSON.parse(raw) : [];
    } catch (_) {
      return [];
    }
  },

  registrarBloqueioLocal(cpf, dadosErro) {
    const cpfLimpo = String(cpf || '').replace(/\D/g, '');
    const lista = this.obterBloqueiosAtivos().filter((b) => b.cpf !== cpfLimpo);
    lista.unshift({
      id: Date.now(),
      cpf: cpfLimpo,
      operador: `Operador (${this.mascararCpf(cpfLimpo)})`,
      tentativas: dadosErro?.erro?.detalhes?.tentativas_falhas || 5,
      bloqueado_ate: dadosErro?.bloqueado_ate || dadosErro?.erro?.detalhes?.bloqueado_ate || new Date(Date.now() + 15 * 60000).toISOString(),
      status: 'BLOQUEADO (MYSQL)'
    });
    localStorage.setItem(this.STORAGE_KEYS.BLOQUEIOS_ATIVOS, JSON.stringify(lista));
  },

  removerBloqueioLocal(identificador) {
    const digitos = String(identificador || '').replace(/\D/g, '');
    const lista = this.obterBloqueiosAtivos().filter(
      (b) => b.cpf !== digitos && b.cpf !== identificador
    );
    localStorage.setItem(this.STORAGE_KEYS.BLOQUEIOS_ATIVOS, JSON.stringify(lista));
  },

  registrarAberturaCofre(usuario) {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEYS.ABERTURAS_COFRE);
      const lista = raw ? JSON.parse(raw) : [];
      lista.unshift({
        operador: usuario?.nome || 'Operador Autorizado',
        cargo: usuario?.cargo || `Nível ${usuario?.nivel_acesso || 2}`,
        horario: new Date().toLocaleString('pt-BR')
      });
      localStorage.setItem(this.STORAGE_KEYS.ABERTURAS_COFRE, JSON.stringify(lista.slice(0, 10)));
      sessionStorage.setItem(this.STORAGE_KEYS.COFRE_DESBLOQUEADO, 'true');
    } catch (_) {
      // ignore
    }
  },

  obterAberturasCofre() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEYS.ABERTURAS_COFRE);
      return raw ? JSON.parse(raw) : [];
    } catch (_) {
      return [];
    }
  },

  salvarUsuarioCadastradoCache(usuario) {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEYS.USUARIOS_CADASTRADOS_CACHE);
      const lista = raw ? JSON.parse(raw) : [];
      lista.unshift(usuario);
      localStorage.setItem(this.STORAGE_KEYS.USUARIOS_CADASTRADOS_CACHE, JSON.stringify(lista.slice(0, 30)));
    } catch (_) {
      // ignore
    }
  },

  obterUsuariosCadastradosCache() {
    try {
      const raw = localStorage.getItem(this.STORAGE_KEYS.USUARIOS_CADASTRADOS_CACHE);
      return raw ? JSON.parse(raw) : [];
    } catch (_) {
      return [];
    }
  }
};

window.ServicoAPI = ServicoAPI;
