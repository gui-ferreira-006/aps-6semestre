/**
 * ============================================================================
 * F.A.C.A - Controle Cumulativo do Menu Lateral por Nível de Acesso
 * ============================================================================
 *
 * REGRA DE NEGÓCIO DOS NÍVEIS DO MENU:
 * - Nível 1 (`nivel = 1`): Mostra SOMENTE a parte do menu de Nível 1 (Relatórios).
 * - Nível 2 (`nivel = 2`): Mostra TUDO do menu de Nível 2 e Nível 1 (Relatórios + Cofre).
 * - Nível 3 (`nivel = 3`): Mostra TUDO daquele menu (Nível 1 + Nível 2 + Nível 3 Auditoria).
 */

(function () {
  /**
   * Aplica a visibilidade cumulativa das seções do menu lateral de acordo com
   * o nível de acesso (1, 2 ou 3) do usuário retornado pelo Backend Python / MySQL.
   *
   * @param {number} nivelUsuario - Nível de acesso (1, 2 ou 3)
   */
  function aplicarMenuPorNivel(nivelUsuario) {
    const nivelNumerico = Number(nivelUsuario) || 3;

    // Regra cumulativa:
    // Nível 1 -> [1]
    // Nível 2 -> [1, 2]
    // Nível 3 -> [1, 2, 3]
    const niveisPermitidos = [];
    if (nivelNumerico >= 1) niveisPermitidos.push(1);
    if (nivelNumerico >= 2) niveisPermitidos.push(2);
    if (nivelNumerico >= 3) niveisPermitidos.push(3);

    // Filtra os blocos do menu lateral marcados com data-menu-nivel="1|2|3"
    const gruposMenu = document.querySelectorAll('[data-menu-nivel]');
    gruposMenu.forEach((grupo) => {
      const nivelDoGrupo = Number(grupo.getAttribute('data-menu-nivel'));
      if (niveisPermitidos.includes(nivelDoGrupo)) {
        grupo.style.display = '';
        grupo.removeAttribute('aria-hidden');
      } else {
        grupo.style.display = 'none';
        grupo.setAttribute('aria-hidden', 'true');
      }
    });

    // Atualiza os botões de pré-visualização de nível na barra superior
    const botoesNivel = document.querySelectorAll('[data-role-preview]');
    botoesNivel.forEach((btn) => {
      const btnNivel = Number(btn.getAttribute('data-role-preview'));
      btn.classList.toggle('active', btnNivel === nivelNumerico);
    });

    // Atualiza indicador textual de nível ativo
    const indicadorNivel = document.getElementById('rbac-role-indicator');
    if (indicadorNivel) {
      const descricoes = {
        1: 'MENU: SOMENTE NÍVEL 1',
        2: 'MENU: NÍVEIS 1 E 2',
        3: 'MENU: NÍVEIS 1, 2 E 3'
      };
      indicadorNivel.textContent = descricoes[nivelNumerico] || descricoes[3];
    }
  }

  /**
   * Inicializa o menu lateral lendo o nível do usuário (quando o SQL estiver ativo)
   * ou aplicando o nível padrão da tela atual sem inventar sessão fictícia.
   */
  function inicializarMenuNiveis(nivelPadraoDaTela = 3) {
    /*
     * [DESCOMENTAR QUANDO O BACKEND PYTHON + MYSQL ESTIVEREM CONECTADOS]
     *
     * const usuarioJson = sessionStorage.getItem('faca_usuario');
     * if (usuarioJson) {
     *   const usuario = JSON.parse(usuarioJson);
     *   // usuario.nivel_acesso vem do MySQL (1, 2 ou 3)
     *   aplicarMenuPorNivel(usuario.nivel_acesso);
     *   return;
     * }
     */

    aplicarMenuPorNivel(nivelPadraoDaTela);
  }

  window.MenuNiveisFaca = {
    aplicarMenuPorNivel,
    inicializarMenuNiveis
  };
})();
