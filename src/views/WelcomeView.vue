<template>
  <div class="welcome">
    <!-- Background -->
    <div class="bg-grid" aria-hidden="true"></div>
    <div class="bg-orb orb-1" aria-hidden="true"></div>
    <div class="bg-orb orb-2" aria-hidden="true"></div>
    <canvas ref="canvasRef" class="bg-canvas" aria-hidden="true"></canvas>

    <!-- Content -->
    <main class="content">
      <!-- Logo -->
      <div class="logo-block">
        <div class="logo-icon">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <path d="M14 2L24 7.5V20.5L14 26L4 20.5V7.5L14 2Z" stroke="#22d3ee" stroke-width="1.5" fill="none"/>
            <path d="M14 2L14 14M14 14L24 7.5M14 14L4 7.5M14 14L14 26M14 14L24 20.5M14 14L4 20.5" stroke="#22d3ee" stroke-width="0.75" stroke-opacity="0.5"/>
          </svg>
        </div>
        <span class="logo-name">COSFI</span>
      </div>

      <!-- Hero -->
      <div class="hero">
        <p class="hero-kicker">Plataforma de Auditoría con IA</p>
        <h1 class="hero-title">
          Semanas de auditoría<br>
          <span class="hero-accent">reducidas a minutos.</span>
        </h1>
        <p class="hero-desc">
          COSFI automatiza la revisión normativa con IA semántica avanzada —
          detecta brechas, genera hallazgos y evalúa cumplimiento de
          COSO, COBIT y RGSI-ASFI desde una sola plataforma.
        </p>
      </div>

      <!-- Stats -->
      <div class="stats">
        <div class="stat">
          <span class="stat-num">3</span>
          <span class="stat-label">Marcos regulatorios integrados</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat">
          <span class="stat-num">97%</span>
          <span class="stat-label">Cobertura normativa automática</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat">
          <span class="stat-num">∞</span>
          <span class="stat-label">Documentos analizables</span>
        </div>
      </div>

      <!-- Features -->
      <div class="features">
        <div class="feature-pill">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          Análisis IA semántico
        </div>
        <div class="feature-pill">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          Detección de brechas
        </div>
        <div class="feature-pill">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          Reportes automatizados
        </div>
        <div class="feature-pill">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 8v4l3 3"/>
          </svg>
          Chatbot inteligente
        </div>
      </div>

      <!-- CTA -->
      <div class="cta-block">
        <router-link to="/login" class="btn-cta">
          <span>Iniciar sesión</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </router-link>
      </div>
    </main>

    <!-- Bottom frameworks bar -->
    <footer class="frameworks-bar">
      <span class="fw-label">Marcos integrados</span>
      <span class="fw-sep">·</span>
      <span class="fw-item">COSO 2013</span>
      <span class="fw-sep">·</span>
      <span class="fw-item">COBIT 2019</span>
      <span class="fw-sep">·</span>
      <span class="fw-item">RGSI-ASFI</span>
      <span class="fw-sep">·</span>
      <span class="fw-item">Python · FastAPI · Vue.js · Firebase</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)
let animFrame = null
let cleanupFn = null

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  const resize = () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  const CYAN = '34, 211, 238'
  const nodes = Array.from({ length: 55 }, () => ({
    x: Math.random() * window.innerWidth,
    y: Math.random() * window.innerHeight,
    vx: (Math.random() - 0.5) * 0.35,
    vy: (Math.random() - 0.5) * 0.35,
    r: Math.random() * 1.5 + 0.5
  }))

  const draw = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    nodes.forEach(n => {
      n.x += n.vx
      n.y += n.vy
      if (n.x < 0 || n.x > canvas.width) n.vx *= -1
      if (n.y < 0 || n.y > canvas.height) n.vy *= -1
    })

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x
        const dy = nodes[i].y - nodes[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < 130) {
          ctx.beginPath()
          ctx.strokeStyle = `rgba(${CYAN}, ${(1 - dist / 130) * 0.12})`
          ctx.lineWidth = 0.5
          ctx.moveTo(nodes[i].x, nodes[i].y)
          ctx.lineTo(nodes[j].x, nodes[j].y)
          ctx.stroke()
        }
      }
    }

    nodes.forEach(n => {
      ctx.beginPath()
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${CYAN}, 0.35)`
      ctx.fill()
    })

    animFrame = requestAnimationFrame(draw)
  }
  draw()

  cleanupFn = () => {
    window.removeEventListener('resize', resize)
    cancelAnimationFrame(animFrame)
  }
})

onUnmounted(() => {
  cleanupFn?.()
})
</script>

<style scoped>
/* ── Base ─────────────────────────────────────────────── */
.welcome {
  position: relative;
  min-height: 100vh;
  background: #07070d;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-family: 'DM Sans', sans-serif;
  color: #e2e8f0;
}

/* ── Background layers ─────────────────────────────────── */
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(34, 211, 238, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(34, 211, 238, 0.035) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
}

.bg-canvas {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  pointer-events: none;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.08) 0%, transparent 70%);
  top: -150px;
  left: -150px;
  animation: drift 18s ease-in-out infinite alternate;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.07) 0%, transparent 70%);
  bottom: -100px;
  right: -100px;
  animation: drift 22s ease-in-out infinite alternate-reverse;
}

@keyframes drift {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(40px, 30px) scale(1.08); }
}

/* ── Content ───────────────────────────────────────────── */
.content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  padding: 2rem 1.5rem 6rem;
  max-width: 720px;
  width: 100%;
  text-align: center;
  animation: rise 0.9s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes rise {
  from { opacity: 0; transform: translateY(28px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Logo ──────────────────────────────────────────────── */
.logo-block {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  animation: rise 0.9s 0.05s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 10px;
  background: rgba(34, 211, 238, 0.06);
  box-shadow: 0 0 20px rgba(34, 211, 238, 0.12), inset 0 1px 0 rgba(255,255,255,0.06);
}

.logo-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: #f1f5f9;
}

.logo-badge {
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: #22d3ee;
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.25);
  border-radius: 4px;
  padding: 2px 6px;
  text-transform: uppercase;
  align-self: flex-start;
  margin-top: 2px;
}

/* ── Hero ──────────────────────────────────────────────── */
.hero {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  animation: rise 0.9s 0.12s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.hero-kicker {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #22d3ee;
  opacity: 0.85;
}

.hero-title {
  font-size: clamp(2.2rem, 5vw, 3.4rem);
  font-weight: 700;
  line-height: 1.15;
  color: #f8fafc;
  letter-spacing: -0.02em;
  margin: 0;
}

.hero-accent {
  background: linear-gradient(135deg, #22d3ee 0%, #6366f1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 1rem;
  line-height: 1.7;
  color: #94a3b8;
  max-width: 560px;
  margin: 0 auto;
}

/* ── Stats ─────────────────────────────────────────────── */
.stats {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1.25rem 2.5rem;
  background: rgba(13, 13, 24, 0.8);
  border: 1px solid rgba(34, 211, 238, 0.12);
  border-radius: 14px;
  backdrop-filter: blur(12px);
  animation: rise 0.9s 0.2s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
}

.stat-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.6rem;
  font-weight: 700;
  color: #22d3ee;
  line-height: 1;
}

.stat-label {
  font-size: 0.7rem;
  color: #64748b;
  text-align: center;
  max-width: 100px;
  line-height: 1.3;
}

.stat-divider {
  width: 1px;
  height: 36px;
  background: rgba(34, 211, 238, 0.12);
}

/* ── Features ──────────────────────────────────────────── */
.features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
  animation: rise 0.9s 0.28s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.feature-pill {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.85rem;
  font-size: 0.78rem;
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.03);
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}

.feature-pill:hover {
  color: #22d3ee;
  border-color: rgba(34, 211, 238, 0.3);
  background: rgba(34, 211, 238, 0.06);
}

/* ── CTA ───────────────────────────────────────────────── */
.cta-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.8rem;
  animation: rise 0.9s 0.36s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.btn-cta {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.85rem 2.2rem;
  background: #22d3ee;
  color: #07070d;
  font-size: 0.95rem;
  font-weight: 700;
  border-radius: 10px;
  text-decoration: none;
  letter-spacing: 0.01em;
  box-shadow: 0 0 30px rgba(34, 211, 238, 0.35), 0 4px 16px rgba(34, 211, 238, 0.2);
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s, background 0.2s;
  position: relative;
  overflow: hidden;
}

.btn-cta::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 60%);
  pointer-events: none;
}

.btn-cta:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 0 50px rgba(34, 211, 238, 0.5), 0 8px 24px rgba(34, 211, 238, 0.3);
  background: #38e4ff;
}

.btn-cta:active {
  transform: translateY(0) scale(0.99);
}

.cta-note {
  font-size: 0.72rem;
  color: #334155;
  letter-spacing: 0.03em;
}

/* ── Footer bar ────────────────────────────────────────── */
.frameworks-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  padding: 0.65rem 1rem;
  background: rgba(7, 7, 13, 0.85);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  font-size: 0.7rem;
  color: #334155;
  flex-wrap: wrap;
}

.fw-label {
  color: #475569;
  font-weight: 500;
}

.fw-item {
  color: #475569;
  transition: color 0.2s;
}

.fw-item:hover {
  color: #64748b;
}

.fw-sep {
  color: #1e293b;
}

/* ── Responsive ────────────────────────────────────────── */
@media (max-width: 600px) {
  .stats {
    flex-direction: column;
    gap: 1rem;
    padding: 1.25rem 2rem;
  }
  .stat-divider {
    width: 40px;
    height: 1px;
  }
  .hero-title {
    font-size: 2rem;
  }
}
</style>
