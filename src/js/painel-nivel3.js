/**
 * ============================================================================
 * F.A.C.A - Controlador da Tela de Nível 3 (Auditoria Global e Monitoramento)
 * ============================================================================
 *
 * ARQUITETURA:
 * - O Banco de Dados MySQL em Docker fica sob responsabilidade do Backend Python.
 * - O Frontend será compactado posteriormente para ser servido pelo Python.
 * - Este módulo gerencia o Menu Lateral cumulativo por Nível (1, 2 e 3) e deixa
 *   toda a gramática fixa comentada para quando os dados vierem do Python/MySQL.
 */

document.addEventListener('DOMContentLoaded', () => {
  const toastEl = document.getElementById('sql-config-toast');
  const workspaceEl = document.querySelector('.nivel3-workspace');
  const btnToggleMenu = document.getElementById('btn-toggle-menu');
  const logoTriggerExpand = document.getElementById('logo-trigger-expand');
  let toastTimeout = null;

  // --------------------------------------------------------------------------
  // 0. BOTÃO DE ESCONDER / MOSTRAR MENU (MOSTRA APENAS A LOGO E EXPANDE A TELA)
  // --------------------------------------------------------------------------
  function alternarVisibilidadeMenu() {
    if (!workspaceEl) return;
    const recolhido = workspaceEl.classList.toggle('menu-recolhido');
    if (btnToggleMenu) {
      btnToggleMenu.title = recolhido
        ? 'Mostrar menu completo'
        : 'Esconder menu (mostrar apenas a logo)';
    }
  }

  if (btnToggleMenu) {
    btnToggleMenu.addEventListener('click', alternarVisibilidadeMenu);
  }

  // Permite clicar na própria logo para reabrir o menu quando estiver recolhido
  if (logoTriggerExpand) {
    logoTriggerExpand.addEventListener('click', () => {
      if (workspaceEl && workspaceEl.classList.contains('menu-recolhido')) {
        alternarVisibilidadeMenu();
      }
    });
  }

  // --------------------------------------------------------------------------
  // 1. INICIALIZAÇÃO DO MENU LATERAL POR NÍVEL (Padrão Nível 3 nesta tela)
  // --------------------------------------------------------------------------
  if (window.MenuNiveisFaca) {
    // Na tela de Nível 3, usuários possuem role = 3 (visualizam Nível 1 + 2 + 3)
    window.MenuNiveisFaca.inicializarMenuNiveis(3);
  }

  // Botões de alternância para testar visualmente a regra de cada Nível no Menu
  const roleButtons = document.querySelectorAll('[data-role-preview]');
  roleButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const nivelSelecionado = Number(btn.getAttribute('data-role-preview'));
      if (window.MenuNiveisFaca) {
        window.MenuNiveisFaca.aplicarMenuPorNivel(nivelSelecionado);
      }
      exibirAvisoSQL(
        `Menu ajustado para Nível ${nivelSelecionado}: exibindo ${
          nivelSelecionado === 3
            ? 'tudo do menu (Níveis 1, 2 e 3)'
            : nivelSelecionado === 2
            ? 'tudo do Nível 2 e Nível 1'
            : 'somente a parte do menu de Nível 1'
        }.`
      );
    });
  });

  // --------------------------------------------------------------------------
  // 2. GRAMÁTICA FIXA PARA RENDERIZAR SESSÕES ATIVAS (PYTHON / MYSQL)
  // --------------------------------------------------------------------------
  function renderizarSessoesAtivasSQL(listaSessoes) {
    const tbody = document.getElementById('tbody-sessoes-ativas');
    if (!tbody || !Array.isArray(listaSessoes)) return;

    /*
     * [DESCOMENTAR QUANDO O BACKEND PYTHON + MYSQL ESTIVEREM ATIVOS]
     *
     * tbody.innerHTML = listaSessoes
     *   .map(
     *     (sessao) => `
     *       <tr>
     *         <td>${sessao.nome_usuario}</td>
     *         <td>${sessao.descricao}</td>
     *         <td>${sessao.data_sessao}</td>
     *         <td>${sessao.ultimo_acesso}</td>
     *       </tr>
     *     `
     *   )
     *   .join('');
     */
  }

  // --------------------------------------------------------------------------
  // 3. GRAMÁTICA FIXA PARA RENDERIZAR HISTÓRICO DE ACESSOS & EVENTOS
  // --------------------------------------------------------------------------
  function renderizarHistoricoEventosSQL(listaEventos) {
    const timelineUl = document.getElementById('lista-timeline-sql');
    const eventosUl = document.getElementById('lista-eventos-sql');
    if (!timelineUl || !eventosUl || !Array.isArray(listaEventos)) return;

    /*
     * [DESCOMENTAR QUANDO O BACKEND PYTHON + MYSQL ESTIVEREM ATIVOS]
     *
     * timelineUl.innerHTML = listaEventos
     *   .map(
     *     (ev, index) => `
     *       <li class="timeline-item ${index === 0 ? 'active' : ''}">
     *         <span class="timeline-node"></span>
     *         <div class="timeline-pill">${ev.data_hora}</div>
     *       </li>
     *     `
     *   )
     *   .join('');
     *
     * eventosUl.innerHTML = listaEventos
     *   .map(
     *     (ev) => `
     *       <li class="evento-row">
     *         <span class="evento-dot"></span>
     *         <div class="evento-info">
     *           <span class="evento-title">${ev.titulo_evento}</span>
     *           <span class="evento-desc">${ev.descricao_evento}</span>
     *         </div>
     *         ${
     *           ev.requer_desbloqueio
     *             ? `<button type="button" class="btn-unblock" data-unblock-id="${ev.usuario_id}">UNBLOCK</button>`
     *             : ''
     *         }
     *       </li>
     *     `
     *   )
     *   .join('');
     */
  }

  // --------------------------------------------------------------------------
  // 4. GRAMÁTICA FIXA PARA ATUALIZAR INDICADORES INFERIORES (TOXINAS E COFRE)
  // --------------------------------------------------------------------------
  function atualizarPanoramaToxinasSQL(dadosToxinas) {
    if (!dadosToxinas) return;
    /*
     * [DESCOMENTAR QUANDO O BACKEND PYTHON + MYSQL ESTIVEREM ATIVOS]
     *
     * document.getElementById('bar-dioxinas').style.width = `${dadosToxinas.dioxinas_pct}%`;
     * document.getElementById('label-inner-dioxinas').textContent = `${dadosToxinas.dioxinas_pct}%`;
     *
     * document.getElementById('bar-pfas').style.width = `${dadosToxinas.pfas_pct}%`;
     * document.getElementById('label-inner-pfas').textContent = `${dadosToxinas.pfas_pct}%`;
     *
     * document.getElementById('bar-fosfatos').style.width = `${dadosToxinas.fosfatos_pct}%`;
     * document.getElementById('label-inner-fosfatos').textContent = `${dadosToxinas.fosfatos_pct}%`;
     */
  }

  function atualizarMedidorCofreSQL(ocupacaoPercentual) {
    const arc = document.getElementById('cofre-gauge-arc');
    const val = document.getElementById('cofre-gauge-value');
    if (!arc || !val || typeof ocupacaoPercentual !== 'number') return;

    /*
     * [DESCOMENTAR QUANDO O BACKEND PYTHON + MYSQL ESTIVEREM ATIVOS]
     *
     * const comprimentoTotalArco = 205;
     * const offset = comprimentoTotalArco - (comprimentoTotalArco * ocupacaoPercentual) / 100;
     * arc.style.strokeDashoffset = String(offset);
     * val.textContent = `${ocupacaoPercentual}%`;
     */
  }

  // --------------------------------------------------------------------------
  // 5. EVENTOS DOS BOTÕES DE AÇÃO (AGUARDANDO BACKEND PYTHON + MYSQL)
  // --------------------------------------------------------------------------
  const sqlActionButtons = document.querySelectorAll('[data-sql-action]');
  sqlActionButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const acao = button.getAttribute('data-sql-action');

      /*
       * [DESCOMENTAR QUANDO O BACKEND PYTHON + MYSQL ESTIVEREM ATIVOS]
       * Aqui cada botão chamará `window.ServicoApiFaca`:
       * - 'adicionar-usuario' -> window.ServicoApiFaca.cadastrarNovoUsuario(...)
       * - 'desbloquear-conta' -> window.ServicoApiFaca.desbloquearContaUsuario(...)
       * - 'historico-acessos' -> window.ServicoApiFaca.obterDadosAuditoriaNivel3()
       */

      exibirAvisoSQL(
        `Ação [${acao.toUpperCase()}] pronta. Configure a ponte Python/MySQL em src/js/config/configuracao-banco.js.`
      );
    });
  });

  function exibirAvisoSQL(mensagem) {
    if (!toastEl) return;
    toastEl.textContent = mensagem;
    toastEl.classList.add('show');
    if (toastTimeout) clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
      toastEl.classList.remove('show');
    }, 3400);
  }

  window.FacaPainelNivel3 = {
    renderizarSessoesAtivasSQL,
    renderizarHistoricoEventosSQL,
    atualizarPanoramaToxinasSQL,
    atualizarMedidorCofreSQL
  };
});
