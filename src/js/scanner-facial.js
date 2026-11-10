/**
 * F.A.C.A - Biometric Holographic Face Scanner
 * Renderiza a malha facial poligonal 3D / cybernetic point cloud
 * com máscara e guia de enquadramento na REGIÃO OVAL central.
 * Limita a captura de vídeo estritamente ao rosto posicionado na região oval
 * tanto no cadastro de vetores 128D no banco quanto na liberação de acesso.
 */

class FaceScanner {
  constructor(canvasId, videoId, hudIds = {}) {
    this.canvas = document.getElementById(canvasId);
    this.video = document.getElementById(videoId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.isCameraActive = false;
    this.stream = null;
    this.isScanning = false;
    this.scanProgress = 0;
    this.laserEl = document.getElementById(hudIds.laserId || 'scan-laser');
    this.progressBar = document.getElementById(hudIds.progressBarId || 'scan-progress-bar');
    this.progressBox = document.getElementById(hudIds.progressBoxId || 'scan-progress-box');
    this.hudStatus = document.getElementById(hudIds.statusId || 'hud-status-text');
    this.hudMetrics = document.getElementById(hudIds.metricsId || 'hud-metrics-text');

    this.hudColor = null; // null | '#2ed573' (sucesso) | '#ff2a40' (erro/alerta)
    this.rotationAngle = 0;
    this.pulse = 0;
    this.points = [];
    this.edges = [];

    this.initFaceModel();
    this.bindResize();
    this.startRendering();
  }

  initFaceModel() {
    // Conjunto de vértices 3D normalizados simulando topologia facial realista
    // (x: -1 a 1, y: -1.2 a 1.2, z: profundidade)
    const rawPoints = [
      // Contorno do Crânio / Testa
      { x: 0.0, y: -0.95, z: 0.2 },
      { x: -0.3, y: -0.88, z: 0.1 },
      { x: 0.3, y: -0.88, z: 0.1 },
      { x: -0.55, y: -0.65, z: -0.1 },
      { x: 0.55, y: -0.65, z: -0.1 },
      { x: -0.7, y: -0.35, z: -0.3 },
      { x: 0.7, y: -0.35, z: -0.3 },

      // Têmporas e Maçãs do Rosto
      { x: -0.75, y: 0.0, z: -0.4 },
      { x: 0.75, y: 0.0, z: -0.4 },
      { x: -0.5, y: 0.15, z: 0.2 },
      { x: 0.5, y: 0.15, z: 0.2 },

      // Mandíbula e Queixo
      { x: -0.6, y: 0.45, z: -0.3 },
      { x: 0.6, y: 0.45, z: -0.3 },
      { x: -0.38, y: 0.75, z: -0.1 },
      { x: 0.38, y: 0.75, z: -0.1 },
      { x: -0.2, y: 0.95, z: 0.2 },
      { x: 0.2, y: 0.95, z: 0.2 },
      { x: 0.0, y: 1.05, z: 0.35 }, // Queixo central

      // Sobrancelhas e Testa Interna
      { x: -0.35, y: -0.45, z: 0.4 },
      { x: -0.15, y: -0.48, z: 0.48 },
      { x: 0.0, y: -0.46, z: 0.5 },
      { x: 0.15, y: -0.48, z: 0.48 },
      { x: 0.35, y: -0.45, z: 0.4 },

      // Olhos
      { x: -0.4, y: -0.25, z: 0.3 }, // Canto externo esquerdo
      { x: -0.25, y: -0.29, z: 0.35 }, // Cima
      { x: -0.12, y: -0.25, z: 0.36 }, // Canto interno
      { x: -0.25, y: -0.21, z: 0.33 }, // Baixo
      { x: -0.25, y: -0.25, z: 0.42, isPupil: true }, // Pupila esquerda

      { x: 0.4, y: -0.25, z: 0.3 }, // Canto externo direito
      { x: 0.25, y: -0.29, z: 0.35 },
      { x: 0.12, y: -0.25, z: 0.36 },
      { x: 0.25, y: -0.21, z: 0.33 },
      { x: 0.25, y: -0.25, z: 0.42, isPupil: true }, // Pupila direita

      // Nariz
      { x: 0.0, y: -0.25, z: 0.52 }, // Topo nasal
      { x: 0.0, y: 0.0, z: 0.68 }, // Ponte central do nariz
      { x: 0.0, y: 0.22, z: 0.8 }, // Ponta do nariz
      { x: -0.16, y: 0.22, z: 0.55 }, // Asa nasal esquerda
      { x: 0.16, y: 0.22, z: 0.55 }, // Asa nasal direita

      // Boca
      { x: -0.28, y: 0.48, z: 0.35 }, // Canto esquerdo
      { x: 0.0, y: 0.43, z: 0.5 }, // Lábio superior centro
      { x: 0.28, y: 0.48, z: 0.35 }, // Canto direito
      { x: 0.0, y: 0.58, z: 0.48 }, // Lábio inferior centro
      { x: 0.0, y: 0.72, z: 0.38 } // Sulco abaixo da boca
    ];

    // Criando conexões de malha poligonal (triângulos / arestas)
    const rawEdges = [
      // Contorno facial
      [0, 1], [1, 3], [3, 5], [5, 7], [7, 11], [11, 13], [13, 15], [15, 17],
      [0, 2], [2, 4], [4, 6], [6, 8], [8, 12], [12, 14], [14, 16], [16, 17],
      
      // Testa e sobrancelhas
      [0, 20], [1, 18], [2, 22], [18, 19], [19, 20], [20, 21], [21, 22],
      
      // Olho esquerdo
      [23, 24], [24, 25], [25, 26], [26, 23],
      [18, 24], [19, 25], [23, 7],
      
      // Olho direito
      [28, 29], [29, 30], [30, 31], [31, 28],
      [22, 29], [21, 30], [28, 8],

      // Nariz
      [20, 33], [25, 33], [30, 33],
      [33, 34], [34, 35],
      [34, 36], [34, 37],
      [35, 36], [35, 37],
      [36, 9], [37, 10],

      // Maçãs do rosto
      [26, 9], [31, 10], [9, 13], [10, 14],

      // Boca
      [35, 39], [36, 38], [37, 40],
      [38, 39], [39, 40], [40, 41], [41, 38],
      [41, 42], [42, 17], [38, 15], [40, 16]
    ];

    this.points = rawPoints;
    this.edges = rawEdges;
  }

  /**
   * Calcula a geometria da região oval central no visor (canvas).
   * Proporção vertical de rosto humano (idêntica à .oval-face-cutout do CSS:
   * altura = 76% do visor -> ry = 0.38 * h, largura = 0.76 * altura -> rx = ry * 0.76).
   */
  getOvalBounds(w, h) {
    const cx = w / 2;
    const cy = h / 2;
    const ry = Math.max(58, h * 0.38);
    const rx = Math.max(44, Math.min(w * 0.38, ry * 0.76));
    return { cx, cy, rx, ry };
  }

  getViewportElement() {
    return this.canvas ? this.canvas.parentElement : null;
  }

  updateOvalOverlayState(state = '') {
    const viewport = this.getViewportElement();
    if (!viewport) return;
    const overlay = viewport.querySelector('.oval-face-overlay');
    if (!overlay) return;
    overlay.classList.remove('oval-scanning', 'oval-success', 'oval-error', 'oval-cam-active');
    if (state) {
      overlay.classList.add(state);
    } else if (this.isCameraActive) {
      overlay.classList.add('oval-cam-active');
    }
  }

  showCapturedPreview(dataUrl) {
    const viewport = this.getViewportElement();
    if (!viewport) return;
    let img = viewport.querySelector('.oval-captured-preview');
    if (!img && dataUrl) {
      const cutout = viewport.querySelector('.oval-face-cutout');
      if (cutout) {
        img = document.createElement('img');
        img.className = 'oval-captured-preview';
        img.alt = 'Rosto capturado na região oval';
        cutout.appendChild(img);
      }
    }
    if (img) {
      if (dataUrl) {
        img.src = dataUrl;
        img.style.display = 'block';
      } else {
        img.removeAttribute('src');
        img.style.display = 'none';
      }
    }
  }

  bindResize() {
    const resize = () => {
      if (!this.canvas) return;
      const rect = this.canvas.parentElement.getBoundingClientRect();
      this.canvas.width = rect.width || 340;
      this.canvas.height = rect.height || 240;
    };
    window.addEventListener('resize', resize);
    resize();
  }

  // Ativar / Desativar Webcam Real
  async toggleWebcam() {
    if (this.isCameraActive) {
      this.stopWebcam();
      return false;
    } else {
      return await this.startWebcam();
    }
  }

  async startWebcam() {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Navegador não suporta acesso à câmera.');
      }
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
      });
      if (this.video) {
        this.video.srcObject = this.stream;
        this.video.style.display = 'block';
        this.isCameraActive = true;
        this.showCapturedPreview(null);
        this.updateOvalOverlayState('oval-cam-active');
        if (this.hudStatus) {
          this.hudStatus.textContent = 'APROXIME O ROSTO NA REGIÃO OVAL';
        }
        if (this.hudMetrics) {
          this.hudMetrics.textContent = 'ENQUADRE NA ÁREA OVAL';
        }
      }
      return true;
    } catch (err) {
      console.warn('Câmera indisponível ou permissão negada:', err);
      this.stopWebcam();
      return false;
    }
  }

  stopWebcam() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    if (this.video) {
      this.video.style.display = 'none';
      this.video.srcObject = null;
    }
    this.isCameraActive = false;
    this.showCapturedPreview(null);
    this.updateOvalOverlayState('');
  }

  /**
   * Verifica se há presença e iluminação/contraste adequados dentro da região oval
   * antes de enviar a captura para validação ou gravação dos vetores 128D.
   */
  validarPresencaNaRegiaoOval() {
    if (!this.video || !this.isCameraActive) {
      return { ok: false, motivo: 'A câmera não está ativa.' };
    }

    const video = this.video;
    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;
    if (vw === 0 || vh === 0) {
      return { ok: false, motivo: 'Aguarde o carregamento do vídeo da câmera.' };
    }

    // Amostra a região central onde fica a oval
    const sampleW = 64;
    const sampleH = 64;
    const probeCanvas = document.createElement('canvas');
    probeCanvas.width = sampleW;
    probeCanvas.height = sampleH;
    const probeCtx = probeCanvas.getContext('2d');
    if (!probeCtx) return { ok: true };

    const cropW = vw * 0.45;
    const cropH = vh * 0.65;
    const cropX = (vw - cropW) / 2;
    const cropY = (vh - cropH) / 2;

    probeCtx.drawImage(video, cropX, cropY, cropW, cropH, 0, 0, sampleW, sampleH);
    const imgData = probeCtx.getImageData(0, 0, sampleW, sampleH).data;

    let sumLum = 0;
    let sumSqLum = 0;
    let count = 0;

    for (let y = 0; y < sampleH; y++) {
      const ny = (y - sampleH / 2) / (sampleH / 2);
      for (let x = 0; x < sampleW; x++) {
        const nx = (x - sampleW / 2) / (sampleW / 2);
        if (nx * nx + ny * ny <= 1.0) {
          const idx = (y * sampleW + x) * 4;
          const lum = 0.299 * imgData[idx] + 0.587 * imgData[idx + 1] + 0.114 * imgData[idx + 2];
          sumLum += lum;
          sumSqLum += lum * lum;
          count++;
        }
      }
    }

    if (count === 0) return { ok: true };
    const mean = sumLum / count;
    const variance = Math.max(0, sumSqLum / count - mean * mean);
    const stdDev = Math.sqrt(variance);

    // Se a câmera estiver totalmente tapada/escura ou sem textura alguma (quadro vazio)
    if (mean < 12 || stdDev < 6) {
      return {
        ok: false,
        motivo: 'Rosto não identificado na região oval! Aproxime seu rosto da câmera, fique dentro do guia oval e garanta boa iluminação.'
      };
    }

    return { ok: true, luminancia: mean, contraste: stdDev };
  }

  /**
   * Captura o quadro atual da webcam limitando ESTRITAMENTE à região oval central do rosto.
   * Isola apenas o rosto posicionado dentro da região oval (descartando o fundo externo
   * e possíveis pessoas ao redor) para extrair/guardar os vetores 128D no banco de dados
   * e para liberar o acesso na autenticação.
   *
   * @returns {string|null} String Base64 da imagem JPEG limitada ao rosto na região oval.
   */
  captureFrameBase64() {
    if (!this.video || !this.isCameraActive) {
      console.warn('FaceScanner: Câmera não está ativa para captura de frame.');
      return null;
    }

    const video = this.video;
    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;

    if (vw === 0 || vh === 0) {
      console.warn('FaceScanner: Dimensões do vídeo ainda não carregadas.');
      return null;
    }

    // Mapeia a região oval exibida no visor (com object-fit: cover) para as coordenadas reais do vídeo
    const viewW = (this.canvas && this.canvas.width) ? this.canvas.width : 340;
    const viewH = (this.canvas && this.canvas.height) ? this.canvas.height : 240;
    const { rx: viewRx, ry: viewRy } = this.getOvalBounds(viewW, viewH);

    const coverScale = Math.max(viewW / vw, viewH / vh);
    const videoOvalRx = viewRx / coverScale;
    const videoOvalRy = viewRy / coverScale;

    // Margem de segurança (~18%) ao redor da elipse para preservar o contorno craniano exigido pelo detector HOG
    // enquanto elimina todo o restante do quadro externo à região oval.
    const marginFactor = 1.18;
    const cropHalfW = Math.min(vw / 2, Math.round(videoOvalRx * marginFactor));
    const cropHalfH = Math.min(vh / 2, Math.round(videoOvalRy * marginFactor));

    const centerX = vw / 2;
    const centerY = vh / 2;
    const sx = Math.max(0, Math.round(centerX - cropHalfW));
    const sy = Math.max(0, Math.round(centerY - cropHalfH));
    const sw = Math.min(vw - sx, cropHalfW * 2);
    const sh = Math.min(vh - sy, cropHalfH * 2);

    // Define resolução de saída padronizada para a ROI facial (alta nitidez para os 128 vetores)
    const outW = Math.max(320, sw);
    const outH = Math.max(380, Math.round(outW * (sh / Math.max(1, sw))));

    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = outW;
    tempCanvas.height = outH;

    const tempCtx = tempCanvas.getContext('2d');
    if (!tempCtx) return null;

    // Preenche o fundo externo com tom neutro escuro para isolar apenas a região oval
    tempCtx.fillStyle = '#181c24';
    tempCtx.fillRect(0, 0, outW, outH);

    // Aplica recorte elíptico correspondente à região oval onde o rosto está posicionado
    tempCtx.save();
    tempCtx.beginPath();
    tempCtx.ellipse(
      outW / 2,
      outH / 2,
      (outW / 2) * 0.96,
      (outH / 2) * 0.96,
      0,
      0,
      Math.PI * 2
    );
    tempCtx.closePath();
    tempCtx.clip();

    // Desenha somente o recorte central da região oval do rosto
    tempCtx.drawImage(video, sx, sy, sw, sh, 0, 0, outW, outH);
    tempCtx.restore();

    // Converte a região oval do rosto para Base64 JPEG com 92% de qualidade
    const dataUrl = tempCanvas.toDataURL('image/jpeg', 0.92);
    this.showCapturedPreview(dataUrl);
    return dataUrl;
  }

  // -------------------------------------------------------------------------
  // Métodos de Controle Visual do HUD e Estados de Resposta da API
  // -------------------------------------------------------------------------

  setScanningState(isScanning, label = 'ANALISANDO ROSTO NA REGIÃO OVAL...') {
    this.isScanning = isScanning;
    this.updateOvalOverlayState(isScanning ? 'oval-scanning' : '');
    if (isScanning) {
      this.hudColor = '#ff2a40';
      if (this.laserEl) this.laserEl.classList.add('scanning');
      if (this.progressBox) this.progressBox.classList.add('active');
      if (this.progressBar) {
        this.progressBar.style.width = '70%';
        this.progressBar.style.backgroundColor = '#ff2a40';
      }
      if (this.hudStatus) {
        this.hudStatus.textContent = label;
        this.hudStatus.style.color = '#ff4757';
      }
      if (this.hudMetrics) {
        this.hudMetrics.textContent = 'EXTRAINDO 128D (OVAL)...';
        this.hudMetrics.style.color = '#ff6b81';
      }
    } else {
      if (this.laserEl) this.laserEl.classList.remove('scanning');
      if (this.progressBox) this.progressBox.classList.remove('active');
    }
  }

  setSuccessState(mensagem = 'ACESSO AUTORIZADO', metrics = 'BIOMETRIA 100%') {
    this.isScanning = false;
    this.hudColor = '#2ed573';
    this.updateOvalOverlayState('oval-success');
    if (this.laserEl) this.laserEl.classList.remove('scanning');
    if (this.progressBox) this.progressBox.classList.add('active');
    if (this.progressBar) {
      this.progressBar.style.width = '100%';
      this.progressBar.style.backgroundColor = '#2ed573';
    }
    if (this.hudStatus) {
      this.hudStatus.textContent = mensagem;
      this.hudStatus.style.color = '#2ed573';
    }
    if (this.hudMetrics) {
      this.hudMetrics.textContent = metrics;
      this.hudMetrics.style.color = '#2ed573';
    }
  }

  setErrorState(mensagem = 'ACESSO NEGADO', metrics = 'APROXIME NA REGIÃO OVAL') {
    this.isScanning = false;
    this.hudColor = '#ff2a40';
    this.showCapturedPreview(null);
    this.updateOvalOverlayState('oval-error');
    if (this.laserEl) this.laserEl.classList.remove('scanning');
    if (this.progressBox) this.progressBox.classList.add('active');
    if (this.progressBar) {
      this.progressBar.style.width = '100%';
      this.progressBar.style.backgroundColor = '#ff2a40';
    }
    if (this.hudStatus) {
      this.hudStatus.textContent = mensagem;
      this.hudStatus.style.color = '#ff2a40';
    }
    if (this.hudMetrics) {
      this.hudMetrics.textContent = metrics;
      this.hudMetrics.style.color = '#ff2a40';
    }
  }

  resetState() {
    this.isScanning = false;
    this.hudColor = null;
    this.showCapturedPreview(null);
    this.updateOvalOverlayState('');
    if (this.laserEl) this.laserEl.classList.remove('scanning');
    if (this.progressBox) this.progressBox.classList.remove('active');
    if (this.progressBar) {
      this.progressBar.style.width = '0%';
      this.progressBar.style.backgroundColor = '#ff2a40';
    }
    if (this.hudStatus) {
      this.hudStatus.textContent = this.isCameraActive ? 'APROXIME O ROSTO NA REGIÃO OVAL' : 'SISTEMA PRONTO';
      this.hudStatus.style.color = '';
    }
    if (this.hudMetrics) {
      this.hudMetrics.textContent = this.isCameraActive ? 'ENQUADRE NA ÁREA OVAL' : 'BIOMETRIA 0%';
      this.hudMetrics.style.color = '';
    }
  }

  startRendering() {
    const render = () => {
      this.draw();
      requestAnimationFrame(render);
    };
    requestAnimationFrame(render);
  }

  draw() {
    if (!this.ctx || !this.canvas) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    ctx.clearRect(0, 0, w, h);

    // Geometria da Região Oval de Enquadramento Facial
    const { cx, cy, rx, ry } = this.getOvalBounds(w, h);

    // 0. Máscara escura fora da Região Oval (isola visualmente apenas a área oval do rosto)
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, w, h);
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = this.isCameraActive
      ? 'rgba(5, 7, 12, 0.78)'
      : 'rgba(5, 7, 12, 0.52)';
    ctx.fill('evenodd');
    ctx.restore();

    // Movimento oscilatório sutil de rotação simulando holograma 3D dentro da oval
    this.rotationAngle += 0.012;
    this.pulse += 0.04;
    const rotY = Math.sin(this.rotationAngle) * 0.18;
    const scale = Math.min(rx * 1.18, ry * 0.92);

    // Quando a câmera real está ligada, deixa a malha 3D mais suave para facilitar o posicionamento do rosto na oval
    const meshOpacityFactor = this.isCameraActive ? 0.35 : 1.0;

    // Projetar pontos 3D para 2D
    const projected = this.points.map((pt) => {
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const xRot = pt.x * cosY + pt.z * sinY;
      const zRot = -pt.x * sinY + pt.z * cosY;

      const fov = 2.4;
      const distance = fov / (fov + zRot * 0.35);

      return {
        x: cx + xRot * scale * distance,
        y: cy + pt.y * scale * distance,
        z: zRot,
        isPupil: pt.isPupil
      };
    });

    // Recorta a renderização da malha 3D estritamente para dentro da Região Oval
    ctx.save();
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.clip();

    // 1. Desenhar Linhas da Malha Facial (Wireframe)
    ctx.lineWidth = 1;
    for (let i = 0; i < this.edges.length; i++) {
      const [i1, i2] = this.edges[i];
      const p1 = projected[i1];
      const p2 = projected[i2];

      const avgZ = (p1.z + p2.z) / 2;
      const alpha = Math.max(0.12, Math.min(0.7, 0.4 + avgZ * 0.25)) * meshOpacityFactor;

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);

      if (this.hudColor === '#2ed573') {
        ctx.strokeStyle = `rgba(46, 213, 115, ${alpha * 1.2})`;
      } else if (this.isScanning || this.hudColor === '#ff2a40') {
        ctx.strokeStyle = `rgba(255, 30, 50, ${alpha * 1.3})`;
      } else {
        ctx.strokeStyle = `rgba(160, 190, 220, ${alpha * 0.65})`;
      }
      ctx.stroke();
    }

    // 2. Desenhar Vértices / Pontos Biométricos (Point Cloud)
    for (let i = 0; i < projected.length; i++) {
      const p = projected[i];
      ctx.beginPath();

      const pointSize = p.isPupil ? 3.2 : 1.8;
      ctx.arc(p.x, p.y, pointSize, 0, Math.PI * 2);

      ctx.globalAlpha = meshOpacityFactor;
      if (this.hudColor === '#2ed573') {
        ctx.fillStyle = '#2ed573';
        ctx.shadowBlur = 6;
        ctx.shadowColor = '#2ed573';
      } else if (p.isPupil || this.isScanning || this.hudColor === '#ff2a40') {
        ctx.fillStyle = '#ff2a40';
        ctx.shadowBlur = 6;
        ctx.shadowColor = '#ff2a40';
      } else {
        ctx.fillStyle = '#cfdaf0';
        ctx.shadowBlur = 3;
        ctx.shadowColor = '#80a0d0';
      }
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.globalAlpha = 1.0;
    }

    // 3. Linha dos Olhos / Mira Biométrica dentro da Oval
    const eyeL = projected[27];
    const eyeR = projected[32];
    if (eyeL && eyeR) {
      ctx.beginPath();
      ctx.strokeStyle = this.hudColor === '#2ed573'
        ? `rgba(46, 213, 115, ${0.85 * meshOpacityFactor})`
        : `rgba(255, 35, 55, ${0.75 * meshOpacityFactor})`;
      ctx.lineWidth = 1.2;
      ctx.setLineDash([4, 4]);
      ctx.moveTo(eyeL.x - 24, eyeL.y);
      ctx.lineTo(eyeR.x + 24, eyeR.y);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.restore();

    // 4. Desenhar a Moldura / Guia da Região Oval e Marcadores de Proximidade
    this.drawOvalFaceGuide(ctx, cx, cy, rx, ry);
  }

  drawOvalFaceGuide(ctx, cx, cy, rx, ry) {
    const pulseOffset = Math.sin(this.pulse) * 2.5;
    let borderColor = 'rgba(255, 42, 64, 0.88)';
    let glowColor = 'rgba(255, 42, 64, 0.45)';

    if (this.hudColor === '#2ed573') {
      borderColor = 'rgba(46, 213, 115, 0.95)';
      glowColor = 'rgba(46, 213, 115, 0.55)';
    } else if (this.isCameraActive && !this.isScanning && !this.hudColor) {
      borderColor = 'rgba(255, 165, 2, 0.92)';
      glowColor = 'rgba(255, 165, 2, 0.4)';
    }

    ctx.save();

    // Anel externo pontilhado pulsante (indicador de aproximação facial)
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx + 6 + pulseOffset * 0.5, ry + 6 + pulseOffset * 0.5, 0, 0, Math.PI * 2);
    ctx.strokeStyle = glowColor;
    ctx.lineWidth = 1.2;
    ctx.setLineDash([6, 6]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Contorno principal da Região Oval
    ctx.beginPath();
    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.strokeStyle = borderColor;
    ctx.lineWidth = 2.4;
    ctx.shadowBlur = 12;
    ctx.shadowColor = glowColor;
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Marcadores de alinhamento (Topo/Testa, Base/Queixo, Laterais/Têmporas)
    const tickLen = 8;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    // Topo
    ctx.moveTo(cx - tickLen, cy - ry);
    ctx.lineTo(cx + tickLen, cy - ry);
    // Base (Queixo)
    ctx.moveTo(cx - tickLen, cy + ry);
    ctx.lineTo(cx + tickLen, cy + ry);
    // Esquerda
    ctx.moveTo(cx - rx, cy - tickLen);
    ctx.lineTo(cx - rx, cy + tickLen);
    // Direita
    ctx.moveTo(cx + rx, cy - tickLen);
    ctx.lineTo(cx + rx, cy + tickLen);
    ctx.stroke();

    ctx.restore();
  }
}

window.FaceScanner = FaceScanner;
