/**
 * ============================================================================
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Arquivo: src/js/painel-nivel3.js
 * Descrição: Controlador SPA das Telas e Abas por Role (Nível 1, Nível 2 e Nível 3),
 *            compatível diretamente com o servidor FastAPI Python (http://localhost:8000/)
 *            sem precisar alterar o main.py, mantendo a mesma configuração Python
 *            da Autenticação Facial (/autenticar) na aba do Nível 2 e pré-configuração MySQL.
 * ============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
  const spaViewLogin = document.getElementById('spa-view-login');
  const spaViewDashboard = document.getElementById('spa-view-dashboard');
  const isSpaMode = Boolean(spaViewLogin && spaViewDashboard);

  let nivelAtual = Number(document.body.getAttribute('data-role-nivel')) || 3;

  // Define a aba inicial padrão de cada Role
  const abaPadraoPorNivel = {
    1: 'estatisticas',
    2: 'cofre-status',
    3: 'historico'
  };

  // Inicializa o Scanner Facial da aba do Nível 2 com a mesma classe usada no Login Python
  let scannerNivel2 = null;
  if (window.FaceScanner) {
    const canvasId = document.getElementById('n2-face-mesh-canvas') ? 'n2-face-mesh-canvas' : 'face-mesh-canvas';
    const videoId = document.getElementById('n2-webcam-video') ? 'n2-webcam-video' : 'webcam-video';

    scannerNivel2 = new window.FaceScanner(canvasId, videoId, {
      laserId: 'n2-scan-laser',
      progressBarId: 'n2-scan-progress-bar',
      progressBoxId: 'n2-scan-progress-box',
      statusId: 'n2-hud-status-text',
      metricsId: 'n2-hud-metrics-text'
    });
  }

  // Atualiza destaque visual da barra superior de demonstração (#spa-top-switcher)
  function atualizarBotoesTopo(modo, roleAtivo) {
    const btnLogin = document.querySelector('#spa-top-switcher [data-spa-action="voltar-login"]');
    const btnsRole = document.querySelectorAll('#spa-top-switcher [data-spa-role]');

    if (btnLogin) {
      btnLogin.classList.toggle('active', modo === 'login');
    }
    btnsRole.forEach((btn) => {
      const n = Number(btn.getAttribute('data-spa-role'));
      btn.classList.toggle('active', modo === 'dashboard' && n === roleAtivo);
    });
  }

  // Ativa uma das 10 telas de aba (.tab-screen) e re-renderiza o menu cumulativo do Role atual
  function ativarAbaNaTela(nomeAba) {
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

    // Re-renderiza o menu lateral cumulativo conforme o Role (Nível 1, 2 ou 3)
    if (window.MenuNiveis) {
      window.MenuNiveis.renderizar({
        containerId: 'sidebar-menu-container',
        nivelPagina: nivelAtual,
        itemAtivo: nomeAba
      });
    }

    // Se a aba de Autenticação Facial do Nível 2 foi aberta, recalibra o canvas 3D
    if (nomeAba === 'autenticacao-facial' && scannerNivel2) {
      setTimeout(() => {
        scannerNivel2.bindResize();
      }, 60);
    }
  }

  // Abre o painel de um Role específico (1, 2 ou 3) sem sair da rota "/" do FastAPI
  window.abrirDashboardRole = function (roleNivel, abaOpcional) {
    nivelAtual = [1, 2, 3].includes(Number(roleNivel)) ? Number(roleNivel) : 1;
    sessionStorage.setItem('faca_role_nivel', String(nivelAtual));
    document.body.setAttribute('data-role-nivel', String(nivelAtual));

    if (isSpaMode) {
      spaViewLogin.style.display = 'none';
      spaViewDashboard.style.display = 'block';
      document.body.classList.add('dashboard-body');
      atualizarBotoesTopo('dashboard', nivelAtual);
    }

    const abaAlvo = abaOpcional || abaPadraoPorNivel[nivelAtual] || 'estatisticas';
    ativarAbaNaTela(abaAlvo);
  };

  // Retorna para a tela de Login Principal (Etapa 1/2)
  window.voltarParaLogin = function () {
    if (scannerNivel2 && scannerNivel2.isCameraActive) {
      scannerNivel2.stopWebcam();
      const btnCam = document.getElementById('btn-n2-toggle-cam');
      if (btnCam) btnCam.textContent = 'Ativar Câmera Real';
    }

    if (isSpaMode) {
      spaViewDashboard.style.display = 'none';
      spaViewLogin.style.display = 'flex';
      document.body.classList.remove('dashboard-body');
      atualizarBotoesTopo('login', null);
      history.replaceState(null, '', window.location.pathname);
    } else {
      window.location.href = '/';
    }
  };

  // Delegação global de cliques para navegação entre Roles, Abas do Menu e Voltar ao Login
  document.addEventListener('click', (e) => {
    const btnVoltar = e.target.closest('[data-spa-action="voltar-login"]');
    if (btnVoltar) {
      e.preventDefault();
      window.voltarParaLogin();
      return;
    }

    const btnRole = e.target.closest('[data-spa-role]');
    if (btnRole) {
      e.preventDefault();
      const novoRole = Number(btnRole.getAttribute('data-spa-role')) || 1;
      window.abrirDashboardRole(novoRole);
      return;
    }

    const btnTab = e.target.closest('[data-spa-tab]');
    if (btnTab) {
      e.preventDefault();
      const aba = btnTab.getAttribute('data-spa-tab');
      if (aba) {
        ativarAbaNaTela(aba);
      }
    }
  });

  // Inicialização automática: verifica se veio query ?role=X ou se está em página standalone
  const params = new URLSearchParams(window.location.search);
  const roleUrl = Number(params.get('role'));
  const hashInicial = window.location.hash.replace('#', '').trim();

  if (!isSpaMode) {
    // Páginas standalone (nivel1.html, nivel2.html, nivel3.html)
    ativarAbaNaTela(hashInicial || abaPadraoPorNivel[nivelAtual]);
  } else if ([1, 2, 3].includes(roleUrl)) {
    window.abrirDashboardRole(roleUrl, hashInicial || undefined);
  } else if (hashInicial && document.querySelector(`.tab-screen[data-tab-panel="${hashInicial}"]`)) {
    window.abrirDashboardRole(nivelAtual, hashInicial);
  }

  // --------------------------------------------------------------------------
  // NÍVEL 2: TRANSIÇÃO ENTRE COFRE BLOQUEADO, FACIAL E COFRE DESBLOQUEADO
  // --------------------------------------------------------------------------
  const viewCofreBloqueado = document.getElementById('view-cofre-bloqueado');
  const viewCofreDesbloqueado = document.getElementById('view-cofre-desbloqueado');
  const btnPreviewLocked = document.getElementById('btn-preview-cofre-locked');
  const btnPreviewUnlocked = document.getElementById('btn-preview-cofre-unlocked');
  const btnIrFacial = document.getElementById('btn-ir-autenticacao-facial');

  function alternarEstadoCofre(desbloqueado) {
    if (!viewCofreBloqueado || !viewCofreDesbloqueado) return;
    if (desbloqueado) {
      viewCofreBloqueado.style.display = 'none';
      viewCofreDesbloqueado.style.display = 'block';
      if (btnPreviewLocked) btnPreviewLocked.classList.remove('active');
      if (btnPreviewUnlocked) btnPreviewUnlocked.classList.add('active');
    } else {
      viewCofreBloqueado.style.display = 'block';
      viewCofreDesbloqueado.style.display = 'none';
      if (btnPreviewLocked) btnPreviewLocked.classList.add('active');
      if (btnPreviewUnlocked) btnPreviewUnlocked.classList.remove('active');
    }
  }

  if (btnPreviewLocked) {
    btnPreviewLocked.addEventListener('click', () => alternarEstadoCofre(false));
  }

  if (btnPreviewUnlocked) {
    btnPreviewUnlocked.addEventListener('click', () => alternarEstadoCofre(true));
  }

  if (btnIrFacial) {
    btnIrFacial.addEventListener('click', () => {
      ativarAbaNaTela('autenticacao-facial');
    });
  }

  // --------------------------------------------------------------------------
  // NÍVEL 2 — ABA AUTENTICAÇÃO FACIAL:
  // Usa exatamente a mesma configuração Python da facial no JS (POST /autenticar)
  // --------------------------------------------------------------------------
  const btnN2StartScan = document.getElementById('btn-n2-start-scan');
  const btnN2ScanLabel = document.getElementById('btn-n2-scan-label');
  const btnN2CancelScan = document.getElementById('btn-n2-cancel-scan');
  const btnN2ToggleCam = document.getElementById('btn-n2-toggle-cam');
  const n2InputOperador = document.getElementById('n2-input-operador-id');
  const n2InputSetor = document.getElementById('n2-input-setor');
  const n2BioFeedback = document.getElementById('n2-bio-feedback');

  if (n2InputOperador) {
    n2InputOperador.addEventListener('input', (e) => {
      const raw = e.target.value;
      if (/^\d+$/.test(raw.replace(/[.-]/g, ''))) {
        let digits = raw.replace(/\D/g, '');
        if (digits.length > 11) digits = digits.slice(0, 11);
        if (digits.length > 9) {
          e.target.value = digits.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
        } else if (digits.length > 6) {
          e.target.value = digits.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
        } else if (digits.length > 3) {
          e.target.value = digits.replace(/(\d{3})(\d{1,3})/, '$1.$2');
        } else {
          e.target.value = digits;
        }
      }
    });
  }

  if (btnN2ToggleCam && scannerNivel2) {
    btnN2ToggleCam.addEventListener('click', async () => {
      clearFeedback(n2BioFeedback);
      const active = await scannerNivel2.toggleWebcam();
      btnN2ToggleCam.textContent = active ? 'Usar Malha Holográfica' : 'Ativar Câmera Real';

      if (active) {
        showFeedback(n2BioFeedback, 'Câmera ativada. Posicione seu rosto no centro do enquadramento.', 'info');
      } else {
        scannerNivel2.resetState();
        showFeedback(n2BioFeedback, 'Modo holográfico ativo. Ative a câmera real para validação das 5 fases.', 'info');
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

      // Verifica se a câmera real está ativa (mesma regra de principal.js)
      if (!scannerNivel2.isCameraActive) {
        showFeedback(
          n2BioFeedback,
          '⚠️ A câmera real não está ativa! Clique em "Ativar Câmera Real" abaixo para permitir a captura facial.',
          'info'
        );
        return;
      }

      const cpfOperador = n2InputOperador ? n2InputOperador.value.trim() : '';
      const senhaOperador = n2InputSetor ? n2InputSetor.value.trim() : '';

      if (!cpfOperador || !senhaOperador) {
        showFeedback(
          n2BioFeedback,
          'Informe o ID do Operador (CPF) e a Senha de Liberação antes de iniciar o escaneamento.',
          'error'
        );
        return;
      }

      btnN2StartScan.disabled = true;
      if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'ENVIANDO AO MOTOR PIVC...';
      clearFeedback(n2BioFeedback);
      scannerNivel2.setScanningState(true, 'ANALISANDO TRAÇOS FACIAIS...');

      // 1. Captura o quadro real da webcam em Base64 (mesmo método do Python / principal.js)
      const frameBase64 = scannerNivel2.captureFrameBase64();

      if (!frameBase64) {
        scannerNivel2.setErrorState('ERRO DE CAPTURA', 'FRAME NULO');
        showFeedback(n2BioFeedback, 'Não foi possível capturar o quadro do vídeo. Verifique se a câmera está conectada.', 'error');
        btnN2StartScan.disabled = false;
        if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'TENTAR NOVAMENTE';
        return;
      }

      // 2. Envia para o backend FastAPI Python (POST /autenticar)
      try {
        const payload = {
          cpf: cpfOperador,
          senha: senhaOperador,
          imagem_base64: frameBase64
        };

        const resposta = await fetch('/autenticar', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        const dados = await resposta.json();

        // 3. Processamento idêntico ao principal.js conforme Status HTTP do Python:
        if (resposta.status === 200 && dados.sucesso) {
          const biometriaInfo = dados.biometria;
          const distTxt = biometriaInfo ? biometriaInfo.distancia_euclidiana.toFixed(4) : '0.0000';
          const confTxt = biometriaInfo ? biometriaInfo.confianca_percentual.toFixed(1) : '100.0';

          scannerNivel2.setSuccessState(
            'COFRE DESBLOQUEADO',
            `DIST: ${distTxt} | CONF: ${confTxt}%`
          );

          if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'ACESSO CONCEDIDO';
          showFeedback(
            n2BioFeedback,
            `ACESSO AO COFRE LIBERADO: Nível ${dados.usuario.nivel_acesso} — ${dados.usuario.nome}. Distância: ${distTxt} (${confTxt}%)`,
            'success'
          );

          // Libera a visualização do Cofre Desbloqueado na aba Cofre Seguro (Status)
          setTimeout(() => {
            btnN2StartScan.disabled = false;
            if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'INICIAR ESCANEAMENTO';
            alternarEstadoCofre(true);
            ativarAbaNaTela('cofre-status');
          }, 1400);

        } else if (resposta.status === 400) {
          const codigo = dados.erro?.codigo || 'CAPTURE_ERROR';
          const mensagem = dados.erro?.mensagem || 'Falha na captura biométrica.';

          scannerNivel2.setErrorState(codigo, 'REPOSICIONE O ROSTO');
          showFeedback(n2BioFeedback, `⚠️ ${mensagem}`, 'info');

          btnN2StartScan.disabled = false;
          if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'ESCANEAR NOVAMENTE';

        } else if (resposta.status === 401) {
          const tentativasRestantes = dados.tentativas_restantes !== undefined ? dados.tentativas_restantes : '?';
          const mensagem = dados.erro?.mensagem || 'Acesso Negado.';

          scannerNivel2.setErrorState('ACESSO NEGADO', `TENTATIVAS: ${tentativasRestantes}`);
          showFeedback(n2BioFeedback, `❌ ${mensagem} [Tentativas restantes: ${tentativasRestantes}]`, 'error');

          btnN2StartScan.disabled = false;
          if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'TENTAR NOVAMENTE';

        } else if (resposta.status === 403) {
          const mensagem = dados.erro?.mensagem || 'Terminal bloqueado por suspeita de ameaça.';

          scannerNivel2.setErrorState('TERMINAL BLOQUEADO', 'CONTA BLOQUEADA');
          showFeedback(n2BioFeedback, `🚨 ${mensagem}`, 'error');

          btnN2StartScan.disabled = true;
          if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'ACESSO BLOQUEADO';

        } else {
          const mensagem = dados.erro?.mensagem || 'Erro interno no motor biométrico.';
          scannerNivel2.setErrorState('ERRO INTERNO', 'MOTOR BIOMÉTRICO');
          showFeedback(n2BioFeedback, `❌ ${mensagem}`, 'error');

          btnN2StartScan.disabled = false;
          if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'TENTAR NOVAMENTE';
        }

      } catch (erro) {
        console.error('Falha na comunicação com o backend Python:', erro);
        scannerNivel2.setErrorState('ERRO DE REDE', 'OFFLINE');
        showFeedback(n2BioFeedback, '❌ Falha de comunicação com o servidor Python F.A.C.A. Verifique se o backend está online.', 'error');
        btnN2StartScan.disabled = false;
        if (btnN2ScanLabel) btnN2ScanLabel.textContent = 'TENTAR NOVAMENTE';
      }
    });
  }

  // --------------------------------------------------------------------------
  // FORMULÁRIOS PRÉ-CONFIGURADOS PARA O BANCO DE DADOS MYSQL (SEM DADOS FICTÍCIOS)
  // --------------------------------------------------------------------------
  const formNovoUsuario = document.getElementById('form-novo-usuario-sql');
  const feedbackModal = document.getElementById('modal-sql-feedback');

  if (formNovoUsuario) {
    formNovoUsuario.addEventListener('submit', async (e) => {
      e.preventDefault();
      /*
       * === [DESCOMENTAR QUANDO O BANCO DE DADOS MYSQL ESTIVER CONECTADO] ===
       * await window.ServicoAPI.adicionarUsuarioMySQL({
       *   nome: document.getElementById('sql-input-nome').value,
       *   cpf: document.getElementById('sql-input-cpf').value,
       *   matricula: document.getElementById('sql-input-matricula').value,
       *   nivel_acesso: Number(document.getElementById('sql-select-role').value),
       *   senha: document.getElementById('sql-input-senha').value
       * });
       */
      showFeedback(
        feedbackModal,
        'Pré-configurado: aguardando conexão com o banco de dados MySQL para executar INSERT INTO usuarios.',
        'info'
      );
    });
  }

  const formGeradorPdf = document.getElementById('form-gerador-pdf');
  const pdfFeedback = document.getElementById('pdf-feedback');

  if (formGeradorPdf) {
    formGeradorPdf.addEventListener('submit', (e) => {
      e.preventDefault();
      /*
       * === [DESCOMENTAR QUANDO O BANCO DE DADOS MYSQL ESTIVER CONECTADO] ===
       * Consulta os registros filtrados no MySQL e preenche #tbody-pdf-preview
       */
      showFeedback(
        pdfFeedback,
        'Pré-configurado: aguardando conexão com o banco de dados MySQL para gerar relatório.',
        'info'
      );
    });
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
