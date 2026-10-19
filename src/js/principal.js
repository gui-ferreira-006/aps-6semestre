/**
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Lógica Principal da Interface:
 * 1. Etapa de Login (CPF e Senha)
 * 2. Transição para Reconhecimento Facial (Biometria Real com PIVC)
 * 3. Integração com API RESTful FastAPI (/autenticar)
 * 4. Validações, Feedback Contextual e Controle de Tentativas/Bloqueio
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

  // Estado da Autenticação em Memória do Cliente
  let currentCpf = '';
  let currentPassword = '';

  // Inicializa o Scanner Facial Holográfico / Câmera Real
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

    let cpfVal = cpfInput.value.trim();
    let pwdVal = passwordInput.value.trim();

    // Valores padrão de demonstração para agilizar testes locais
    if (!cpfVal) {
      cpfVal = '123.456.789-00';
      cpfInput.value = cpfVal;
    }
    if (!pwdVal) {
      pwdVal = 'Faca@2026';
      passwordInput.value = pwdVal;
    }

    currentCpf = cpfVal;
    currentPassword = pwdVal;

    // Feedback visual de validação
    showFeedback(loginFeedback, 'Identificação confirmada. Carregando módulo biométrico...', 'info');

    setTimeout(async () => {
      clearFeedback(loginFeedback);
      transitionToStep('biometrics');

      // Tenta iniciar a webcam real automaticamente na transição
      if (scanner && !scanner.isCameraActive) {
        const camAtiva = await scanner.startWebcam();
        if (camAtiva) {
          btnToggleCam.textContent = 'Usar Malha Holográfica';
          showFeedback(bioFeedback, 'Câmera operacional. Enquadre seu rosto e clique em Iniciar Reconhecimento.', 'info');
        } else {
          btnToggleCam.textContent = 'Ativar Câmera Real';
          showFeedback(bioFeedback, 'Câmera real desativada. Para validação biométrica real, clique em "Ativar Câmera Real" abaixo.', 'info');
        }
      }
    }, 350);
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
    if (scanner) {
      scanner.resetState();
      if (scanner.isCameraActive) {
        scanner.stopWebcam();
        btnToggleCam.textContent = 'Ativar Câmera Real';
      }
    }
    transitionToStep('login');
  });

  // -------------------------------------------------------------------------
  // 5. Interação de Reconhecimento Facial (Biometria Real via API)
  // -------------------------------------------------------------------------
  btnStartScan.addEventListener('click', async () => {
    if (!scanner || scanner.isScanning) return;

    // Verifica se a câmera real está ativa para permitir a extração biométrica das 5 fases
    if (!scanner.isCameraActive) {
      showFeedback(
        bioFeedback,
        '⚠️ A câmera real não está ativa! Clique em "Ativar Câmera Real" abaixo para permitir a captura facial.',
        'info'
      );
      return;
    }

    btnStartScan.disabled = true;
    btnScanLabel.textContent = 'ENVIANDO AO MOTOR PIVC...';
    clearFeedback(bioFeedback);
    scanner.setScanningState(true, 'ANALISANDO BIOMETRIA (PIVC)...');

    // 1. Captura o quadro real da webcam em Base64
    const frameBase64 = scanner.captureFrameBase64();

    if (!frameBase64) {
      scanner.setErrorState('ERRO DE CAPTURA', 'FRAME NULO');
      showFeedback(bioFeedback, 'Não foi possível capturar o quadro do vídeo. Verifique se a câmera está conectada.', 'error');
      btnStartScan.disabled = false;
      btnScanLabel.textContent = 'TENTAR NOVAMENTE';
      return;
    }

    // 2. Envia para o backend FastAPI (POST /autenticar)
    try {
      const payload = {
        cpf: currentCpf,
        senha: currentPassword,
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

      // 3. Processamento das Respostas Conforme o Status HTTP da API:
      if (resposta.status === 200 && dados.sucesso) {
        // --- SUCESSO: HTTP 200 (Autenticação MFA Concluída) ---
        const biometriaInfo = dados.biometria;
        const distTxt = biometriaInfo ? biometriaInfo.distancia_euclidiana.toFixed(4) : '0.0000';
        const confTxt = biometriaInfo ? biometriaInfo.confianca_percentual.toFixed(1) : '100.0';

        scanner.setSuccessState(
          'ACESSO AUTORIZADO',
          `DIST: ${distTxt} | CONF: ${confTxt}%`
        );

        btnScanLabel.textContent = 'ACESSO CONCEDIDO';
        showFeedback(
          bioFeedback,
          `ACESSO LIBERADO: Nível ${dados.usuario.nivel_acesso} — ${dados.usuario.nome} (${dados.usuario.cargo}). Distância Euclidiana: ${distTxt} (Confiança: ${confTxt}%)`,
          'success'
        );

        // Armazena token e dados do usuário na sessão
        sessionStorage.setItem('faca_token', dados.token);
        sessionStorage.setItem('faca_usuario', JSON.stringify(dados.usuario));

        setTimeout(() => {
          btnStartScan.disabled = false;
          btnScanLabel.textContent = 'ESCANEAR NOVAMENTE';
        }, 3000);

      } else if (resposta.status === 400) {
        // --- ERRO DE ENTRADA / CAPTURA: HTTP 400 (Não desconta tentativa) ---
        const codigo = dados.erro?.codigo || 'CAPTURE_ERROR';
        const mensagem = dados.erro?.mensagem || 'Falha na captura biométrica.';

        scanner.setErrorState(codigo, 'REPOSICIONE O ROSTO');
        showFeedback(bioFeedback, `⚠️ ${mensagem}`, 'info');

        btnStartScan.disabled = false;
        btnScanLabel.textContent = 'ESCANEAR NOVAMENTE';

      } else if (resposta.status === 401) {
        // --- FALHA DE AUTENTICAÇÃO: HTTP 401 (Senha incorreta ou Rosto Divergente) ---
        const tentativasRestantes = dados.tentativas_restantes !== undefined ? dados.tentativas_restantes : '?';
        const mensagem = dados.erro?.mensagem || 'Acesso Negado.';

        scanner.setErrorState('ACESSO NEGADO', `TENTATIVAS: ${tentativasRestantes}`);
        showFeedback(bioFeedback, `❌ ${mensagem} [Tentativas restantes: ${tentativasRestantes}]`, 'error');

        btnStartScan.disabled = false;
        btnScanLabel.textContent = 'TENTAR NOVAMENTE';

      } else if (resposta.status === 403) {
        // --- BLOQUEIO DE SEGURANÇA: HTTP 403 (5 falhas consecutivas) ---
        const mensagem = dados.erro?.mensagem || 'Terminal bloqueado por suspeita de ameaça.';

        scanner.setErrorState('TERMINAL BLOQUEADO', 'CONTA BLOQUEADA');
        showFeedback(bioFeedback, `🚨 ${mensagem}`, 'error');

        btnStartScan.disabled = true;
        btnScanLabel.textContent = 'ACESSO BLOQUEADO';

      } else {
        // --- OUTROS ERROS (500, 503) ---
        const mensagem = dados.erro?.mensagem || 'Erro interno no motor biométrico.';
        scanner.setErrorState('ERRO INTERNO', 'MOTOR BIOMÉTRICO');
        showFeedback(bioFeedback, `❌ ${mensagem}`, 'error');

        btnStartScan.disabled = false;
        btnScanLabel.textContent = 'TENTAR NOVAMENTE';
      }

    } catch (erro) {
      console.error('Falha na comunicação com o backend:', erro);
      scanner.setErrorState('ERRO DE REDE', 'OFFLINE');
      showFeedback(bioFeedback, '❌ Falha de comunicação com o servidor F.A.C.A. Verifique se o backend está online.', 'error');
      btnStartScan.disabled = false;
      btnScanLabel.textContent = 'TENTAR NOVAMENTE';
    }
  });

  // Alternar Câmera Real
  btnToggleCam.addEventListener('click', async () => {
    if (!scanner) return;
    clearFeedback(bioFeedback);
    const active = await scanner.toggleWebcam();
    btnToggleCam.textContent = active ? 'Usar Malha Holográfica' : 'Ativar Câmera Real';

    if (active) {
      showFeedback(bioFeedback, 'Câmera ativada. Posicione seu rosto no centro do enquadramento.', 'info');
    } else {
      scanner.resetState();
      showFeedback(bioFeedback, 'Modo holográfico ativo. Ative a câmera real para validação das 5 fases.', 'info');
    }
  });

  // Link Esqueceu sua senha
  forgotPwdLink.addEventListener('click', (e) => {
    e.preventDefault();
    showFeedback(loginFeedback, 'Solicitação enviada ao oficial de segurança do Ministério.', 'info');
  });

  // Helpers de Feedback
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
