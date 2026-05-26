<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuditsStore } from '@/stores/audits'
import AppIcon from '@/components/ui/AppIcon.vue'

const emit = defineEmits(['close'])
const router = useRouter()
const store = useAuditsStore()

const step = ref(1)
const form = reactive({
  entity: '', type: 'Auditoría TI', city: '', period: '',
  frameworks: ['COBIT', 'COSO', 'RGSI']
})
const periodError = ref('')

const entityTypes = ['Banco', 'Cooperativa', 'Financiera', 'Fondo Financiero Privado', 'Institución Financiera de Desarrollo']
const auditTypes  = ['Auditoría TI', 'Auditoría Seguridad', 'Auditoría Cumplimiento', 'Auditoría Operativa']
const frameworkOptions = ['COBIT', 'COSO', 'RGSI']
const cities = ['La Paz', 'Cochabamba', 'Santa Cruz', 'Oruro', 'Potosí', 'Sucre', 'Tarija', 'Beni', 'Pando']

const isStep1Valid = computed(() => form.entity && !periodError.value)

function validatePeriod(value) {
  if (!value) {
    periodError.value = ''
    return true
  }
  const pattern = /^\d{4}-Q[1-4]$/
  if (!pattern.test(value)) {
    periodError.value = 'Formato inválido. Usa: YYYY-Q[1-4] (ej: 2026-Q1)'
    return false
  }
  periodError.value = ''
  return true
}

function toggleFramework(fw) {
  const idx = form.frameworks.indexOf(fw)
  if (idx >= 0) form.frameworks.splice(idx, 1)
  else form.frameworks.push(fw)
}

async function create() {
  // Validar período antes de crear
  const quarter = Math.ceil((new Date().getMonth() + 1) / 3)
  const period = form.period || `${new Date().getFullYear()}-Q${quarter}`
  
  if (!validatePeriod(period)) {
    console.warn('Período inválido:', period)
    return
  }
  
  const city = form.city || 'La Paz'
  try {
    const id = await store.createAudit({
      entity: form.entity,
      type: form.type,
      city,
      period,
      frameworks: [...form.frameworks]
    })
    emit('close')
    router.push(`/workspace/${id}`)
  } catch (e) {
    console.error('Error creando auditoría:', e)
    periodError.value = 'Error al crear auditoría. Intenta de nuevo.'
  }
}

function nextStep() {
  if (isStep1Valid.value) {
    step.value++
  }
}
</script>

<template>
  <div class="overlay-backdrop" @click.self="emit('close')">
    <div class="modal">
      <div class="modal-header">
        <div>
          <div class="modal-title">Nueva auditoría</div>
          <div class="mono text-xs text-muted">Paso {{ step }} de 2</div>
        </div>
        <button class="btn btn-ghost btn-icon btn-sm" @click="emit('close')">
          <AppIcon name="x" :size="14" />
        </button>
      </div>

      <!-- Step indicator -->
      <div style="padding:0 20px;border-bottom:1px solid var(--border);display:flex;gap:0;">
        <div v-for="s in 2" :key="s" style="flex:1;padding:8px 0;text-align:center;">
          <span class="mono text-xs" :style="{ color: s === step ? 'var(--accent)' : s < step ? 'var(--risk-l)' : 'var(--text-3)' }">
            {{ s === step ? '▶' : s < step ? '✓' : '○' }}
            {{ s === 1 ? 'Entidad' : 'Marcos' }}
          </span>
        </div>
      </div>

      <div class="modal-body">
        <!-- Step 1 -->
        <template v-if="step === 1">
          <div class="form-group">
            <label class="form-label">Nombre de la entidad *</label>
            <input v-model="form.entity" class="form-input" placeholder="Ej. Banco Fassil S.A." required />
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div class="form-group">
              <label class="form-label">Tipo de auditoría</label>
              <select v-model="form.type" class="form-select">
                <option v-for="t in auditTypes" :key="t">{{ t }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Ciudad</label>
              <select v-model="form.city" class="form-select">
                <option value="">Seleccionar…</option>
                <option v-for="c in cities" :key="c">{{ c }}</option>
              </select>
            </div>
          </div>
          <div class="form-group" style="margin-bottom:0;">
            <label class="form-label">Período <span style="color:var(--text-3);">(opcional)</span></label>
            <input
              v-model="form.period"
              class="form-input"
              :style="{ borderColor: periodError ? 'var(--risk-h)' : '' }"
              placeholder="Ej. 2026-Q1 (vacío = trimestre actual)"
              @input="validatePeriod(form.period)"
            />
            <div v-if="periodError" style="color:var(--risk-h);font-size:12px;margin-top:4px;font-weight:500;">
              ⚠️ {{ periodError }}
            </div>
          </div>
        </template>

        <!-- Step 2 -->
        <template v-else>
          <div class="section-label" style="margin-bottom:12px;">Marcos normativos a aplicar</div>
          <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:20px;">
            <div
              v-for="fw in frameworkOptions"
              :key="fw"
              class="report-card"
              :class="{ selected: form.frameworks.includes(fw) }"
              @click="toggleFramework(fw)"
              style="margin-bottom:0;"
            >
              <div class="report-icon">
                <AppIcon name="shield" :size="14" />
              </div>
              <div style="flex:1;">
                <div style="font-size:13px;font-weight:600;margin-bottom:1px;">{{ fw }}</div>
                <div class="mono text-xs text-muted">
                  {{ fw==='COBIT' ? 'Gobernanza y gestión de TI · ISACA' : fw==='COSO' ? 'Control interno · COSO 2013' : 'Seguridad de la información · ASFI Bolivia' }}
                </div>
              </div>
              <div class="checkbox" :class="{ checked: form.frameworks.includes(fw) }">
                <AppIcon v-if="form.frameworks.includes(fw)" name="check" :size="9" style="color:#000;" />
              </div>
            </div>
          </div>
        </template>
      </div>

      <div class="modal-footer">
        <button v-if="step > 1" class="btn btn-ghost" @click="step--">Atrás</button>
        <div style="margin-left:auto;display:flex;gap:8px;">
          <button class="btn btn-ghost" @click="emit('close')">Cancelar</button>
          <button v-if="step < 2" class="btn btn-primary" :disabled="!isStep1Valid" @click="nextStep">
            Siguiente
          </button>
          <button v-else class="btn btn-primary" :disabled="!form.frameworks.length" @click="create">
            <AppIcon name="plus" :size="13" />
            Crear auditoría
          </button>
        </div>
      </div>
    </div>
  </div>
</template>