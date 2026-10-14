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
  // 1. Máscara Automática de CPF (000.000.000-00)
  // -------------------------------------------------------------------------
  cpfInput.addEventListener('input', (e) => {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 11) value = value.slice(0, 11);

    if (value.length > 9) {
      value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
    } else if (value.length > 6) {
      value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
    } else if (value.length > 3) {
      value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
    }

    e.target.value = value;
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
  formLogin.addEventListener('submit', (e) => {
    e.preventDefault();

    const cpfVal = cpfInput.value.trim();
    const pwdVal = passwordInput.value.trim();

    if (!cpfVal || !pwdVal) {
      showFeedback(loginFeedback, 'Preencha o CPF e a senha para continuar.', 'error');
      return;
    }

    // Feedback temporário de validação
    showFeedback(loginFeedback, 'Credenciais verificadas. Iniciando módulo biométrico...', 'info');

    setTimeout(() => {
      clearFeedback(loginFeedback);
      transitionToStep('biometrics');
    }, 600);
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
  // 5. Interação de Reconhecimento Facial (Biometria)
  // -------------------------------------------------------------------------
  btnStartScan.addEventListener('click', () => {
    if (!scanner || scanner.isScanning) return;

    btnStartScan.disabled = true;
    btnScanLabel.textContent = 'ESCANEANDO...';
    clearFeedback(bioFeedback);

    scanner.startScanning(() => {
      // Callback ao concluir leitura
      btnScanLabel.textContent = 'RECONHECIMENTO CONCLUÍDO';
      showFeedback(
        bioFeedback,
        'ACESSO LIBERADO: Nível 2 - Divisão de Toxinas e Preservação',
        'success'
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
