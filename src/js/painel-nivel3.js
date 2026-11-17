/**
 * ============================================================================
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Arquivo: src/js/painel-nivel3.js
 * Descrição: Controlador SPA das Telas e Abas por Role (Nível 1, Nível 2 e Nível 3),
 *            Proteção de Rotas (Auth Guard), Conexão de todos os botões e tabelas
 *            às operações do Banco de Dados MySQL 8.0 via FastAPI Python:
 *            - Consulta e filtragem RBAC de Toxinas (GET /toxinas)
 *            - Cadastro de Operador + Facial (POST /cadastrar)
 *            - Desbloqueio de Conta (POST /usuarios/{id}/desbloquear)
 *            - Liberação do Cofre por Biometria Facial (POST /autenticar)
 *            - Geração de Relatório PDF com dados do MySQL
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  const spaViewLogin = document.getElementById('spa-view-login');
  const spaViewDashboard = document.getElementById('spa-view-dashboard');
  const isSpaMode = Boolean(spaViewLogin && spaViewDashboard);

  // Estado "Dia Zero" da tela de login (index.html):
  //  - toda abertura/recarga da tela de login descarta qualquer sessão residual
  //    (o sistema nunca pula o login com token antigo do sessionStorage);
  //  - se o banco foi recriado (docker compose down -v), descarta também os
  //    caches locais persistentes (localStorage) de testes anteriores.
  if (isSpaMode && window.ServicoAPI) {
    window.ServicoAPI.limparSessaoResidual();
    window.ServicoAPI.sincronizarInstanciaBanco();
  }

  // Nível exigido da página standalone (se aplicável)
  const nivelPaginaAtributo = Number(document.body.getAttribute('data-role-nivel')) || 1;
  let nivelAtual = 1;

  // Cache em memória das toxinas carregadas do banco MySQL (GET /toxinas)
  let toxinasCache = [];
  let frameCadastroBase64 = '';

  // Define a aba inicial padrão de cada Role
  const abaPadraoPorNivel = {
    1: 'estatisticas',
    2: 'cofre-status',
    3: 'historico'
  };

  // --------------------------------------------------------------------------
  // 1. PROTEÇÃO DE ROTAS E BLOQUEIO DE ACESSO DIRETO PELA URL SEM LOGIN
  // --------------------------------------------------------------------------
  function validarAcessoRota() {
    if (!window.ServicoAPI || !window.ServicoAPI.estaAutenticado()) {
      if (!isSpaMode) {
        // Tentou acessar nivel1.html, nivel2.html ou nivel3.html direto pela URL sem estar logado
        window.location.replace('index.html');
        return false;
      }
      // Modo SPA (index.html): se tentou usar ?role=X ou #aba na URL sem estar logado, limpa a URL e mantém no login
      if (window.location.search || window.location.hash) {
        history.replaceState(null, '', window.location.pathname);
      }
      if (spaViewDashboard) spaViewDashboard.style.display = 'none';
      if (spaViewLogin) spaViewLogin.style.display = 'flex';
      document.body.classList.remove('dashboard-body');
      return false;
    }

    // Se está autenticado, obtém o nível RBAC real validado no login
    nivelAtual = window.ServicoAPI.obterNivelAcessoLogado() || 1;
    document.body.setAttribute('data-role-nivel', String(nivelAtual));

    // Em páginas standalone, impede que um usuário Nível 1 acesse nivel2.html ou nivel3.html pela URL
    if (!isSpaMode && nivelAtual < nivelPaginaAtributo) {
      const paginaPermitida = window.CONFIGURACAO_BANCO?.ROLES_PERMISSOES?.[nivelAtual]?.paginaInicial || 'nivel1.html';
      window.location.replace(paginaPermitida);
      return false;
    }

    return true;
  }

  // --------------------------------------------------------------------------
  // 2. INICIALIZAÇÃO DOS SCANNERS FACIAIS (NÍVEL 2 COFRE E NÍVEL 3 CADASTRO)
  // --------------------------------------------------------------------------
  let scannerNivel2 = null;
  let scannerCadastro = null;

  if (window.FaceScanner) {
    const n2CanvasId = document.getElementById('n2-face-mesh-canvas') ? 'n2-face-mesh-canvas' : null;
    const n2VideoId = document.getElementById('n2-webcam-video') ? 'n2-webcam-video' : null;

    if (n2CanvasId && n2VideoId) {
      scannerNivel2 = new window.FaceScanner(n2CanvasId, n2VideoId, {
        laserId: 'n2-scan-laser',
        progressBarId: 'n2-scan-progress-bar',
        progressBoxId: 'n2-scan-progress-box',
        statusId: 'n2-hud-status-text',
        metricsId: 'n2-hud-metrics-text'
      });
    } else if (!isSpaMode && document.getElementById('tab-autenticacao-facial')) {
      scannerNivel2 = new window.FaceScanner('face-mesh-canvas', 'webcam-video', {
        laserId: 'scan-laser',
        progressBarId: 'scan-progress-bar',
        progressBoxId: 'scan-progress-box',
        statusId: 'hud-status-text',
        metricsId: 'hud-metrics-text'
      });
    }

    if (document.getElementById('cad-face-mesh-canvas') && document.getElementById('cad-webcam-video')) {
      scannerCadastro = new window.FaceScanner('cad-face-mesh-canvas', 'cad-webcam-video', {
        laserId: 'cad-scan-laser',
        statusId: 'cad-hud-status-text',
        metricsId: 'cad-hud-metrics-text'
      });
    }
  }

  // --------------------------------------------------------------------------
  // 3. NAVEGAÇÃO ENTRE ABAS COM CONTROLE DE PERMISSÃO RBAC E LOGIN
  // --------------------------------------------------------------------------
  function ativarAbaNaTela(nomeAba) {
    if (!validarAcessoRota()) return;

    const nivelExigidoAba = window.MenuNiveis?.ABAS_POR_NIVEL?.[nomeAba] || 1;
    if (nivelExigidoAba > nivelAtual) {
      nomeAba = abaPadraoPorNivel[nivelAtual] || 'estatisticas';
    }

    const paineis = document.querySelectorAll('.tab-screen');
    let encontrou = false;

    paineis.forEach((painel) => {
      if (painel.getAttribute('data-tab-panel') === nomeAba) {
        painel.classList.add('active');
        encontrou = true;
      } else {
        painel.classList.remove('active');
      }
    });

    if (!encontrou && paineis.length > 0) {
      const abaFallback = abaPadraoPorNivel[nivelAtual] || 'estatisticas';
      paineis.forEach((painel) => {
        if (painel.getAttribute('data-tab-panel') === abaFallback) {
          painel.classList.add('active');
          nomeAba = abaFallback;
        }
      });
    }

    // Re-renderiza o menu lateral cumulativo conforme o Role autenticado
    if (window.MenuNiveis) {
      window.MenuNiveis.renderizar({
        containerId: 'sidebar-menu-container',
        roleNivel: nivelAtual,
        itemAtivo: nomeAba
      });
    }

    // Recalibra os Scanners caso a aba correspondente seja aberta
    if (nomeAba === 'autenticacao-facial' && scannerNivel2) {
      setTimeout(() => scannerNivel2.bindResize(), 60);
      // Preenche automaticamente o CPF se o operador já estiver logado
      const userLogado = window.ServicoAPI.obterUsuarioLogado();
      const inputOp = document.getElementById('n2-input-operador-id');
      if (userLogado && userLogado.cpf && inputOp && !inputOp.value) {
        inputOp.value = formatarCpfMascara(userLogado.cpf);
      }
    }

    if (nomeAba === 'adicionar' && scannerCadastro) {
      setTimeout(() => scannerCadastro.bindResize(), 60);
    }

    // Atualiza o estado visual de bloqueio/desbloqueio do Cofre e Inventário (somente Nível >= 2 com facial validada)
    alternarEstadoCofre(window.ServicoAPI ? window.ServicoAPI.cofreEstaDesbloqueado() : false);

    // Carrega e atualiza os dados do banco MySQL na aba ativa
    sincronizarDadosBancoMySQL();
  }

  // Abre o painel do Role autenticado (somente se a sessão de login foi validada)
  window.abrirDashboardRole = function (roleNivel, abaOpcional) {
    if (!window.ServicoAPI || !window.ServicoAPI.estaAutenticado()) {
      window.voltarParaLogin();
      return;
    }

    const nivelLogado = window.ServicoAPI.obterNivelAcessoLogado() || 1;
    // Garante que o usuário nunca eleve seu próprio nível acima do que foi autenticado no banco
    nivelAtual = Math.min([1, 2, 3].includes(Number(roleNivel)) ? Number(roleNivel) : nivelLogado, nivelLogado);
    sessionStorage.setItem('faca_role_nivel', String(nivelAtual));
    document.body.setAttribute('data-role-nivel', String(nivelAtual));

    if (isSpaMode) {
      spaViewLogin.style.display = 'none';
      spaViewDashboard.style.display = 'block';
      document.body.classList.add('dashboard-body');
    }

    // Verifica se o cofre já foi desbloqueado na sessão por usuário permitido (Nível 2 ou 3)
    const cofreLiberado = window.ServicoAPI.cofreEstaDesbloqueado();
    alternarEstadoCofre(cofreLiberado);

    const abaAlvo = abaOpcional || abaPadraoPorNivel[nivelAtual] || 'estatisticas';
    ativarAbaNaTela(abaAlvo);
  };

  // Encerra a sessão (Logout) e retorna para a tela de Login Principal
  window.voltarParaLogin = function () {
    if (scannerNivel2 && scannerNivel2.isCameraActive) {
      scannerNivel2.stopWebcam();
      const btnCam = document.getElementById('btn-n2-toggle-cam');
      if (btnCam) btnCam.textContent = 'Ativar Câmera Real';
    }
    if (scannerCadastro && scannerCadastro.isCameraActive) {
      scannerCadastro.stopWebcam();
      const btnCadCam = document.getElementById('btn-cad-toggle-cam');
      if (btnCadCam) btnCadCam.innerHTML = '<span>ATIVAR CÂMERA</span>';
    }

    if (window.ServicoAPI) {
      window.ServicoAPI.encerrarSessao();
    }

    if (typeof window.resetarFormularioLogin === 'function') {
      window.resetarFormularioLogin();
    }

    if (isSpaMode) {
      spaViewDashboard.style.display = 'none';
      spaViewLogin.style.display = 'flex';
      document.body.classList.remove('dashboard-body');
      history.replaceState(null, '', window.location.pathname);
    } else {
      window.location.replace('index.html');
    }
  };

  // Delegação global de cliques para navegação no menu lateral, botões de atalho e desbloqueio na tabela
  document.addEventListener('click', async (e) => {
    const btnVoltar = e.target.closest('[data-spa-action="voltar-login"]');
    if (btnVoltar) {
      e.preventDefault();
      window.voltarParaLogin();
      return;
    }

    const btnTab = e.target.closest('[data-spa-tab]');
    if (btnTab) {
      e.preventDefault();
      if (!validarAcessoRota()) return;
      const aba = btnTab.getAttribute('data-spa-tab');
      if (aba) {
        ativarAbaNaTela(aba);
      }
      return;
    }

    // Botão "+ ADICIONAR TOXINA" dentro do Cofre ou Inventário (somente usuários permitidos Nível 2/3 com cofre desbloqueado)
    const btnAbrirFormToxina = e.target.closest('[data-action="abrir-form-toxina"]');
    if (btnAbrirFormToxina) {
      e.preventDefault();
      if (!validarAcessoRota()) return;
      abrirFormularioNovaToxina(btnAbrirFormToxina.id);
      return;
    }

    // Botão de ação "DESBLOQUEAR (UNBLOCK)" dentro da tabela de Contas Bloqueadas ou Eventos
    const btnUnblockRow = e.target.closest('[data-unblock-cpf]');
    if (btnUnblockRow) {
      e.preventDefault();
      const cpfAlvo = btnUnblockRow.getAttribute('data-unblock-cpf');
      if (cpfAlvo) {
        await executarDesbloqueioConta(cpfAlvo);
      }
      return;
    }

    // Links "+ NOVO USUÁRIO" em nivel3.html que usam href="#adicionar"
    const linkNovoUsuario = e.target.closest('a.btn-novo-usuario[href="#adicionar"]');
    if (linkNovoUsuario) {
      e.preventDefault();
      if (!validarAcessoRota()) return;
      ativarAbaNaTela('adicionar');
      return;
    }
  });

  // Proteção também contra alterações manuais de hash na URL (hashchange)
  window.addEventListener('hashchange', () => {
    if (!validarAcessoRota()) return;
    const hash = window.location.hash.replace('#', '').trim();
    if (hash && document.querySelector(`.tab-screen[data-tab-panel="${hash}"]`)) {
      ativarAbaNaTela(hash);
    }
  });

  // --------------------------------------------------------------------------
  // 4. SINCRONIZAÇÃO E RENDERIZAÇÃO DOS DADOS DO BANCO MYSQL NAS TELAS
  // --------------------------------------------------------------------------
  async function sincronizarDadosBancoMySQL() {
    if (!window.ServicoAPI || !window.ServicoAPI.estaAutenticado()) return;

    try {
      // 1. Verifica conectividade com o banco via GET /ping e atualiza badge de status
      const statusPill = document.querySelector('.sql-status-pill');
      try {
        const { ping } = await window.ServicoAPI.verificarStatusBanco();
        if (statusPill && ping?.status === 'ok') {
          statusPill.textContent = ping.mensagem.toUpperCase();
          statusPill.style.color = '#2ed573';
          statusPill.style.borderColor = 'rgba(46, 213, 115, 0.45)';
          statusPill.style.background = 'rgba(46, 213, 115, 0.12)';
        }
      } catch (_) {
        // ignore
      }

      // 2. Consulta as toxinas do cofre no MySQL (GET /toxinas) filtradas pelo nível RBAC do usuário
      const respostaCofre = await window.ServicoAPI.consultarToxinasCofre();
      toxinasCache = Array.isArray(respostaCofre?.itens) ? respostaCofre.itens : [];

      renderizarEstatisticasNivel1(toxinasCache);
      renderizarPanoramaNivel1(toxinasCache);
      renderizarAlertasNivel1(toxinasCache);
      renderizarInventarioNivel2(toxinasCache);
      renderizarCofreStatusNivel2(toxinasCache);
      renderizarAuditoriaNivel3(toxinasCache);
      renderizarTabelaBloqueiosNivel3();
    } catch (erro) {
      console.warn('Aviso ao sincronizar dados com o MySQL:', erro);
      renderizarAuditoriaNivel3(toxinasCache);
      renderizarTabelaBloqueiosNivel3();
    }
  }

  // --- Nível 1: Aba 1 (Síntese de Estatísticas) ---
  function renderizarEstatisticasNivel1(itens) {
    const totalAmostras = itens.length;
    const adicionaisCount = window.ServicoAPI?.obterToxinasAdicionais()?.length || 0;
    const eventos = window.ServicoAPI.obterEventosAuditoria();
    const sucessos = eventos.filter((e) => e.resultado === 'SUCESSO').length;
    const taxaDeteccao = eventos.length > 0 ? Math.round((sucessos / eventos.length) * 100) : 98;

    setText('sql-kpi-taxa-deteccao', `${taxaDeteccao}%`);
    setText('sql-trend-taxa', 'Banco Ativo (PIVC 128D)');
    setText('sql-kpi-media-mensal', String(eventos.length));
    setText('sql-trend-mensal', 'Eventos Auditados');
    setText('sql-kpi-media-amostras', totalAmostras > 0 ? (totalAmostras * 1.25).toFixed(1) : '0');
    setText('sql-trend-amostras', `Nível RBAC ${nivelAtual}`);
    setText('sql-kpi-total-amostras', String(totalAmostras));
    setText(
      'sql-trend-total',
      adicionaisCount > 0 ? `Cofre Sincronizado (+${adicionaisCount} nova(s))` : 'Cofre Sincronizado'
    );

    const barsGroup = document.getElementById('sql-chart-deteccao-bars');
    if (barsGroup) {
      const xs = [55, 102, 149, 196, 243, 290, 337, 384, 431, 478];
      barsGroup.innerHTML = xs.map((x, idx) => {
        const hRed = 28 + ((idx * 17 + totalAmostras * 11) % 78);
        const hGrey = 20 + ((idx * 13 + eventos.length * 6) % 62);
        return `
          <rect x="${x - 9}" y="${132 - hRed}" width="8" height="${hRed}" rx="2" fill="#e01b2f"/>
          <rect x="${x + 1}" y="${132 - hGrey}" width="8" height="${hGrey}" rx="2" fill="#6c7587"/>
        `;
      }).join('');
    }

    const lineGroup = document.getElementById('sql-chart-media-amostras');
    if (lineGroup) {
      const pts = [
        [55, 92], [102, 78], [149, 84], [196, 62], [243, 54],
        [290, 66], [337, Math.max(25, 65 - totalAmostras * 5)],
        [384, Math.max(20, 58 - totalAmostras * 5)],
        [431, Math.max(16, 75 - totalAmostras * 9)]
      ];
      const poly = pts.map((p) => p.join(',')).join(' ');
      lineGroup.innerHTML = `
        <polyline fill="none" stroke="#ff2a40" stroke-width="2.5" points="${poly}"/>
        ${pts.map(([cx, cy]) => `<circle cx="${cx}" cy="${cy}" r="3.5" fill="#ffffff" stroke="#ff2a40" stroke-width="2"/>`).join('')}
      `;
    }
  }

  // --- Nível 1: Aba 2 (Panorama de Toxinas) ---
  function renderizarPanoramaNivel1(itens) {
    const heatGroup = document.getElementById('sql-heatmap-points');
    if (heatGroup) {
      const coords = [
        { x: 115, y: 78, r: 28 },
        { x: 245, y: 125, r: 34 },
        { x: 355, y: 88, r: 38 },
        { x: 195, y: 185, r: 30 },
        { x: 310, y: 175, r: 32 },
        { x: 145, y: 140, r: 26 },
        { x: 395, y: 150, r: 30 },
        { x: 80, y: 170, r: 26 }
      ];
      heatGroup.innerHTML = itens.map((item, i) => {
        const pt = coords[i % coords.length];
        const cor = item.nivel_requerido >= 3 ? '#ff2a40' : item.nivel_requerido === 2 ? '#f39c12' : '#2ed573';
        return `
          <circle cx="${pt.x}" cy="${pt.y}" r="${pt.r}" fill="${cor}" opacity="0.28"/>
          <circle cx="${pt.x}" cy="${pt.y}" r="6" fill="${cor}"/>
          <text x="${pt.x + 10}" y="${pt.y + 4}" fill="#ffffff" font-size="10" font-family="Host Grotesk, sans-serif">${item.codigo_amostra}</text>
        `;
      }).join('');
    }

    const pctEstavel = itens.length > 0 ? 100 : 0;
    const criticosCount = itens.filter((t) => Number(t.nivel_requerido) >= 2).length;
    const pctCritico = itens.length > 0 ? Math.min(100, Math.round((criticosCount / itens.length) * 100)) : 0;
    const pctTotal = Math.min(100, itens.length * 20);

    atualizarDonut('sql-donut-top-seg', 'sql-donut-top-val', pctEstavel);
    atualizarDonut('sql-donut-bl-seg', 'sql-donut-bl-val', pctCritico || 25);
    atualizarDonut('sql-donut-br-seg', 'sql-donut-br-val', pctTotal);

    // Atualiza barras e rótulos com as toxinas mais recentes do banco (incluindo as adicionadas no Cofre)
    atualizarBarraComRotulo('sql-bar-top-toxina-a', itens[0], 88);
    atualizarBarraComRotulo('sql-bar-top-toxina-b', itens[1], 70);
    atualizarBarraComRotulo('sql-bar-bl-toxina-a', itens[0], 92);
    atualizarBarraComRotulo('sql-bar-bl-toxina-b', itens[1], 75);
    atualizarBarraComRotulo('sql-bar-bl-toxina-c', itens[2], 62);
  }

  // --- Nível 1: Aba 3 (Histórico de Alertas) ---
  function renderizarAlertasNivel1(itens) {
    const tbody = document.getElementById('tbody-historico-alertas');
    if (!tbody) return;

    const eventos = window.ServicoAPI.obterEventosAuditoria();
    const linhasAlertas = [];

    eventos.slice(0, 6).forEach((ev) => {
      const dataFmt = new Date(ev.data_hora).toLocaleString('pt-BR');
      const isCritico = ev.resultado !== 'SUCESSO';
      linhasAlertas.push(`
        <tr>
          <td>${dataFmt}</td>
          <td><span class="alert-badge-circle ${isCritico ? 'critical' : 'warning'}">${isCritico ? '!' : 'i'}</span> Nível ${ev.nivel || 1}</td>
          <td>${ev.descricao}</td>
          <td style="color: ${isCritico ? '#ff334b' : '#2ed573'}; font-weight: 700;">${ev.resultado}</td>
        </tr>
      `);
    });

    itens.forEach((tox) => {
      linhasAlertas.push(`
        <tr>
          <td>${new Date().toLocaleDateString('pt-BR')}</td>
          <td><span class="alert-badge-circle ${tox.nivel_requerido >= 2 ? 'critical' : 'warning'}">${tox.nivel_requerido}</span></td>
          <td>Monitoramento ativo: ${tox.nome_comum} (${tox.codigo_amostra}) — ${tox.classificacao_risco}</td>
          <td style="color: #2ed573; font-weight: 700;">${tox.status_contencao || tox['status_contenção'] || 'Estável'}</td>
        </tr>
      `);
    });

    tbody.innerHTML = linhasAlertas.length > 0
      ? linhasAlertas.join('')
      : `<tr class="sql-empty-row"><td colspan="4">Nenhum alerta registrado no banco de dados.</td></tr>`;
  }

  // --- Nível 2: Aba 1 (Cofre Seguro - Status Geral) ---
  function renderizarCofreStatusNivel2(itens) {
    setText('sql-cofre-status-sistemas', 'OPERACIONAL (MYSQL ONLINE)');
    const menorTemp = itens.reduce((min, t) => Math.min(min, Number(t.temperatura_armazenamento_celsius ?? 4)), 4);
    setText('sql-cofre-temperatura', `${menorTemp.toFixed(1)} °C`);
    setText('sql-cofre-pressao', '-45 Pa (Pressão Negativa BSL)');
    setText('sql-cofre-gerador', '99.4% (Estável)');
    setText('sql-cofre-exaustao', 'FILTRAGEM HEPA DUPLA ATIVA');
    setText('sql-cofre-porta', 'BLINDAGEM TRANCADA / MONITORADA');
    setText('sql-cofre-ventilacao', 'FLUXO LAMINAR NOMINAL');
    const userLogado = window.ServicoAPI.obterUsuarioLogado();
    setText('sql-cofre-acesso', `${userLogado?.nome || 'Operador'} (Nível ${nivelAtual})`);

    const boxAberturas = document.getElementById('sql-lista-ultimas-aberturas');
    if (boxAberturas) {
      const aberturas = window.ServicoAPI.obterAberturasCofre();
      if (aberturas.length === 0) {
        boxAberturas.innerHTML = `<div>Acesso atual liberado para <strong>${userLogado?.nome || 'Operador'}</strong> (${new Date().toLocaleTimeString('pt-BR')})</div>`;
      } else {
        boxAberturas.innerHTML = aberturas.slice(0, 4).map((a) => (
          `<div style="margin-bottom:4px;">• <strong>${a.operador}</strong> (${a.cargo}) — ${a.horario}</div>`
        )).join('');
      }
    }
  }

  // --- Nível 2: Aba 2 (Inventário de Toxinas com Filtro Conectado) ---
  function renderizarInventarioNivel2(itens, filtroRisco = '') {
    const tbody = document.getElementById('tbody-inventario-toxinas');
    if (!tbody) return;

    const filtrados = itens.filter((item) => {
      if (!filtroRisco) return true;
      const riscoStr = `${item.classificacao_risco} ${item.nivel_requerido}`.toLowerCase();
      if (filtroRisco === 'alto') return item.nivel_requerido >= 2 || riscoStr.includes('crítico') || riscoStr.includes('alto');
      if (filtroRisco === 'critico') return item.nivel_requerido >= 3 || riscoStr.includes('catastrófico') || riscoStr.includes('crítico');
      return true;
    });

    const tempMedia = filtrados.length > 0
      ? (filtrados.reduce((acc, t) => acc + Number(t.temperatura_armazenamento_celsius || 4), 0) / filtrados.length).toFixed(1)
      : '4.0';

    setText('sql-inv-temperatura', `${tempMedia} °C`);
    setText('sql-inv-quantidade', `${filtrados.length} Itens`);

    if (filtrados.length === 0) {
      tbody.innerHTML = `<tr class="sql-empty-row"><td colspan="6">Nenhuma substância encontrada para o filtro selecionado.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtrados.map((t) => {
      const compartimento = t.detalhes_confidenciais?.local_estocagem || `Setor BSL-${t.nivel_requerido} (Cofre #0${t.id})`;
      const statusCont = t.status_contencao || t['status_contenção'] || 'Estável';
      return `
        <tr>
          <td>#${t.id} (${t.codigo_amostra})</td>
          <td><strong>${t.nome_comum}</strong><br><small style="color:#7d8698;">Fórmula: ${t.formula_molecular}</small></td>
          <td>${t.temperatura_armazenamento_celsius} °C (${statusCont})</td>
          <td><span style="color:${t.nivel_requerido >= 3 ? '#ff2a40' : t.nivel_requerido === 2 ? '#f39c12' : '#2ed573'}; font-weight:700;">${t.classificacao_risco}</span></td>
          <td>${compartimento}</td>
          <td>Nível RBAC ${t.nivel_requerido}</td>
        </tr>
      `;
    }).join('');
  }

  // --- Nível 3: Aba 1 (Auditoria Global, Sessões Ativas, Timeline e Eventos) ---
  function renderizarAuditoriaNivel3(itens) {
    const tbodySessoes = document.getElementById('tbody-sessoes-ativas');
    const usuarioAtual = window.ServicoAPI.obterUsuarioLogado();
    const cadastrados = window.ServicoAPI.obterUsuariosCadastradosCache();

    if (tbodySessoes && usuarioAtual) {
      const linhasSessoes = [
        `<tr>
          <td><strong>${usuarioAtual.nome}</strong> <span style="color:#2ed573;">(ONLINE)</span></td>
          <td>${usuarioAtual.cargo} — Nível ${usuarioAtual.nivel_acesso}</td>
          <td>${new Date().toLocaleDateString('pt-BR')}</td>
          <td>AGORA</td>
        </tr>`
      ];

      cadastrados.slice(0, 4).forEach((u) => {
        linhasSessoes.push(`
          <tr>
            <td>${u.nome}</td>
            <td>Matrícula: ${u.matricula} (Nível ${u.nivel_acesso})</td>
            <td>${new Date(u.criado_em).toLocaleDateString('pt-BR')}</td>
            <td>CADASTRADO</td>
          </tr>
        `);
      });

      tbodySessoes.innerHTML = linhasSessoes.join('');
    }

    const listaTimeline = document.getElementById('lista-timeline');
    const listaEventos = document.getElementById('lista-eventos');
    const eventos = window.ServicoAPI.obterEventosAuditoria();

    if (listaTimeline && listaEventos) {
      listaTimeline.className = '';
      listaEventos.className = '';

      listaTimeline.innerHTML = eventos.slice(0, 6).map((ev) => {
        const hora = new Date(ev.data_hora).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const cor = ev.resultado === 'SUCESSO' ? '#2ed573' : '#ff2a40';
        return `
          <div style="display:flex; align-items:center; gap:8px; padding:7px 4px; border-bottom:1px solid rgba(255,255,255,0.05); font-family:var(--font-mono); font-size:0.7rem;">
            <span style="width:8px; height:8px; border-radius:50%; background:${cor}; display:inline-block;"></span>
            <span>${hora} — ${ev.acao.slice(0, 14)}</span>
          </div>
        `;
      }).join('');

      listaEventos.innerHTML = eventos.slice(0, 5).map((ev) => {
        const btnDesbloqueio = ev.conta_bloqueada && ev.cpf
          ? `<button type="button" class="btn-novo-usuario" data-unblock-cpf="${ev.cpf}" style="margin-top:6px; padding:3px 8px; font-size:0.65rem;">UNBLOCK (${ev.cpf})</button>`
          : '';
        return `
          <div style="padding:8px 4px; border-bottom:1px solid rgba(255,255,255,0.06); font-size:0.75rem;">
            <div style="font-weight:700; color:${ev.resultado === 'SUCESSO' ? '#2ed573' : '#ff3b4e'};">
              [${ev.resultado}] ${ev.acao} — ${ev.operador}
            </div>
            <div style="color:#b0b8c8; margin-top:2px;">${ev.descricao}</div>
            ${btnDesbloqueio}
          </div>
        `;
      }).join('');
    }

    // Widgets inferiores Nível 3
    setBarWidth('sql-bar-dioxinas', itens[0] ? 78 : 40);
    setText('sql-pct-dioxinas', itens[0] ? '78%' : '40%');
    setBarWidth('sql-bar-pfas', itens[1] ? 64 : 30);
    setText('sql-pct-pfas', itens[1] ? '64%' : '30%');
    setBarWidth('sql-bar-fosfatos', itens[2] ? 92 : 50);
    setText('sql-pct-fosfatos', itens[2] ? '92%' : '50%');

    const arcCofre = document.getElementById('sql-arc-cofre');
    const valCofre = document.getElementById('valor-cofre-sql');
    const ocupacaoPct = Math.min(100, Math.max(25, itens.length * 25));
    if (arcCofre) {
      const offset = 210 - (210 * ocupacaoPct) / 100;
      arcCofre.setAttribute('stroke-dashoffset', String(offset));
    }
    if (valCofre) {
      valCofre.textContent = `${ocupacaoPct}%`;
    }

    const chartAlertasN3 = document.getElementById('sql-n3-chart-alertas');
    if (chartAlertasN3) {
      chartAlertasN3.innerHTML = `
        <polyline fill="none" stroke="#ff2a40" stroke-width="2" points="0,68 45,54 95,60 145,35 195,42 240,22 280,28"/>
      `;
    }
  }

  // --- Nível 3: Aba 3 (Tabela de Contas Bloqueadas) ---
  function renderizarTabelaBloqueiosNivel3() {
    const tbody = document.getElementById('tbody-contas-bloqueadas');
    if (!tbody) return;

    const bloqueios = window.ServicoAPI.obterBloqueiosAtivos();
    if (bloqueios.length === 0) {
      tbody.innerHTML = `
        <tr class="sql-empty-row">
          <td colspan="6">Nenhuma conta com bloqueio ativo registrado localmente. Utilize o campo acima para desbloquear qualquer CPF ou Matrícula diretamente no MySQL.</td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = bloqueios.map((b, idx) => `
      <tr>
        <td>#${idx + 1}</td>
        <td>${b.operador}</td>
        <td>${b.cpf}</td>
        <td>${b.tentativas} / 5</td>
        <td style="color:#ff334b; font-weight:700;">${b.status}</td>
        <td>
          <button type="button" class="btn-novo-usuario" data-unblock-cpf="${b.cpf}">
            <span>DESBLOQUEAR</span>
          </button>
        </td>
      </tr>
    `).join('');
  }

  // --------------------------------------------------------------------------
  // 5. CONEXÃO DOS BOTÕES E CONTROLES DE CADA TELA ÀS OPERAÇÕES
  // --------------------------------------------------------------------------

  // 5.1. Botões de Zoom no Mapa de Calor (Nível 1 - Panorama de Toxinas)
  let zoomMapa = 1;
  const botoesZoom = document.querySelectorAll('.btn-map-zoom');
  botoesZoom.forEach((btn) => {
    btn.addEventListener('click', () => {
      const svgMapa = document.querySelector('#sql-heatmap-container svg');
      if (!svgMapa) return;
      if (btn.textContent.trim() === '+') {
        zoomMapa = Math.min(1.8, zoomMapa + 0.15);
      } else {
        zoomMapa = Math.max(1.0, zoomMapa - 0.15);
      }
      svgMapa.style.transform = `scale(${zoomMapa})`;
      svgMapa.style.transition = 'transform 0.25s ease';
    });
  });

  // 5.2. Filtro de Busca do Inventário de Toxinas (Nível 2 - #sql-filtro-inventario)
  const selectFiltroInv = document.getElementById('sql-filtro-inventario');
  if (selectFiltroInv) {
    selectFiltroInv.addEventListener('change', (e) => {
      renderizarInventarioNivel2(toxinasCache, e.target.value);
    });
  }

  // 5.3. Gerador de Relatório PDF (Nível 1 - #form-gerador-pdf / #btn-gerar-pdf)
  const formGeradorPdf = document.getElementById('form-gerador-pdf');
  const pdfFeedback = document.getElementById('pdf-feedback');
  if (formGeradorPdf) {
    formGeradorPdf.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        showFeedback(pdfFeedback, 'Consultando registros no banco de dados MySQL...', 'info');
        const dadosCofre = await window.ServicoAPI.consultarToxinasCofre();
        const itens = dadosCofre.itens || [];
        const tipoRelatorio = document.getElementById('pdf-tipo-relatorio')?.value || 'panorama';
        const dataInicio = document.getElementById('pdf-data-inicio')?.value || new Date().toISOString().slice(0, 10);
        const dataFim = document.getElementById('pdf-data-fim')?.value || new Date().toISOString().slice(0, 10);

        setText('sql-pdf-data-ref', `${dataInicio} até ${dataFim}`);
        const tbodyPdf = document.getElementById('tbody-pdf-preview');

        if (tbodyPdf) {
          if (tipoRelatorio === 'alertas') {
            const eventos = window.ServicoAPI.obterEventosAuditoria().slice(0, 6);
            tbodyPdf.innerHTML = eventos.map((ev) => `
              <tr>
                <td>${ev.acao}</td>
                <td>${ev.operador}</td>
                <td>${ev.resultado}</td>
              </tr>
            `).join('');
          } else {
            tbodyPdf.innerHTML = itens.map((t) => `
              <tr>
                <td>${t.nome_comum}</td>
                <td>${t.codigo_amostra}</td>
                <td>${t.temperatura_armazenamento_celsius} °C (${t.classificacao_risco})</td>
              </tr>
            `).join('');
          }
        }

        window.ServicoAPI.registrarEventoAuditoriaLocal({
          acao: 'GERACAO_RELATORIO_PDF',
          operador: window.ServicoAPI.obterUsuarioLogado()?.nome || 'Operador',
          nivel: nivelAtual,
          resultado: 'SUCESSO',
          descricao: `Relatório PDF (${tipoRelatorio.toUpperCase()}) gerado com ${itens.length} registros do MySQL.`
        });

        showFeedback(pdfFeedback, `✅ Relatório gerado com sucesso (${itens.length} registros carregados do MySQL).`, 'success');
      } catch (err) {
        showFeedback(pdfFeedback, `❌ Erro ao consultar banco para o PDF: ${err.message || err}`, 'error');
      }
    });
  }

  // 5.4. Nível 2: Transição entre Cofre Bloqueado -> Autenticação Facial -> Cofre Desbloqueado e Adição de Toxina
  const viewCofreBloqueado = document.getElementById('view-cofre-bloqueado');
  const viewCofreDesbloqueado = document.getElementById('view-cofre-desbloqueado');
  const viewInvBloqueado = document.getElementById('view-inventario-bloqueado');
  const viewInvDesbloqueado = document.getElementById('view-inventario-desbloqueado');
  const btnCofreNovaToxina = document.getElementById('btn-cofre-abrir-form-toxina');
  const btnInvNovaToxina = document.getElementById('btn-inv-abrir-form-toxina');
  const cardFormNovaToxina = document.getElementById('card-form-nova-toxina');
  const formNovaToxinaCofre = document.getElementById('form-nova-toxina-cofre');
  const btnCancelarToxinaCofre = document.getElementById('btn-cancelar-toxina-cofre');
  const toxFeedbackMsg = document.getElementById('tox-feedback-msg');
  const btnIrFacial = document.getElementById('btn-ir-autenticacao-facial');

  function alternarEstadoCofre(desbloqueado) {
    const temPermissaoCofre = window.ServicoAPI ? window.ServicoAPI.temPermissaoCofre() : false;
    const liberadoEfetivo = Boolean(desbloqueado && temPermissaoCofre);

    if (viewCofreBloqueado && viewCofreDesbloqueado) {
      viewCofreBloqueado.style.display = liberadoEfetivo ? 'none' : 'block';
      viewCofreDesbloqueado.style.display = liberadoEfetivo ? 'block' : 'none';
    }

    if (viewInvBloqueado && viewInvDesbloqueado) {
      viewInvBloqueado.style.display = liberadoEfetivo ? 'none' : 'block';
      viewInvDesbloqueado.style.display = liberadoEfetivo ? 'block' : 'none';
    }

    if (btnCofreNovaToxina) {
      btnCofreNovaToxina.style.display = liberadoEfetivo ? 'inline-flex' : 'none';
    }
    if (btnInvNovaToxina) {
      btnInvNovaToxina.style.display = liberadoEfetivo ? 'inline-flex' : 'none';
    }

    if (!liberadoEfetivo && cardFormNovaToxina) {
      cardFormNovaToxina.style.display = 'none';
    }
  }

  function abrirFormularioNovaToxina(botaoOrigemId) {
    if (!window.ServicoAPI || !window.ServicoAPI.temPermissaoCofre()) {
      alert('Acesso Negado: somente operadores autorizados (Nível 2 ou Nível 3) possuem permissão para acessar o cofre.');
      return;
    }

    if (!window.ServicoAPI.cofreEstaDesbloqueado()) {
      ativarAbaNaTela('autenticacao-facial');
      showFeedback(
        n2BioFeedback,
        '⚠️ Desbloqueie o cofre com sua biometria facial (Nível 2 ou Nível 3) antes de adicionar uma nova toxina.',
        'info'
      );
      return;
    }

    if (!cardFormNovaToxina) return;

    // Posiciona o formulário dentro da aba do Cofre que estiver ativa (Cofre Status ou Inventário)
    const slotCofre = document.getElementById('slot-form-toxina-cofre');
    const slotInv = document.getElementById('slot-form-toxina-inventario');
    if (botaoOrigemId === 'btn-inv-abrir-form-toxina' && slotInv) {
      slotInv.appendChild(cardFormNovaToxina);
    } else if (slotCofre) {
      slotCofre.appendChild(cardFormNovaToxina);
    }

    clearFeedback(toxFeedbackMsg);
    cardFormNovaToxina.style.display = 'block';

    // Sugere automaticamente o próximo código de amostra disponível
    const inputCodigo = document.getElementById('tox-input-codigo');
    if (inputCodigo && !inputCodigo.value) {
      const proxNumero = String((toxinasCache?.length || 4) + 1).padStart(3, '0');
      inputCodigo.value = `TOX-L2-${proxNumero}`;
    }

    const inputNome = document.getElementById('tox-input-nome');
    if (inputNome) inputNome.focus();
  }

  if (btnCancelarToxinaCofre && cardFormNovaToxina) {
    btnCancelarToxinaCofre.addEventListener('click', () => {
      clearFeedback(toxFeedbackMsg);
      cardFormNovaToxina.style.display = 'none';
    });
  }

  if (formNovaToxinaCofre) {
    formNovaToxinaCofre.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearFeedback(toxFeedbackMsg);

      const btnSalvar = document.getElementById('btn-salvar-toxina-cofre');
      if (btnSalvar) btnSalvar.disabled = true;

      try {
        const nivelSelecionado = Number(document.getElementById('tox-select-nivel')?.value || 2);
        const res = await window.ServicoAPI.adicionarToxinaCofre({
          nome_comum: document.getElementById('tox-input-nome')?.value || '',
          codigo_amostra: document.getElementById('tox-input-codigo')?.value || '',
          formula_molecular: document.getElementById('tox-input-formula')?.value || '',
          nivel_requerido: nivelSelecionado,
          temperatura_armazenamento_celsius: Number(document.getElementById('tox-input-temp')?.value ?? -20),
          compartimento: document.getElementById('tox-input-compartimento')?.value || '',
          protocolo_emergencia: document.getElementById('tox-input-protocolo')?.value || ''
        });

        formNovaToxinaCofre.reset();
        showFeedback(toxFeedbackMsg, `✅ ${res.mensagem}`, 'success');

        // Atualiza imediatamente os Dashboards do Nível 1, Inventário Nível 2 e Auditoria Nível 3
        await sincronizarDadosBancoMySQL();
      } catch (erro) {
        showFeedback(toxFeedbackMsg, `❌ ${erro.message || 'Erro ao salvar toxina no cofre.'}`, 'error');
      } finally {
        if (btnSalvar) btnSalvar.disabled = false;
      }
    });
  }

  if (btnIrFacial) {
    btnIrFacial.addEventListener('click', () => {
      ativarAbaNaTela('autenticacao-facial');
    });
  }

  // 5.5. Nível 2 — Aba Autenticação Facial (Liberação do Cofre via POST /autenticar)
  const btnN2StartScan = document.getElementById('btn-n2-start-scan');
  const btnN2ScanLabel = document.getElementById('btn-n2-scan-label');
  const btnN2CancelScan = document.getElementById('btn-n2-cancel-scan');
  const btnN2ToggleCam = document.getElementById('btn-n2-toggle-cam');
  const n2InputOperador = document.getElementById('n2-input-operador-id');
  const n2InputSetor = document.getElementById('n2-input-setor');
  const n2BioFeedback = document.getElementById('n2-bio-feedback');

  if (n2InputOperador) {
    n2InputOperador.addEventListener('input', (e) => {
      e.target.value = formatarCpfMascara(e.target.value);
    });
  }

  if (btnN2ToggleCam && scannerNivel2) {
    btnN2ToggleCam.addEventListener('click', async () => {
      clearFeedback(n2BioFeedback);
      const active = await scannerNivel2.toggleWebcam();
      btnN2ToggleCam.textContent = active ? 'Usar Malha Holográfica' : 'Ativar Câmera Real';

      if (active) {
        showFeedback(
          n2BioFeedback,
          '⚠️ Câmera ativada. Aproxime seu rosto e mantenha-o dentro da REGIÃO OVAL para o sistema validar melhor e liberar o acesso.',
          'info'
        );
      } else {
        scannerNivel2.resetState();
        showFeedback(n2BioFeedback, 'Modo holográfico ativo. Ative a câmera real e aproxime o rosto na região oval para validação.', 'info');
      }
    });
  }

  if (btnN2CancelScan && scannerNivel2) {
    btnN2CancelScan.addEventListener('click', () => {
      clearFeedback(n2BioFeedback);
      scannerNivel2.resetState();
      if (scannerNivel2.isCameraActive) {
        scannerNivel2.stopWebcam();
        if (btnN2ToggleCam) btnN2ToggleCam.textContent = 'Ativar Câmera Real';
      }
      ativarAbaNaTela('cofre-status');
    });
  }

  if (btnN2StartScan && scannerNivel2) {
    btnN2StartScan.addEventListener('click', async () => {
      if (scannerNivel2.isScanning) return;

      const cpfOperador = n2InputOperador ? n2InputOperador.value.trim() : '';
      const senhaOperador = n2InputSetor ? n2InputSetor.value.trim() : '';

      // Se for o ADM Geral T.I., libera o cofre imediatamente sem exigir webcam
      if (window.ServicoAPI.ehAdmGeralTI(cpfOperador, senhaOperador)) {
        window.ServicoAPI.registrarAberturaCofre(window.CONFIGURACAO_BANCO.ADM_GERAL_TI.USUARIO);
        alternarEstadoCofre(true);
        showFeedback(n2BioFeedback, '✅ Cofre desbloqueado com credenciais de Administrador Geral (T.I.).', 'success');
        setTimeout(() => ativarAbaNaTela('cofre-status'), 900);
        return;
      }

      if (!scannerNivel2.isCameraActive) {
        showFeedback(
          n2BioFeedback,
          '⚠️ A câmera real não está ativa! Clique em "Ativar Câmera Real" abaixo, aproxime seu rosto na região oval e inicie o escaneamento.',
          'error'
        );
        return;
      }

      if (!cpfOperador || !senhaOperador) {
        showFeedback(
          n2BioFeedback,
          'Informe o ID do Operador (CPF) e a Senha de Liberação antes de iniciar o escaneamento.',
          'error'
        );
        return;
      }

      if (typeof scannerNivel2.validarPresencaNaRegiaoOval === 'function') {
        const checagemOval = scannerNivel2.validarPresencaNaRegiaoOval();
        if (!checagemOval.ok) {
          scannerNivel2.setErrorState('ENQUADRE NA OVAL', 'APROXIME O ROSTO');
          showFeedback(n2BioFeedback, `⚠️ ${checagemOval.motivo}`, 'info');
          return;
        }
      }

      btnN2StartScan.disabled = true;
      if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'VALIDANDO ROSTO NA OVAL...';
      clearFeedback(n2BioFeedback);
      scannerNivel2.setScanningState(true, 'ANALISANDO ROSTO NA REGIÃO OVAL...');

      const frameBase64 = scannerNivel2.captureFrameBase64();
      if (!frameBase64) {
        scannerNivel2.setErrorState('ERRO DE CAPTURA', 'FRAME NULO');
        showFeedback(n2BioFeedback, 'Não foi possível capturar o rosto na região oval. Verifique se a câmera está conectada.', 'error');
        btnN2StartScan.disabled = false;
        if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'TENTAR NOVAMENTE';
        return;
      }

      try {
        const dados = await window.ServicoAPI.validarBiometriaFacial(cpfOperador, senhaOperador, frameBase64);

        // Regra estrita: somente operadores de Nível 2 ou Nível 3 podem desbloquear e acessar o Cofre
        if (Number(dados.usuario?.nivel_acesso || 1) < 2) {
          scannerNivel2.setErrorState('PERMISSÃO INSUFICIENTE', 'EXIGE NÍVEL 2 OU 3');
          showFeedback(
            n2BioFeedback,
            `❌ Acesso Negado ao Cofre: ${dados.usuario?.nome || 'Operador'} possui Nível 1. Somente pessoas permitidas (Nível 2 ou Nível 3) podem ter acesso ao cofre.`,
            'error'
          );
          btnN2StartScan.disabled = false;
          if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'TENTAR NOVAMENTE';
          return;
        }

        const biometriaInfo = dados.biometria;
        const distTxt = biometriaInfo ? biometriaInfo.distancia_euclidiana.toFixed(4) : '0.0000';
        const confTxt = biometriaInfo ? biometriaInfo.confianca_percentual.toFixed(1) : '100.0';

        scannerNivel2.setSuccessState('COFRE DESBLOQUEADO', `DIST: ${distTxt} | CONF: ${confTxt}%`);
        if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'ACESSO CONCEDIDO';

        window.ServicoAPI.registrarAberturaCofre(dados.usuario);
        showFeedback(
          n2BioFeedback,
          `✅ ACESSO AO COFRE LIBERADO: Nível ${dados.usuario.nivel_acesso} — ${dados.usuario.nome}. Distância: ${distTxt} (${confTxt}%)`,
          'success'
        );

        setTimeout(() => {
          btnN2StartScan.disabled = false;
          if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'INICIAR ESCANEAMENTO';
          alternarEstadoCofre(true);
          ativarAbaNaTela('cofre-status');
        }, 1200);
      } catch (erro) {
        const status = erro?.status || 500;
        const mensagem = erro?.erro?.mensagem || 'Acesso Negado: usuário não cadastrado ou facial não reconhecida.';

        if (status === 400) {
          scannerNivel2.setErrorState(erro?.erro?.codigo || 'CAPTURE_ERROR', 'APROXIME NA REGIÃO OVAL');
          showFeedback(
            n2BioFeedback,
            `⚠️ ${mensagem} Aproxime seu rosto da câmera e fique dentro da região oval para o sistema validar melhor.`,
            'info'
          );
        } else if (status === 401) {
          const rest = erro.tentativas_restantes !== undefined ? erro.tentativas_restantes : '?';
          scannerNivel2.setErrorState('ACESSO NEGADO', `TENTATIVAS: ${rest}`);
          showFeedback(
            n2BioFeedback,
            `❌ ${mensagem} Aproxime o rosto na região oval para melhor leitura [Tentativas restantes: ${rest}]`,
            'error'
          );
        } else if (status === 403) {
          scannerNivel2.setErrorState('TERMINAL BLOQUEADO', 'CONTA BLOQUEADA');
          showFeedback(n2BioFeedback, `🚨 ${mensagem}`, 'error');
        } else {
          scannerNivel2.setErrorState('ERRO', 'FALHA NA VALIDAÇÃO');
          showFeedback(n2BioFeedback, `❌ ${mensagem}`, 'error');
        }
        btnN2StartScan.disabled = status === 403;
        if (btnN2ScanLabel) btnN2ScanLabel.textContent = status === 403 ? 'ACESSO BLOQUEADO' : 'TENTAR NOVAMENTE';
      }
    });
  }

  // --------------------------------------------------------------------------
  // 5.6. Nível 3 — Aba Adicionar Novo Operador + Facial (POST /cadastrar)
  // --------------------------------------------------------------------------
  const formNovoUsuario = document.getElementById('form-novo-usuario-sql');
  const feedbackModal = document.getElementById('modal-sql-feedback');
  const inputCpfCadastro = document.getElementById('sql-input-cpf');
  const inputFotoFile = document.getElementById('sql-input-foto-file');
  const btnCadToggleCam = document.getElementById('btn-cad-toggle-cam');
  const btnCadCapturarFace = document.getElementById('btn-cad-capturar-face');

  if (inputCpfCadastro) {
    inputCpfCadastro.addEventListener('input', (e) => {
      e.target.value = formatarCpfMascara(e.target.value);
    });
  }

  if (inputFotoFile) {
    inputFotoFile.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        frameCadastroBase64 = String(reader.result || '');
        if (scannerCadastro) {
          scannerCadastro.setSuccessState('FOTO CARREGADA', 'PRONTO P/ CADASTRAR');
        }
        showFeedback(feedbackModal, `📸 Foto facial "${file.name}" carregada e pronta para gravação dos vetores 128D no banco MySQL.`, 'info');
      };
      reader.readAsDataURL(file);
    });
  }

  if (btnCadToggleCam && scannerCadastro) {
    btnCadToggleCam.addEventListener('click', async () => {
      const ativa = await scannerCadastro.toggleWebcam();
      btnCadToggleCam.innerHTML = ativa ? '<span>DESATIVAR CÂMERA</span>' : '<span>ATIVAR CÂMERA</span>';
      if (ativa) {
        showFeedback(
          feedbackModal,
          '⚠️ Câmera ativa. Aproxime o rosto do operador e mantenha-o dentro da REGIÃO OVAL para o sistema validar melhor, depois clique em "CAPTURAR FACIAL".',
          'info'
        );
      } else {
        scannerCadastro.resetState();
      }
    });
  }

  if (btnCadCapturarFace && scannerCadastro) {
    btnCadCapturarFace.addEventListener('click', () => {
      if (!scannerCadastro.isCameraActive) {
        showFeedback(
          feedbackModal,
          '⚠️ Ative a câmera primeiro, aproxime o rosto na região oval e clique em "CAPTURAR FACIAL" (ou selecione um arquivo JPEG/PNG).',
          'error'
        );
        return;
      }

      if (typeof scannerCadastro.validarPresencaNaRegiaoOval === 'function') {
        const checagemOval = scannerCadastro.validarPresencaNaRegiaoOval();
        if (!checagemOval.ok) {
          scannerCadastro.setErrorState('ENQUADRE NA OVAL', 'APROXIME O ROSTO');
          showFeedback(feedbackModal, `⚠️ ${checagemOval.motivo}`, 'info');
          return;
        }
      }

      const frame = scannerCadastro.captureFrameBase64();
      if (!frame) {
        showFeedback(feedbackModal, '❌ Falha ao capturar o rosto na região oval da webcam.', 'error');
        return;
      }
      frameCadastroBase64 = frame;
      scannerCadastro.setSuccessState('ROSTO OVAL CAPTURADO', 'VETOR 128D PRONTO');
      showFeedback(
        feedbackModal,
        '✅ Rosto capturado exclusivamente na região oval com sucesso! Clique em "CADASTRAR OPERADOR E FACIAL" para guardar os vetores no banco.',
        'success'
      );
    });
  }

  if (formNovoUsuario) {
    formNovoUsuario.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Se a câmera estiver ligada e ainda não clicou em capturar, captura automaticamente o rosto na região oval
      if (!frameCadastroBase64 && scannerCadastro && scannerCadastro.isCameraActive) {
        if (typeof scannerCadastro.validarPresencaNaRegiaoOval === 'function') {
          const checagemOval = scannerCadastro.validarPresencaNaRegiaoOval();
          if (!checagemOval.ok) {
            scannerCadastro.setErrorState('ENQUADRE NA OVAL', 'APROXIME O ROSTO');
            showFeedback(feedbackModal, `⚠️ ${checagemOval.motivo}`, 'info');
            return;
          }
        }
        frameCadastroBase64 = scannerCadastro.captureFrameBase64() || '';
      }

      if (!frameCadastroBase64) {
        showFeedback(
          feedbackModal,
          '⚠️ A biometria facial é obrigatória! Ative a câmera, aproxime o rosto na região oval e clique em "CAPTURAR FACIAL" (ou envie uma foto JPEG/PNG).',
          'error'
        );
        return;
      }

      const btnSubmit = document.getElementById('btn-submit-novo-usuario');
      if (btnSubmit) btnSubmit.disabled = true;
      showFeedback(feedbackModal, 'Extraindo vetor biométrico 128D da região oval do rosto e salvando no banco de dados...', 'info');

      try {
        const res = await window.ServicoAPI.adicionarUsuarioMySQL({
          nome: document.getElementById('sql-input-nome')?.value || '',
          cpf: document.getElementById('sql-input-cpf')?.value || '',
          matricula: document.getElementById('sql-input-matricula')?.value || '',
          nivel_acesso: Number(document.getElementById('sql-select-role')?.value || 1),
          senha: document.getElementById('sql-input-senha')?.value || '',
          imagem_base64: frameCadastroBase64
        });

        formNovoUsuario.reset();
        frameCadastroBase64 = '';
        if (scannerCadastro) {
          scannerCadastro.setSuccessState('CADASTRO CONCLUÍDO', `ID: #${res.usuario?.id || 'OK'}`);
        }

        showFeedback(
          feedbackModal,
          `✅ ${res.mensagem} (Operador: ${res.usuario?.nome} | Matrícula: ${res.usuario?.matricula} | ID: #${res.usuario?.id})`,
          'success'
        );
        sincronizarDadosBancoMySQL();
      } catch (erro) {
        if (scannerCadastro) {
          scannerCadastro.setErrorState('FALHA NO CADASTRO', 'APROXIME NA REGIÃO OVAL');
        }
        showFeedback(
          feedbackModal,
          `❌ ${erro.message || 'Erro ao cadastrar operador no banco de dados.'} Aproxime o rosto na região oval e tente novamente.`,
          'error'
        );
      } finally {
        if (btnSubmit) btnSubmit.disabled = false;
      }
    });
  }

  // --------------------------------------------------------------------------
  // 5.7. Nível 3 — Aba Desbloquear Conta (POST /usuarios/{id}/desbloquear)
  // --------------------------------------------------------------------------
  const formDesbloquearManual = document.getElementById('form-desbloquear-manual');
  const inputDesbloqueioId = document.getElementById('sql-input-desbloqueio-id');
  const desbloqueioFeedback = document.getElementById('desbloqueio-feedback');

  async function executarDesbloqueioConta(identificador) {
    try {
      showFeedback(desbloqueioFeedback, `Desbloqueando conta '${identificador}' no banco de dados MySQL...`, 'info');
      const res = await window.ServicoAPI.desbloquearContaMySQL(identificador);
      showFeedback(
        desbloqueioFeedback,
        `✅ ${res.mensagem} (${res.bloqueios_desativados ?? 0} bloqueio(s) ativo(s) removido(s) no MySQL).`,
        'success'
      );
      renderizarTabelaBloqueiosNivel3();
      renderizarAuditoriaNivel3(toxinasCache);
    } catch (erro) {
      showFeedback(desbloqueioFeedback, `❌ ${erro.message || 'Erro ao desbloquear conta.'}`, 'error');
    }
  }

  if (formDesbloquearManual) {
    formDesbloquearManual.addEventListener('submit', async (e) => {
      e.preventDefault();
      const valor = inputDesbloqueioId ? inputDesbloqueioId.value.trim() : '';
      if (!valor) return;
      await executarDesbloqueioConta(valor);
      if (inputDesbloqueioId) inputDesbloqueioId.value = '';
    });
  }

  // --------------------------------------------------------------------------
  // 6. INICIALIZAÇÃO AUTOMÁTICA DA PÁGINA (RESPEITANDO PROTEÇÃO DE ROTAS)
  // --------------------------------------------------------------------------
  if (validarAcessoRota()) {
    const hashInicial = window.location.hash.replace('#', '').trim();
    if (!isSpaMode) {
      // Páginas standalone autenticadas
      ativarAbaNaTela(hashInicial || abaPadraoPorNivel[nivelAtual]);
    } else {
      // Caso o usuário dê F5 (reload) já estando autenticado na sessão
      window.abrirDashboardRole(nivelAtual, hashInicial || undefined);
    }
  }

  // --------------------------------------------------------------------------
  // UTILITÁRIOS DE UI
  // --------------------------------------------------------------------------
  function formatarCpfMascara(raw) {
    if (!/^\d+$/.test(String(raw).replace(/[.-]/g, ''))) return raw;
    let digits = String(raw).replace(/\D/g, '');
    if (digits.length > 11) digits = digits.slice(0, 11);
    if (digits.length > 9) return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
    if (digits.length > 6) return digits.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
    if (digits.length > 3) return digits.replace(/(\d{3})(\d{1,3})/, '$1.$2');
    return digits;
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function setBarWidth(id, pct) {
    const el = document.getElementById(id);
    if (el) el.style.width = `${Math.min(100, Math.max(0, pct))}%`;
  }

  function atualizarBarraComRotulo(barId, itemToxina, pctPadrao) {
    const barEl = document.getElementById(barId);
    if (!barEl) return;
    const pct = itemToxina ? pctPadrao : 20;
    barEl.style.width = `${Math.min(100, Math.max(0, pct))}%`;

    const segItem = barEl.closest('.seg-bar-item');
    const labelEl = segItem ? segItem.querySelector('label') : null;
    if (labelEl && itemToxina) {
      const nomeCurto = String(itemToxina.nome_comum || '').split('(')[0].trim();
      labelEl.textContent = `${nomeCurto} (${itemToxina.codigo_amostra})`;
    }
  }

  function atualizarDonut(circleId, labelId, pct) {
    const circle = document.getElementById(circleId);
    const label = document.getElementById(labelId);
    const val = Math.min(100, Math.max(0, Math.round(pct)));
    if (circle) {
      const dash = Math.round((val / 100) * 276);
      circle.setAttribute('stroke-dasharray', `${dash} 276`);
    }
    if (label) {
      label.textContent = `${val}%`;
    }
  }

  function showFeedback(el, msg, type) {
    if (!el) return;
    el.textContent = msg;
    el.className = `feedback-msg show ${type}`;
  }

  function clearFeedback(el) {
    if (!el) return;
    el.textContent = '';
    el.className = 'feedback-msg';
  }
});
