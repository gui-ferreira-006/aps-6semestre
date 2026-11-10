/**
 * F.A.C.A - Frente de Autenticação e Controle de Acesso
 * Lógica Principal da Interface de Login:
 * 1. Etapa de Login (CPF/Matrícula e Senha)
 * 2. Acesso Exclusivo ADM Geral (T.I.) — entra sem passar pelo reconhecimento facial
 * 3. Transição para Reconhecimento Facial (Biometria Real com PIVC) para os demais usuários
 * 4. Integração com API RESTful FastAPI + MySQL (/autenticar)
 * 5. Validação rigorosa de dados pessoais + facial no banco de dados e controle de bloqueio
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
  // 1. Máscara de CPF (preserva códigos alfanuméricos de T.I. como MMA-TI-000)
  // -------------------------------------------------------------------------
  if (cpfInput) {
    cpfInput.addEventListener('input', (e) => {
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

  // -------------------------------------------------------------------------
  // 2. Alternar Visibilidade da Senha
  // -------------------------------------------------------------------------
  let isPwdVisible = false;
  if (btnTogglePwd && passwordInput && eyeIcon) {
    btnTogglePwd.addEventListener('click', () => {
      isPwdVisible = !isPwdVisible;
      passwordInput.type = isPwdVisible ? 'text' : 'password';

      if (isPwdVisible) {
        eyeIcon.innerHTML = `
          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
          <line x1="1" y1="1" x2="23" y2="23"></line>
        `;
      } else {
        eyeIcon.innerHTML = `
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        `;
      }
    });
  }

  // -------------------------------------------------------------------------
  // 3. Submissão do Formulário de Login:
  //    - Verifica primeiro se é o Usuário Administrador Geral (T.I.) -> Entra direto sem facial!
  //    - Caso contrário -> Exige CPF de 11 dígitos e avança para validação de dados + facial no banco
  // -------------------------------------------------------------------------
  if (formLogin) {
    formLogin.addEventListener('submit', async (e) => {
      e.preventDefault();

      const cpfVal = cpfInput.value.trim();
      const pwdVal = passwordInput.value.trim();

      if (!cpfVal || !pwdVal) {
        showFeedback(loginFeedback, 'Informe seu CPF e senha para continuar.', 'error');
        return;
      }

      // 3.1. Verifica se é o Usuário Administrador Geral (Equipe de T.I.)
      if (window.ServicoAPI && window.ServicoAPI.ehAdmGeralTI(cpfVal, pwdVal)) {
        showFeedback(
          loginFeedback,
          'Credenciais de Administrador Geral (T.I.) confirmadas. Acesso liberado sem reconhecimento facial...',
          'success'
        );

        const resAdm = await window.ServicoAPI.autenticarAdmGeralTI(cpfVal, pwdVal);
        if (resAdm && resAdm.sucesso) {
          setTimeout(() => {
            clearFeedback(loginFeedback);
            if (typeof window.abrirDashboardRole === 'function') {
              window.abrirDashboardRole(3, 'historico');
            }
          }, 550);
          return;
        }
      }

      // 3.2. Para os demais usuários, valida se informou um CPF de 11 dígitos antes de abrir o scanner facial
      const digitosCpf = cpfVal.replace(/\D/g, '');
      if (digitosCpf.length !== 11) {
        showFeedback(
          loginFeedback,
          'Acesso Negado: Informe um CPF válido de 11 dígitos cadastrado no sistema (ou credenciais válidas de T.I.).',
          'error'
        );
        return;
      }

      // Se tentou usar o CPF do ADM T.I. (000.000.000-00) com senha incorreta, nega imediatamente
      if (digitosCpf === (window.CONFIGURACAO_BANCO?.ADM_GERAL_TI?.CPF || '00000000000')) {
        showFeedback(
          loginFeedback,
          'Acesso Negado: Senha incorreta para o usuário Administrador Geral (T.I.).',
          'error'
        );
        return;
      }

      currentCpf = cpfVal;
      currentPassword = pwdVal;

      showFeedback(
        loginFeedback,
        'Credenciais recebidas. Iniciando verificação obrigatória de biometria facial no banco...',
        'info'
      );

      setTimeout(async () => {
        clearFeedback(loginFeedback);
        transitionToStep('biometrics');

        // Tenta iniciar a webcam real automaticamente na transição
        if (scanner && !scanner.isCameraActive) {
          const camAtiva = await scanner.startWebcam();
          if (camAtiva) {
            btnToggleCam.textContent = 'Usar Malha Holográfica';
            showFeedback(
              bioFeedback,
              '⚠️ Aproxime seu rosto da câmera e mantenha-o dentro da REGIÃO OVAL para o sistema validar melhor. Em seguida, clique em "INICIAR RECONHECIMENTO".',
              'info'
            );
          } else {
            btnToggleCam.textContent = 'Ativar Câmera Real';
            showFeedback(
              bioFeedback,
              'Câmera real desativada. Clique em "Ativar Câmera Real" abaixo, aproxime seu rosto na região oval e inicie a validação.',
              'info'
            );
          }
        }
      }, 350);
    });
  }

  // -------------------------------------------------------------------------
  // 4. Transição Suave entre Etapas
  // -------------------------------------------------------------------------
  function transitionToStep(step) {
    if (!stepLogin || !stepBiometrics) return;
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

  // Expor reset da tela de login para uso no Logout
  window.resetarFormularioLogin = function () {
    currentCpf = '';
    currentPassword = '';
    if (formLogin) formLogin.reset();
    clearFeedback(loginFeedback);
    clearFeedback(bioFeedback);
    if (scanner) {
      scanner.resetState();
      if (scanner.isCameraActive) {
        scanner.stopWebcam();
      }
    }
    if (btnToggleCam) btnToggleCam.textContent = 'Ativar Câmera Real';
    if (btnStartScan) btnStartScan.disabled = false;
    if (btnScanLabel) btnScanLabel.textContent = 'INICIAR RECONHECIMENTO';
    transitionToStep('login');
  };

  // Voltar para a Etapa 1
  if (btnBackLogin) {
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
  }

  // -------------------------------------------------------------------------
  // 5. Interação de Reconhecimento Facial (Biometria Real via API Python + MySQL)
  // -------------------------------------------------------------------------
  if (btnStartScan) {
    btnStartScan.addEventListener('click', async () => {
      if (!scanner || scanner.isScanning) return;

      if (!scanner.isCameraActive) {
        showFeedback(
          bioFeedback,
          '⚠️ A câmera real não está ativa! Clique em "Ativar Câmera Real" abaixo, aproxime seu rosto na região oval e inicie a validação.',
          'error'
        );
        return;
      }

      // Valida se há presença/iluminação adequada dentro da região oval antes de enviar
      if (typeof scanner.validarPresencaNaRegiaoOval === 'function') {
        const checagemOval = scanner.validarPresencaNaRegiaoOval();
        if (!checagemOval.ok) {
          scanner.setErrorState('ENQUADRE NA OVAL', 'APROXIME O ROSTO');
          showFeedback(bioFeedback, `⚠️ ${checagemOval.motivo}`, 'info');
          return;
        }
      }

      btnStartScan.disabled = true;
      btnScanLabel.textContent = 'VALIDANDO ROSTO NA OVAL...';
      clearFeedback(bioFeedback);
      scanner.setScanningState(true, 'VALIDANDO ROSTO NA REGIÃO OVAL...');

      // 1. Captura o quadro real da webcam limitado estritamente ao rosto na região oval em Base64
      const frameBase64 = scanner.captureFrameBase64();

      if (!frameBase64) {
        scanner.setErrorState('ERRO DE CAPTURA', 'FRAME NULO');
        showFeedback(bioFeedback, 'Não foi possível capturar o rosto na região oval. Verifique se a câmera está conectada.', 'error');
        btnStartScan.disabled = false;
        btnScanLabel.textContent = 'TENTAR NOVAMENTE';
        return;
      }

      // 2. Valida CPF, Senha e Biometria Facial contra o banco MySQL via ServicoAPI
      try {
        const dados = await window.ServicoAPI.validarBiometriaFacial(currentCpf, currentPassword, frameBase64);

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
          `✅ ACESSO LIBERADO: Nível ${dados.usuario.nivel_acesso} — ${dados.usuario.nome} (${dados.usuario.cargo}). Distância Euclidiana: ${distTxt} (Confiança: ${confTxt}%)`,
          'success'
        );

        setTimeout(() => {
          const nivel = Number(dados.usuario.nivel_acesso) || 1;
          if (scanner && scanner.isCameraActive) {
            scanner.stopWebcam();
            btnToggleCam.textContent = 'Ativar Câmera Real';
          }
          if (typeof window.abrirDashboardRole === 'function') {
            window.abrirDashboardRole(nivel);
          }
        }, 1200);

      } catch (erro) {
        const status = erro?.status || 500;
        const codigo = erro?.erro?.codigo || 'AUTH_ERROR';
        const mensagem = erro?.erro?.mensagem || 'Acesso Negado: usuário não cadastrado ou biometria facial não reconhecida.';

        if (status === 400) {
          scanner.setErrorState(codigo, 'APROXIME NA REGIÃO OVAL');
          showFeedback(
            bioFeedback,
            `⚠️ ${mensagem} Aproxime seu rosto da câmera e mantenha-o centralizado dentro da região oval para o sistema validar melhor.`,
            'info'
          );
          btnStartScan.disabled = false;
          btnScanLabel.textContent = 'ESCANEAR NOVAMENTE';
        } else if (status === 401) {
          const tentativasRestantes = erro.tentativas_restantes !== undefined ? erro.tentativas_restantes : '?';
          scanner.setErrorState('ACESSO NEGADO', `TENTATIVAS: ${tentativasRestantes}`);
          showFeedback(
            bioFeedback,
            `❌ ${mensagem} Aproxime o rosto na região oval para melhor leitura [Tentativas restantes: ${tentativasRestantes}]`,
            'error'
          );
          btnStartScan.disabled = false;
          btnScanLabel.textContent = 'TENTAR NOVAMENTE';
        } else if (status === 403) {
          scanner.setErrorState('TERMINAL BLOQUEADO', 'CONTA BLOQUEADA');
          showFeedback(bioFeedback, `🚨 ${mensagem}`, 'error');
          btnStartScan.disabled = true;
          btnScanLabel.textContent = 'ACESSO BLOQUEADO';
        } else {
          scanner.setErrorState('ERRO DE COMUNICAÇÃO', 'SERVIDOR / BANCO');
          showFeedback(
            bioFeedback,
            `❌ ${erro?.erro?.mensagem || 'Falha de comunicação com o servidor F.A.C.A. Verifique se o backend e o banco estão online.'}`,
            'error'
          );
          btnStartScan.disabled = false;
          btnScanLabel.textContent = 'TENTAR NOVAMENTE';
        }
      }
    });
  }

  // Alternar Câmera Real
  if (btnToggleCam) {
    btnToggleCam.addEventListener('click', async () => {
      if (!scanner) return;
      clearFeedback(bioFeedback);
      const active = await scanner.toggleWebcam();
      btnToggleCam.textContent = active ? 'Usar Malha Holográfica' : 'Ativar Câmera Real';

      if (active) {
        showFeedback(
          bioFeedback,
          '⚠️ Câmera ativada. Aproxime seu rosto e mantenha-o dentro da REGIÃO OVAL para o sistema validar melhor.',
          'info'
        );
      } else {
        scanner.resetState();
        showFeedback(bioFeedback, 'Modo holográfico ativo. Ative a câmera real e posicione o rosto na região oval para validação.', 'info');
      }
    });
  }

  // Link Esqueceu sua senha
  if (forgotPwdLink) {
    forgotPwdLink.addEventListener('click', (e) => {
      e.preventDefault();
      showFeedback(
        loginFeedback,
        'Contate a equipe de T.I. (Administrador Geral) para redefinição de credenciais ou desbloqueio de conta.',
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
