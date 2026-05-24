<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppIcon from '@/components/ui/AppIcon.vue'

const router = useRouter()
const auth = useAuthStore()

const mode = ref('login') // 'login' | 'signup'
const loading = ref(false)
const error = ref('')

const form = reactive({ name: '', email: '', password: '', confirm: '' })

async function submit() {
  error.value = ''
  if (mode.value === 'signup') {
    if (!form.name.trim()) { error.value = 'El nombre es requerido'; return }
    if (form.password !== form.confirm) { error.value = 'Las contraseñas no coinciden'; return }
    if (form.password.length < 6) { error.value = 'La contraseña debe tener al menos 6 caracteres'; return }
  }
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(form.email, form.password)
    } else {
      await auth.signup(form.name, form.email, form.password)
    }
    router.push('/inicio')
  } catch (e) {
    error.value = friendlyError(e.code || e.message)
  } finally {
    loading.value = false
  }
}

function friendlyError(code) {
  const map = {
    'auth/wrong-password': 'Contraseña incorrecta',
    'auth/user-not-found': 'Usuario no encontrado',
    'auth/email-already-in-use': 'El correo ya está registrado',
    'auth/invalid-email': 'Correo inválido',
    'auth/too-many-requests': 'Demasiados intentos. Intenta más tarde.'
  }
  return map[code] || 'Error al autenticar. Verifica tus credenciales.'
}
</script>

<template>
  <div class="login-root">
    <!-- Left: Marketing -->
    <div class="login-left dot-grid">
      <div class="login-left-inner">
        <div class="login-logo">
          <div class="logo-mark" style="width:36px;height:36px;font-size:15px;">CF</div>
          <div>
            <div class="logo-text" style="font-size:16px;">COSFI</div>
            <div class="logo-sub">Auditoría TI · IA · ASFI</div>
          </div>
        </div>

        <div class="login-stat">
          <div class="stat-num">97<span>%</span></div>
          <div class="stat-label">cobertura normativa automática</div>
        </div>

        <div class="converge-diagram">
          <div class="conv-center">
            <div class="conv-dot" />
            <span>Hallazgo</span>
          </div>
          <div class="conv-arms">
            <div class="conv-arm arm-cobit">
              <span class="conv-tag cobit-tag">COBIT 2019</span>
              <div class="conv-line" />
            </div>
            <div class="conv-arm arm-coso">
              <span class="conv-tag coso-tag">COSO 2013</span>
              <div class="conv-line" />
            </div>
            <div class="conv-arm arm-rgsi">
              <span class="conv-tag rgsi-tag">RGSI · ASFI</span>
              <div class="conv-line" />
            </div>
          </div>
        </div>

        <p class="login-desc">
          Cruza automáticamente tres marcos normativos y genera<br/>
          matrices de hallazgos consolidadas listas para presentación.
        </p>
      </div>
    </div>

    <!-- Right: Form -->
    <div class="login-right">
      <div class="login-form-wrap">
        <div class="login-form-header">
          <h1>{{ mode === 'login' ? 'Iniciar sesión' : 'Crear cuenta' }}</h1>
          <p class="text-muted" style="font-size:12px;margin-top:4px;">
            {{ mode === 'login' ? 'Accede a tu espacio de trabajo' : 'Crea tu cuenta personal' }}
          </p>
        </div>

        <form @submit.prevent="submit" class="login-form">
          <div v-if="mode === 'signup'" class="form-group">
            <label class="form-label">Nombre completo</label>
            <input v-model="form.name" class="form-input" type="text" placeholder="Ej. Ana Mamani" autocomplete="name" required />
          </div>

          <div class="form-group">
            <label class="form-label">Correo electrónico</label>
            <input v-model="form.email" class="form-input" type="email" placeholder="correo@entidad.bo" autocomplete="email" required />
          </div>

          <div class="form-group">
            <label class="form-label">Contraseña</label>
            <input v-model="form.password" class="form-input" type="password" placeholder="••••••••" autocomplete="current-password" required />
          </div>

          <div v-if="mode === 'signup'" class="form-group">
            <label class="form-label">Confirmar contraseña</label>
            <input v-model="form.confirm" class="form-input" type="password" placeholder="••••••••" autocomplete="new-password" required />
          </div>

          <div v-if="error" class="login-error">
            <AppIcon name="alert-triangle" :size="13" />
            {{ error }}
          </div>

          <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:11px;" :disabled="loading">
            <div v-if="loading" class="spinner" style="border-color:rgba(0,0,0,0.2);border-top-color:#000;" />
            {{ mode === 'login' ? 'Ingresar' : 'Crear cuenta' }}
          </button>
        </form>

        <div class="login-toggle">
          <span class="text-muted">{{ mode === 'login' ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?' }}</span>
          <button class="toggle-link" @click="mode = mode === 'login' ? 'signup' : 'login'; error = ''">
            {{ mode === 'login' ? 'Crear cuenta' : 'Iniciar sesión' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-root {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  overflow: hidden;
}

.login-left {
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-left::before {
  content: '';
  position: absolute;
  bottom: -200px;
  left: -200px;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(34,211,238,0.06) 0%, transparent 70%);
  pointer-events: none;
}

.login-left-inner {
  padding: 48px;
  max-width: 440px;
  width: 100%;
}

.login-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 56px;
}

.login-stat {
  margin-bottom: 36px;
}

.stat-num {
  font-family: var(--mono);
  font-size: 72px;
  font-weight: 700;
  color: var(--accent);
  line-height: 1;
  letter-spacing: -3px;
  margin-bottom: 6px;
}

.stat-num span { font-size: 40px; color: var(--text-2); }

.stat-label {
  font-size: 13px;
  color: var(--text-2);
  font-family: var(--mono);
  letter-spacing: 0.3px;
}

/* Convergence diagram */
.converge-diagram {
  position: relative;
  height: 120px;
  margin-bottom: 32px;
  display: flex;
  align-items: center;
}

.conv-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
}

.conv-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 12px rgba(34,211,238,0.6);
  animation: pulse 1.8s ease-in-out infinite;
}

.conv-center span {
  font-family: var(--mono);
  font-size: 9px;
  color: var(--accent);
  letter-spacing: 0.5px;
}

.conv-arms {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.conv-arm {
  display: flex;
  align-items: center;
  gap: 8px;
}

.conv-tag {
  font-family: var(--mono);
  font-size: 9px;
  font-weight: 700;
  padding: 3px 7px;
  border-radius: 2px;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.cobit-tag { background: rgba(167,139,250,0.12); color: #a78bfa; border: 1px solid rgba(167,139,250,0.25); }
.coso-tag  { background: rgba(251,146,60,0.12);  color: #fb923c; border: 1px solid rgba(251,146,60,0.25); }
.rgsi-tag  { background: var(--accent-dim);       color: var(--accent); border: 1px solid var(--border-accent); }

.conv-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(255,255,255,0.08), rgba(34,211,238,0.3));
}

.login-desc {
  font-size: 12px;
  color: var(--text-2);
  line-height: 1.7;
}

/* Right panel */
.login-right {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: 48px;
}

.login-form-wrap {
  width: 100%;
  max-width: 360px;
}

.login-form-header {
  margin-bottom: 28px;
}

.login-form-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
  font-family: var(--mono);
}

.login-form { margin-bottom: 20px; }

.login-error {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(239,68,68,0.08);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: 3px;
  padding: 9px 12px;
  font-size: 12px;
  color: var(--risk-x);
  margin-bottom: 14px;
}

.login-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  margin-top: 16px;
}

.toggle-link {
  background: none;
  border: none;
  color: var(--accent);
  cursor: pointer;
  font-size: 12px;
  font-family: var(--sans);
  text-decoration: underline;
  text-underline-offset: 2px;
}

@media (max-width: 768px) {
  .login-root { grid-template-columns: 1fr; }
  .login-left { display: none; }
}
</style>
