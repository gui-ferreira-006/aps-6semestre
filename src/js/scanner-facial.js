/**
 * F.A.C.A - Biometric Holographic Face Scanner
 * Renderiza a malha facial poligonal 3D / cybernetic point cloud
 * idêntica à referência visual com animação e suporte a webcam real.
 */

class FaceScanner {
  constructor(canvasId, videoId) {
    this.canvas = document.getElementById(canvasId);
    this.video = document.getElementById(videoId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.isCameraActive = false;
    this.stream = null;
    this.isScanning = false;
    this.scanProgress = 0;
    this.laserEl = document.getElementById('scan-laser');
    this.progressBar = document.getElementById('scan-progress-bar');
    this.progressBox = document.getElementById('scan-progress-box');
    this.hudStatus = document.getElementById('hud-status-text');
    this.hudMetrics = document.getElementById('hud-metrics-text');

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
  }

  // Iniciar sequência biométrica
  startScanning(onComplete) {
    if (this.isScanning) return;
    this.isScanning = true;
    this.scanProgress = 0;

    if (this.laserEl) this.laserEl.classList.add('scanning');
    if (this.progressBox) this.progressBox.classList.add('active');
    if (this.hudStatus) this.hudStatus.textContent = 'ANALISANDO BIOMETRIA...';

    const duration = 2800; // 2.8 segundos de análise
    const startTime = performance.now();

    const scanInterval = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(100, Math.floor((elapsed / duration) * 100));
      this.scanProgress = progress;

      if (this.progressBar) this.progressBar.style.width = `${progress}%`;
      if (this.hudMetrics) this.hudMetrics.textContent = `BIOMETRIA ${progress}%`;

      if (elapsed < duration) {
        requestAnimationFrame(scanInterval);
      } else {
        this.isScanning = false;
        if (this.laserEl) this.laserEl.classList.remove('scanning');
        if (this.hudStatus) {
          this.hudStatus.textContent = 'ACESSO AUTORIZADO';
          this.hudStatus.style.color = '#2ed573';
        }
        if (onComplete) onComplete();
      }
    };

    requestAnimationFrame(scanInterval);
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

    // Movimento oscilatório sutil de rotação simulando holograma 3D
    this.rotationAngle += 0.012;
    this.pulse += 0.04;
    const rotY = Math.sin(this.rotationAngle) * 0.18; // oscilação suave no eixo Y
    const scale = Math.min(w, h) * 0.42;
    const cx = w / 2;
    const cy = h / 2 - 2;

    // Projetar pontos 3D para 2D
    const projected = this.points.map((pt) => {
      // Rotação em Y
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const xRot = pt.x * cosY + pt.z * sinY;
      const zRot = -pt.x * sinY + pt.z * cosY;

      // Projeção perspectiva
      const fov = 2.4;
      const distance = fov / (fov + zRot * 0.35);

      return {
        x: cx + xRot * scale * distance,
        y: cy + pt.y * scale * distance,
        z: zRot,
        isPupil: pt.isPupil
      };
    });

    // 1. Desenhar Linhas da Malha Facial (Wireframe)
    ctx.lineWidth = 1;
    for (let i = 0; i < this.edges.length; i++) {
      const [i1, i2] = this.edges[i];
      const p1 = projected[i1];
      const p2 = projected[i2];

      const avgZ = (p1.z + p2.z) / 2;
      const alpha = Math.max(0.12, Math.min(0.7, 0.4 + avgZ * 0.25));

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);

      if (this.isScanning) {
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
      
      const pointSize = p.isPupil ? 3.5 : 2;
      ctx.arc(p.x, p.y, pointSize, 0, Math.PI * 2);

      if (p.isPupil || this.isScanning) {
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
    }

    // 3. Linha dos Olhos / Mira Biométrica Vermelha (Idêntica à foto)
    const eyeL = projected[27];
    const eyeR = projected[32];
    if (eyeL && eyeR) {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(255, 35, 55, 0.75)';
      ctx.lineWidth = 1.2;
      ctx.setLineDash([4, 4]);
      ctx.moveTo(eyeL.x - 28, eyeL.y);
      ctx.lineTo(eyeR.x + 28, eyeR.y);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }
}

window.FaceScanner = FaceScanner;
