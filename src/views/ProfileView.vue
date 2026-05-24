<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/layout/AppShell.vue'
import AppIcon from '@/components/ui/AppIcon.vue'

const router = useRouter()
const auth = useAuthStore()

const editMode = ref(false)
const pwdMode = ref(false)
const saving = ref(false)
const message = ref('')

const form = reactive({
  name: auth.user?.name || '',
  email: auth.user?.email || ''
})

const pwdForm = reactive({ current: '', newPwd: '', confirm: '' })

async function saveProfile() {
  saving.value = true
  message.value = ''
  try {
    await auth.updateUserProfile({ name: form.name, email: form.email })
    editMode.value = false
    message.value = 'Perfil actualizado correctamente.'
  } catch (e) {
    message.value = 'Error al actualizar el perfil.'
  } finally {
    saving.value = false
  }
}

async function changePassword() {
  if (pwdForm.newPwd !== pwdForm.confirm) { message.value = 'Las contraseñas no coinciden.'; return }
  if (pwdForm.newPwd.length < 6) { message.value = 'Mínimo 6 caracteres.'; return }
  saving.value = true
  message.value = ''
  try {
    await auth.changePassword(pwdForm.newPwd)
    pwdMode.value = false
    pwdForm.current = pwdForm.newPwd = pwdForm.confirm = ''
    message.value = 'Contraseña actualizada correctamente.'
  } catch {
    message.value = 'Error al cambiar la contraseña. Puede que necesites volver a iniciar sesión.'
  } finally {
    saving.value = false
  }
}

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <AppShell>
    <div class="topbar">
      <span class="topbar-crumb mono text-xs">COSFI</span>
      <AppIcon name="chevron-right" :size="12" style="color:var(--text-3)" />
      <span class="topbar-title">Mi perfil</span>
    </div>

    <div class="page-content" style="max-width:580px;">
      <!-- Avatar + info header -->
      <div class="card animate-in" style="margin-bottom:16px;">
        <div class="card-body" style="display:flex;align-items:center;gap:20px;">
          <div class="avatar-lg">{{ auth.initials }}</div>
          <div style="flex:1;">
            <div style="font-size:16px;font-weight:600;margin-bottom:2px;">{{ auth.user?.name }}</div>
            <div class="mono text-xs text-muted">{{ auth.user?.email }}</div>
            <div class="mono text-xs text-muted" style="margin-top:4px;">
              Miembro desde {{ auth.user?.createdAt }}
            </div>
          </div>
          <div style="display:flex;gap:12px;">
            <div style="text-align:center;">
              <div class="mono" style="font-size:22px;font-weight:700;color:var(--text);">{{ auth.user?.stats?.audits || 0 }}</div>
              <div class="mono text-xs text-muted">auditorías</div>
            </div>
            <div style="text-align:center;">
              <div class="mono" style="font-size:22px;font-weight:700;color:var(--risk-l);">{{ auth.user?.stats?.approvedFindings || 0 }}</div>
              <div class="mono text-xs text-muted">aprobados</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Success/error message -->
      <div v-if="message" class="animate-in" style="display:flex;align-items:center;gap:8px;background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.2);border-radius:3px;padding:10px 14px;margin-bottom:16px;font-size:12px;color:var(--risk-l);">
        <AppIcon name="check-circle" :size="13" />
        {{ message }}
      </div>

      <!-- Edit profile -->
      <div class="card animate-in" style="margin-bottom:16px;">
        <div class="card-header">
          <AppIcon name="edit" :size="13" style="color:var(--text-2)" />
          <span style="font-size:12px;font-weight:500;">Información personal</span>
          <button class="btn btn-ghost btn-sm" style="margin-left:auto;" @click="editMode = !editMode">
            {{ editMode ? 'Cancelar' : 'Editar' }}
          </button>
        </div>
        <div class="card-body">
          <template v-if="!editMode">
            <div class="profile-row">
              <div class="form-label">Nombre</div>
              <div>{{ auth.user?.name }}</div>
            </div>
            <div class="profile-row">
              <div class="form-label">Correo</div>
              <div class="mono text-sm">{{ auth.user?.email }}</div>
            </div>
          </template>
          <template v-else>
            <div class="form-group">
              <label class="form-label">Nombre completo</label>
              <input v-model="form.name" class="form-input" type="text" />
            </div>
            <div class="form-group" style="margin-bottom:0;">
              <label class="form-label">Correo electrónico</label>
              <input v-model="form.email" class="form-input" type="email" />
            </div>
            <div style="margin-top:16px;display:flex;justify-content:flex-end;gap:8px;">
              <button class="btn btn-ghost btn-sm" @click="editMode=false">Cancelar</button>
              <button class="btn btn-primary btn-sm" @click="saveProfile" :disabled="saving">
                <div v-if="saving" class="spinner" style="width:10px;height:10px;border-color:rgba(0,0,0,0.2);border-top-color:#000;" />
                Guardar
              </button>
            </div>
          </template>
        </div>
      </div>

      <!-- Change password -->
      <div class="card animate-in" style="margin-bottom:16px;">
        <div class="card-header">
          <AppIcon name="lock" :size="13" style="color:var(--text-2)" />
          <span style="font-size:12px;font-weight:500;">Contraseña</span>
          <button class="btn btn-ghost btn-sm" style="margin-left:auto;" @click="pwdMode = !pwdMode">
            {{ pwdMode ? 'Cancelar' : 'Cambiar' }}
          </button>
        </div>
        <div v-if="pwdMode" class="card-body">
          <div class="form-group">
            <label class="form-label">Nueva contraseña</label>
            <input v-model="pwdForm.newPwd" class="form-input" type="password" placeholder="••••••••" />
          </div>
          <div class="form-group" style="margin-bottom:0;">
            <label class="form-label">Confirmar contraseña</label>
            <input v-model="pwdForm.confirm" class="form-input" type="password" placeholder="••••••••" />
          </div>
          <div style="margin-top:16px;display:flex;justify-content:flex-end;gap:8px;">
            <button class="btn btn-ghost btn-sm" @click="pwdMode=false">Cancelar</button>
            <button class="btn btn-primary btn-sm" @click="changePassword" :disabled="saving">Actualizar contraseña</button>
          </div>
        </div>
      </div>

      <!-- Sign out -->
      <div class="card animate-in">
        <div class="card-body" style="display:flex;align-items:center;justify-content:space-between;">
          <div>
            <div style="font-size:13px;font-weight:500;margin-bottom:2px;">Cerrar sesión</div>
            <div class="text-muted text-xs">Sal de tu cuenta en este dispositivo.</div>
          </div>
          <button class="btn btn-danger" @click="logout">
            <AppIcon name="logout" :size="13" />
            Salir
          </button>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.profile-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 8px;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}
.profile-row:last-child { border-bottom: none; }
</style>
