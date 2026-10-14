/**
 * F.A.C.A - Neural Constellation / Plexus Canvas Background
 * Gera o efeito de rede de nós e conexões cibernéticas avermelhadas idêntico à imagem.
 */

(function () {
  const canvas = document.getElementById('bg-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  let mouse = {
    x: width / 2,
    y: height / 2,
    radius: 140
  };

  const PARTICLE_COUNT = Math.min(Math.floor((width * height) / 14000), 75);
  const MAX_DISTANCE = 150;
  const particles = [];

  class Particle {
    constructor() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.vx = (Math.random() - 0.5) * 0.45;
      this.vy = (Math.random() - 0.5) * 0.45;
      this.baseRadius = Math.random() * 1.8 + 1;
      this.radius = this.baseRadius;
      
      // Variações de cor vermelha e carmim cibernético
      const isRed = Math.random() > 0.45;
      this.color = isRed
        ? `rgba(${200 + Math.floor(Math.random() * 55)}, ${10 + Math.floor(Math.random() * 30)}, ${20 + Math.floor(Math.random() * 30)}, `
        : `rgba(${120 + Math.floor(Math.random() * 40)}, ${130 + Math.floor(Math.random() * 30)}, ${150 + Math.floor(Math.random() * 40)}, `;
      this.alpha = Math.random() * 0.6 + 0.3;
      this.pulseSpeed = Math.random() * 0.02 + 0.01;
      this.pulseAngle = Math.random() * Math.PI * 2;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;

      if (this.x < 0 || this.x > width) this.vx *= -1;
      if (this.y < 0 || this.y > height) this.vy *= -1;

      // Pulso sutil no tamanho do nó
      this.pulseAngle += this.pulseSpeed;
      this.radius = this.baseRadius + Math.sin(this.pulseAngle) * 0.5;

      // Interação sutil com o cursor
      const dx = mouse.x - this.x;
      const dy = mouse.y - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < mouse.radius) {
        const force = (mouse.radius - dist) / mouse.radius;
        this.x -= (dx / dist) * force * 1.2;
        this.y -= (dy / dist) * force * 1.2;
      }
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, Math.max(0.8, this.radius), 0, Math.PI * 2);
      ctx.fillStyle = this.color + this.alpha + ')';
      ctx.shadowBlur = 8;
      ctx.shadowColor = 'rgba(230, 20, 40, 0.6)';
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  function init() {
    particles.length = 0;
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push(new Particle());
    }
  }

  function connect() {
    for (let a = 0; a < particles.length; a++) {
      for (let b = a + 1; b < particles.length; b++) {
        const dx = particles[a].x - particles[b].x;
        const dy = particles[a].y - particles[b].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < MAX_DISTANCE) {
          const alpha = (1 - dist / MAX_DISTANCE) * 0.28;
          ctx.beginPath();
          ctx.strokeStyle = `rgba(180, 25, 40, ${alpha})`;
          ctx.lineWidth = 0.9;
          ctx.moveTo(particles[a].x, particles[a].y);
          ctx.lineTo(particles[b].x, particles[b].y);
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      particles[i].update();
      particles[i].draw();
    }
    connect();

    requestAnimationFrame(animate);
  }

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    init();
  });

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  init();
  animate();
})();
