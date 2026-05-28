<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuditsStore } from '@/stores/audits'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/layout/AppShell.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import NewAuditModal from '@/components/NewAuditModal.vue'
import { STATUS_PILL_CLASS, RISK_PILL_CLASS } from '@/data/mock'

const router = useRouter()
const store = useAuditsStore()
const auth = useAuthStore()

const showNewAudit = ref(false)

const kpis = computed(() => {
  const active = store.audits.filter(a => a.status !== 'Finalizada').length
  const pending = store.audits.reduce((s, a) => s + (a.pendingFindings || 0), 0)
  const docs = store.audits.reduce((s, a) => s + (a.documents || 0), 0)
  return [
    { label: 'Auditorías activas', value: active, delta: '+2 este mes' },
    { label: 'Hallazgos pendientes', value: pending, delta: 'requieren revisión' },
    { label: 'Documentos analizados', value: docs, delta: 'en todos los proyectos' }
  ]
})

const recent = computed(() => store.audits.slice(0, 5))

function openAudit(audit) {
  store.setCurrentAudit(audit.id)
  router.push(`/workspace/${audit.id}`)
}

function statusDot(status) {
  const map = { 'Pendiente': '#64748b', 'Procesando': '#3b82f6', 'En revisión': '#eab308', 'Finalizada': '#22c55e' }
  return map[status] || '#64748b'
}

function maturityColor(level) {
  const map = {
    1: 'hsl(354, 80%, 55%)',
    2: 'hsl(28, 85%, 55%)',
    3: 'hsl(200, 85%, 55%)',
    4: 'hsl(262, 80%, 60%)',
    5: 'hsl(142, 80%, 45%)'
  }
  return map[Math.round(level)] || 'hsl(200, 85%, 55%)'
}
</script>

<template>
  <AppShell>
    <div class="topbar">
      <span class="topbar-crumb mono text-xs">COSFI</span>
      <AppIcon name="chevron-right" :size="12" style="color:var(--text-3)" />
      <span class="topbar-title">Inicio</span>
      <div class="topbar-actions">
        <button class="btn btn-primary btn-sm" @click="showNewAudit = true">
          <AppIcon name="plus" :size="13" />
          Nueva auditoría
        </button>
      </div>
    </div>

    <div class="page-content">
      <!-- KPIs -->
      <div class="kpi-grid">
        <div v-for="kpi in kpis" :key="kpi.label" class="kpi-card animate-in">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value">{{ kpi.value }}</div>
          <div class="kpi-delta text-muted">{{ kpi.delta }}</div>
        </div>
      </div>

      <!-- Recent audits -->
      <div class="card animate-in">
        <div class="card-header">
          <AppIcon name="list" :size="14" style="color:var(--text-2)" />
          <span style="font-size:12px;font-weight:500;">Auditorías recientes</span>
          <div style="margin-left:auto">
            <RouterLink to="/auditorias" class="btn btn-ghost btn-sm">Ver todas</RouterLink>
          </div>
        </div>
        <div v-if="recent.length === 0" class="empty-state">
          <h3>Sin auditorías</h3>
          <p>Crea tu primera auditoría con el botón "Nueva auditoría".</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Entidad</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Progreso</th>
              <th>Hallazgos</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in recent" :key="a.id" @click="openAudit(a)">
              <td>
                <div style="display:flex;align-items:center;gap:4px;">
                  <div style="font-weight:500;font-size:13px;">{{ a.entity }}</div>
                  <span v-if="a.maturity" class="mono" :style="{ color: maturityColor(a.maturity.level), border: `1px solid ${maturityColor(a.maturity.level)}`, borderRadius: '4px', padding: '1px 5px', fontSize: '9px', fontWeight: 'bold', display: 'inline-block', lineHeight: '1', background: 'rgba(255,255,255,0.02)' }">
                    M{{ a.maturity.level }}
                  </span>
                </div>
                <div class="mono text-xs text-muted">{{ a.city }} · {{ a.period }}</div>
              </td>
              <td><span class="mono text-xs text-muted">{{ a.type }}</span></td>
              <td>
                <span class="pill" :class="STATUS_PILL_CLASS[a.status]">
                  <span class="status-dot" :style="{ background: statusDot(a.status) }" />
                  {{ a.status }}
                </span>
              </td>
              <td style="min-width:100px">
                <div style="display:flex;align-items:center;gap:8px;">
                  <div class="progress-bar" style="flex:1">
                    <div class="progress-fill" :style="{ width: a.progress + '%' }" />
                  </div>
                  <span class="mono text-xs text-muted">{{ a.progress }}%</span>
                </div>
              </td>
              <td>
                <span class="mono text-sm">{{ a.findings }}</span>
                <span v-if="a.pendingFindings" class="mono text-xs text-muted"> ({{ a.pendingFindings }} pend.)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <NewAuditModal v-if="showNewAudit" @close="showNewAudit = false" />
  </AppShell>
</template>
