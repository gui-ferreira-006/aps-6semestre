/**
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Lógica Principal da Interface:
 * 1. Etapa de Login (CPF e Senha)
 * 2. Transição para Reconhecimento Facial (Biometria)
 * 3. Validações e Interatividade
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elementos da Etapa 1 (Login)
  const stepLogin = document.getElementById('step-login');
  const formLogin = document.getElementById('form-login');
  const cpfInput = document.getElementById('cpf-input');
  const passwordInput = document.getElementById('password-input');
  const btnTogglePwd = document.getElementById('btn-toggle-pwd');
  const eyeIcon = document.getElementById('eye-icon');
  const loginFeedback = document.getElementById('login-feedback');
  const forgotPwdLink = document.getElementById('link-forgot-pwd');

  // Elementos da Etapa 2 (Biometria)
  const stepBiometrics = document.getElementById('step-biometrics');
  const btnStartScan = document.getElementById('btn-start-scan');
  const btnScanLabel = document.getElementById('btn-scan-label');
  const btnBackLogin = document.getElementById('btn-back-login');
  const btnToggleCam = document.getElementById('btn-toggle-cam');
  const bioFeedback = document.getElementById('bio-feedback');

  // Inicializa o Scanner Facial
  let scanner = null;
  if (window.FaceScanner) {
    scanner = new window.FaceScanner('face-mesh-canvas', 'webcam-video');
  }

  // -------------------------------------------------------------------------
  // 1. Máscara de CPF (Formata se forem números, ou aceita qualquer texto de teste)
  // -------------------------------------------------------------------------
  cpfInput.addEventListener('input', (e) => {
    const raw = e.target.value;
    // Se o usuário digitou apenas números, aplica máscara de CPF
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

  // -------------------------------------------------------------------------
  // 2. Alternar Visibilidade da Senha
  // -------------------------------------------------------------------------
  let isPwdVisible = false;
  btnTogglePwd.addEventListener('click', () => {
    isPwdVisible = !isPwdVisible;
    passwordInput.type = isPwdVisible ? 'text' : 'password';

    if (isPwdVisible) {
      // Ícone com corte (olho fechado)
      eyeIcon.innerHTML = `
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
        <line x1="1" y1="1" x2="23" y2="23"></line>
      `;
    } else {
      // Ícone padrão (olho aberto)
      eyeIcon.innerHTML = `
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      `;
    }
  });

  // -------------------------------------------------------------------------
  // 3. Submissão do Formulário de Login -> Transição para Biometria
  // -------------------------------------------------------------------------
  formLogin.addEventListener('submit', async (e) => {
    e.preventDefault();

    const cpfVal = cpfInput.value.trim();
    const pwdVal = passwordInput.value.trim();

    /*
     * ========================================================================
     * [INTEGRAÇÃO BACKEND PYTHON (MYSQL / DOCKER) - ETAPA 1: CPF E SENHA]
     * O Docker e o MySQL ficam no Backend em Python, e este Frontend será
     * compactado para rodar integrado ao Python.
     * Quando o banco estiver ativo, descomente a gramática abaixo:
     *
     * try {
     *   await window.ServicoApiFaca.validarCredenciais(cpfVal, pwdVal);
     *   showFeedback(loginFeedback, 'Credenciais validadas. Iniciando biometria...', 'info');
     *   setTimeout(() => {
     *     clearFeedback(loginFeedback);
     *     transitionToStep('biometrics');
     *   }, 450);
     * } catch (erro) {
     *   showFeedback(loginFeedback, erro.message, 'error');
     * }
     * return;
     * ========================================================================
     */

    // Transição estrutural de interface (aguardando integração SQL no Backend Python)
    showFeedback(
      loginFeedback,
      'Aguardando integração SQL. Avançando para etapa biométrica...',
      'info'
    );

    setTimeout(() => {
      clearFeedback(loginFeedback);
      transitionToStep('biometrics');
    }, 450);
  });

  // -------------------------------------------------------------------------
  // 4. Transição Suave entre Etapas
  // -------------------------------------------------------------------------
  function transitionToStep(step) {
    if (step === 'biometrics') {
      stepLogin.classList.remove('active');
      setTimeout(() => {
        stepBiometrics.classList.add('active');
        if (scanner) {
          scanner.bindResize();
        }
      }, 150);
    } else {
      stepBiometrics.classList.remove('active');
      setTimeout(() => {
        stepLogin.classList.add('active');
      }, 150);
    }
  }

  // Voltar para a Etapa 1
  btnBackLogin.addEventListener('click', () => {
    clearFeedback(bioFeedback);
    if (scanner && scanner.isCameraActive) {
      scanner.stopWebcam();
      btnToggleCam.textContent = 'Ativar Câmera Real';
    }
    transitionToStep('login');
  });

  // -------------------------------------------------------------------------
  // 5. Interação de Reconhecimento Facial (Biometria) -> Nível de Acesso SQL
  // -------------------------------------------------------------------------
  btnStartScan.addEventListener('click', () => {
    if (!scanner || scanner.isScanning) return;

    btnStartScan.disabled = true;
    btnScanLabel.textContent = 'ESCANEANDO...';
    clearFeedback(bioFeedback);

    scanner.startScanning(async () => {
      btnScanLabel.textContent = 'LEITURA CONCLUÍDA';

      /*
       * ======================================================================
       * [INTEGRAÇÃO BACKEND PYTHON (MYSQL / DOCKER) - ETAPA 2: BIOMETRIA]
       * Quando o Backend Python + MySQL estiverem ativos, descomente a
       * gramática fixa abaixo para autenticar a face e redirecionar por nível:
       *
       * try {
       *   const base64Puro = capturarBase64Puro(scanner.canvas);
       *   const dadosAuth = await window.ServicoApiFaca.autenticarBiometria(base64Puro);
       *
       *   // Redirecionamento baseado em `nivel_acesso` (1, 2 ou 3) vindo do MySQL:
       *   // - Nível 3: Menu Completo (Níveis 1, 2 e 3) -> nivel3.html
       *   // - Nível 2: Menu Níveis 1 e 2 -> nivel3.html
       *   // - Nível 1: Somente Menu Nível 1 -> nivel3.html
       *   if (dadosAuth.usuario.nivel_acesso === 3) {
       *     window.location.href = 'nivel3.html';
       *   } else if (dadosAuth.usuario.nivel_acesso === 2) {
       *     window.location.href = 'nivel3.html';
       *   } else {
       *     window.location.href = 'nivel3.html';
       *   }
       * } catch (erro) {
       *   showFeedback(bioFeedback, erro.mensagem || 'Acesso negado pelo banco.', 'error');
       * }
       * ======================================================================
       */

      showFeedback(
        bioFeedback,
        'Captura concluída. Aguardando Backend Python / MySQL para validar acesso.',
        'info'
      );

      setTimeout(() => {
        btnStartScan.disabled = false;
        btnScanLabel.textContent = 'ESCANEAR NOVAMENTE';
      }, 2500);
    });
  });

  // Alternar Câmera Real
  btnToggleCam.addEventListener('click', async () => {
    if (!scanner) return;
    const active = await scanner.toggleWebcam();
    btnToggleCam.textContent = active ? 'Usar Malha Holográfica' : 'Ativar Câmera Real';
  });

  // Link Esqueceu sua senha
  forgotPwdLink.addEventListener('click', (e) => {
    e.preventDefault();
    showFeedback(loginFeedback, 'Solicitação enviada ao oficial de segurança.', 'info');
  });

  // Helpers de Feedback
  function showFeedback(el, msg, type) {
    el.textContent = msg;
    el.className = `feedback-msg show ${type}`;
  }

  function clearFeedback(el) {
    el.textContent = '';
    el.className = 'feedback-msg';
  }
});
