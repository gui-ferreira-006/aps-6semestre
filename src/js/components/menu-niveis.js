/**
 * ============================================================================
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Arquivo: src/js/components/menu-niveis.js
 * Descrição: Renderizador do Menu Lateral Cumulativo por Role (Nível 1, 2 e 3)
 *            Operando em modo SPA (Single Page Application) na rota raiz (/)
 *            com controle estrito de autenticação (sem botões de pré-visualização
 *            ou troca livre de nível sem login validado).
 * ============================================================================
 *
 * REGRA DE VISIBILIDADE DO MENU POR ROLE AUTENTICADA:
 * - Role Nível 1: Exibe SOMENTE a seção "NÍVEL 1 (Relatórios)" + "SAIR (Logout)"
 * - Role Nível 2: Exibe "NÍVEL 1 (Relatórios)" + "NÍVEL 2 (Cofre)" + "SAIR (Logout)"
 * - Role Nível 3: Exibe TODO o menu ("NÍVEL 1" + "NÍVEL 2" + "NÍVEL 3 (Auditoria)") + "SAIR (Logout)"
 */

(function () {
  const ABAS_POR_NIVEL = {
    estatisticas: 1,
    panorama: 1,
    alertas: 1,
    pdf: 1,
    'cofre-status': 2,
    inventario: 2,
    'autenticacao-facial': 2,
    historico: 3,
    adicionar: 3,
    desbloquear: 3
  };

  function obterRoleAtual(fallback = 1) {
    if (window.ServicoAPI && window.ServicoAPI.estaAutenticado()) {
      const nivelLogado = window.ServicoAPI.obterNivelAcessoLogado();
      if ([1, 2, 3].includes(nivelLogado)) {
        return nivelLogado;
      }
    }
    const salvo = Number(sessionStorage.getItem('faca_role_nivel'));
    if (salvo === 1 || salvo === 2 || salvo === 3) {
      return salvo;
    }
    return fallback;
  }

  function definirRoleAtual(novaRole) {
    const r = Number(novaRole);
    if (r === 1 || r === 2 || r === 3) {
      sessionStorage.setItem('faca_role_nivel', String(r));
      document.body.setAttribute('data-role-nivel', String(r));
    }
  }

  function renderizarMenuPorRole(opcoes = {}) {
    const container = document.getElementById(opcoes.containerId || 'sidebar-menu-container');
    if (!container) return;

    // Não renderiza o menu caso o usuário não esteja autenticado
    if (window.ServicoAPI && !window.ServicoAPI.estaAutenticado()) {
      container.innerHTML = '';
      return;
    }

    const roleNivel = Number(opcoes.roleNivel) || obterRoleAtual(1);
    const usuarioLogado = window.ServicoAPI ? window.ServicoAPI.obterUsuarioLogado() : null;
    const nomeOperador = usuarioLogado?.nome || 'Operador Autenticado';
    const cargoOperador = usuarioLogado?.cargo || `Nível ${roleNivel}`;

    const itemAtivo = opcoes.itemAtivo || (roleNivel === 3 ? 'historico' : roleNivel === 2 ? 'cofre-status' : 'estatisticas');
    const nivelDaAbaAtiva = ABAS_POR_NIVEL[itemAtivo] || roleNivel;

    // ------------------------------------------------------------------------
    // SEÇÃO NÍVEL 1 (Relatórios) -> Visível para Role 1, Role 2 e Role 3
    // ------------------------------------------------------------------------
    const blocoNivel1 = `
      <div class="menu-section ${nivelDaAbaAtiva === 1 ? 'section-highlighted' : ''}" data-menu-level="1">
        <a href="#estatisticas" data-spa-tab="estatisticas" class="menu-section-title">
          <span class="section-icon-grid">
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="1.5" y="1.5" width="5" height="5" rx="1"/>
              <rect x="9.5" y="1.5" width="5" height="5" rx="1"/>
              <rect x="1.5" y="9.5" width="5" height="5" rx="1"/>
              <rect x="9.5" y="9.5" width="5" height="5" rx="1"/>
            </svg>
          </span>
          <span><strong>NÍVEL 1</strong> <small>(Relatórios)</small></span>
        </a>
        <ul class="menu-items-list">
          <li>
            <a href="#estatisticas" data-spa-tab="estatisticas"
               class="menu-item-link ${itemAtivo === 'estatisticas' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="20" x2="18" y2="10"/>
                  <line x1="12" y1="20" x2="12" y2="4"/>
                  <line x1="6" y1="20" x2="6" y2="14"/>
                </svg>
              </span>
              <span>SÍNTESE DE ESTATÍSTICAS</span>
            </a>
          </li>
          <li>
            <a href="#panorama" data-spa-tab="panorama"
               class="menu-item-link ${itemAtivo === 'panorama' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M12 2v3m0 14v3M2 12h3m14 0h3m-2.93-7.07l-2.12 2.12M7.05 16.95l-2.12 2.12m0-14.14l2.12 2.12m9.9 9.9l2.12 2.12"/>
                </svg>
              </span>
              <span>PANORAMA DE TOXINAS</span>
            </a>
          </li>
          <li>
            <a href="#alertas" data-spa-tab="alertas"
               class="menu-item-link ${itemAtivo === 'alertas' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
              </span>
              <span>HISTÓRICO DE ALERTAS</span>
            </a>
          </li>
          <li>
            <a href="#pdf" data-spa-tab="pdf"
               class="menu-item-link ${itemAtivo === 'pdf' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>
              </span>
              <span>GERADOR PDF</span>
            </a>
          </li>
        </ul>
      </div>
    `;

    // ------------------------------------------------------------------------
    // SEÇÃO NÍVEL 2 (Cofre) -> Visível APENAS para Role 2 e Role 3
    // ------------------------------------------------------------------------
    const blocoNivel2 = roleNivel >= 2 ? `
      <div class="menu-sep"></div>
      <div class="menu-section ${nivelDaAbaAtiva === 2 ? 'section-highlighted' : ''}" data-menu-level="2">
        <a href="#cofre-status" data-spa-tab="cofre-status" class="menu-section-title">
          <span class="section-icon-grid">
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="1.5" y="1.5" width="5" height="5" rx="1"/>
              <rect x="9.5" y="1.5" width="5" height="5" rx="1"/>
              <rect x="1.5" y="9.5" width="5" height="5" rx="1"/>
              <rect x="9.5" y="9.5" width="5" height="5" rx="1"/>
            </svg>
          </span>
          <span><strong>NÍVEL 2</strong> <small>(Cofre)</small></span>
        </a>
        <ul class="menu-items-list">
          <li>
            <a href="#cofre-status" data-spa-tab="cofre-status"
               class="menu-item-link ${itemAtivo === 'cofre-status' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </span>
              <span>COFRE SEGURO <small>(Status)</small></span>
            </a>
          </li>
          <li>
            <a href="#inventario" data-spa-tab="inventario"
               class="menu-item-link ${itemAtivo === 'inventario' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <ellipse cx="12" cy="5" rx="9" ry="3"/>
                  <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
                  <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
                </svg>
              </span>
              <span>INVENTÁRIO DE TOXINAS</span>
            </a>
          </li>
          <li>
            <a href="#autenticacao-facial" data-spa-tab="autenticacao-facial"
               class="menu-item-link ${itemAtivo === 'autenticacao-facial' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 7V5a2 2 0 0 1 2-2h2"/>
                  <path d="M17 3h2a2 2 0 0 1 2 2v2"/>
                  <path d="M21 17v2a2 2 0 0 1-2 2h-2"/>
                  <path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
                  <circle cx="12" cy="12" r="3"/>
                </svg>
              </span>
              <span>AUTENTICAÇÃO FACIAL</span>
            </a>
          </li>
        </ul>
      </div>
    ` : '';

    // ------------------------------------------------------------------------
    // SEÇÃO NÍVEL 3 (Auditoria) -> Visível APENAS para Role 3
    // ------------------------------------------------------------------------
    const blocoNivel3 = roleNivel >= 3 ? `
      <div class="menu-sep"></div>
      <div class="menu-section menu-section-nivel3 ${nivelDaAbaAtiva === 3 ? 'section-highlighted' : ''}" data-menu-level="3">
        <a href="#historico" data-spa-tab="historico" class="menu-section-title">
          <span class="section-icon-grid">
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </span>
          <span><strong>NÍVEL 3</strong> <small>(Auditoria)</small></span>
        </a>
        <ul class="menu-items-list">
          <li>
            <a href="#historico" data-spa-tab="historico"
               class="menu-item-link ${itemAtivo === 'historico' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>
                  <line x1="17" y1="11" x2="22" y2="11"/>
                  <line x1="17" y1="15" x2="22" y2="15"/>
                </svg>
              </span>
              <span>HISTÓRICO DE ACESSOS</span>
            </a>
          </li>
          <li>
            <a href="#adicionar" data-spa-tab="adicionar"
               class="menu-item-link item-add-red ${itemAtivo === 'adicionar' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
              </span>
              <span>ADICIONAR</span>
            </a>
          </li>
          <li>
            <a href="#desbloquear" data-spa-tab="desbloquear"
               class="menu-item-link ${itemAtivo === 'desbloquear' ? 'active' : ''}">
              <span class="item-icon">
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 9.9-1"/>
                </svg>
              </span>
              <span>DESBLOQUEAR CONTA</span>
            </a>
          </li>
        </ul>
      </div>
    ` : '';

    container.innerHTML = `
      <aside class="faca-sidebar" aria-label="Menu Lateral por Role">
        <div class="sidebar-header-brand">
          <div class="sidebar-mini-shield">
            <svg viewBox="0 0 160 160" width="38" height="38">
              <path d="M22 68 L36 68 L48 80 L48 102" fill="none" stroke="#cfd6e0" stroke-width="3" stroke-linecap="round"/>
              <path d="M138 68 L124 68 L112 80 L112 102" fill="none" stroke="#cfd6e0" stroke-width="3" stroke-linecap="round"/>
              <path d="M80 18 L118 42 L118 102 L98 126 L62 126 L42 102 L42 42 Z"
                    fill="none" stroke="#dfe4ec" stroke-width="5.5" stroke-linejoin="round" />
              <path d="M80 38 L100 52 L100 92 L88 106 L72 106 L60 92 L60 52 Z"
                    fill="none" stroke="#ff223e" stroke-width="3.5" />
              <circle cx="80" cy="74" r="22" fill="rgba(230, 20, 44, 0.4)" />
              <g transform="translate(68, 62)">
                <rect x="3" y="10" width="18" height="14" rx="2.5" fill="#e6142c" stroke="#ff475b" stroke-width="1.5" />
                <path d="M6 10 V6 A6 6 0 0 1 18 6 V10" fill="none" stroke="#ff6b7b" stroke-width="2.5" stroke-linecap="round" />
              </g>
            </svg>
          </div>
          <div class="sidebar-brand-titles">
            <span class="sidebar-faca-title">F.A.C.A</span>
            <span class="sidebar-faca-sub">${nomeOperador} (${cargoOperador})</span>
          </div>
        </div>

        <div class="menu-sep"></div>

        <nav class="sidebar-menu-nav">
          ${blocoNivel1}
          ${blocoNivel2}
          ${blocoNivel3}
        </nav>

        <div class="menu-sep"></div>

        <div class="sidebar-footer-access">
          <a href="#logout" data-spa-action="voltar-login" class="menu-access-link" id="btn-sidebar-logout">
            <span class="access-icon">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </span>
            <span><strong>ENCERRAR SESSÃO</strong> <small>(Sair)</small></span>
          </a>
        </div>
      </aside>
    `;
  }

  window.MenuNiveis = {
    renderizar: renderizarMenuPorRole,
    obterRoleAtual,
    definirRoleAtual,
    ABAS_POR_NIVEL
  };
})();
