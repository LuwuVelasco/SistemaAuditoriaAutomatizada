<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuditsStore } from '@/stores/audits'
import AppShell from '@/components/layout/AppShell.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import NewAuditModal from '@/components/NewAuditModal.vue'
import { STATUS_PILL_CLASS } from '@/data/mock'

const router = useRouter()
const store = useAuditsStore()

const showNewAudit = ref(false)
const viewMode = ref('list') // 'list' | 'grid'
const search = ref('')
const filterStatus = ref('Todos')

const statusFilters = ['Todos', 'Pendiente', 'Procesando', 'En revisión', 'Finalizada']

const filtered = computed(() => {
  return store.audits.filter(a => {
    const matchSearch = !search.value ||
      a.entity.toLowerCase().includes(search.value.toLowerCase()) ||
      a.type.toLowerCase().includes(search.value.toLowerCase()) ||
      a.city.toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = filterStatus.value === 'Todos' || a.status === filterStatus.value
    return matchSearch && matchStatus
  })
})

function openAudit(id) {
  store.setCurrentAudit(id)
  router.push(`/workspace/${id}`)
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
  return map[level] || 'hsl(200, 85%, 55%)'
}
</script>

<template>
  <AppShell>
    <div class="topbar">
      <span class="topbar-crumb mono text-xs">COSFI</span>
      <AppIcon name="chevron-right" :size="12" style="color:var(--text-3)" />
      <span class="topbar-title">Auditorías</span>
      <div class="topbar-actions">
        <button class="btn btn-primary btn-sm" @click="showNewAudit = true">
          <AppIcon name="plus" :size="13" />
          Nueva auditoría
        </button>
      </div>
    </div>

    <div class="page-content">
      <!-- Filter bar -->
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:16px;flex-wrap:wrap;">
        <div class="search-wrap" style="flex:1;min-width:200px;max-width:320px;">
          <AppIcon name="search" :size="14" class="search-icon" />
          <input v-model="search" class="form-input" placeholder="Buscar entidad, tipo, ciudad…" style="padding-left:32px;" />
        </div>

        <div class="filter-bar">
          <span
            v-for="s in statusFilters"
            :key="s"
            class="filter-chip"
            :class="{ active: filterStatus === s }"
            @click="filterStatus = s"
          >{{ s }}</span>
        </div>

        <div class="view-toggle" style="margin-left:auto;">
          <div class="view-toggle-btn" :class="{ active: viewMode === 'list' }" @click="viewMode = 'list'">
            <AppIcon name="list" :size="14" />
          </div>
          <div class="view-toggle-btn" :class="{ active: viewMode === 'grid' }" @click="viewMode = 'grid'">
            <AppIcon name="grid" :size="14" />
          </div>
        </div>
      </div>

      <!-- Grid view -->
      <div v-if="viewMode === 'grid'" class="audit-grid">
        <div
          v-for="a in filtered"
          :key="a.id"
          class="audit-card animate-in"
          @click="openAudit(a.id)"
        >
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:6px;">
            <div class="audit-card-entity">
              {{ a.entity }}
              <span v-if="a.maturity" class="mono" :style="{ color: maturityColor(a.maturity.level), border: `1px solid ${maturityColor(a.maturity.level)}`, borderRadius: '4px', padding: '1px 5px', fontSize: '9px', fontWeight: 'bold', marginLeft: '6px', display: 'inline-block', lineHeight: '1', background: 'rgba(255,255,255,0.02)' }">
                M{{ a.maturity.level }}
              </span>
            </div>
            <span class="pill" :class="STATUS_PILL_CLASS[a.status]">
              <span class="status-dot" :style="{ background: statusDot(a.status) }" />
              {{ a.status }}
            </span>
          </div>
          <div class="audit-card-meta">{{ a.type }} · {{ a.city }} · {{ a.period }}</div>

          <div style="margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
              <span class="mono text-xs text-muted">Progreso</span>
              <span class="mono text-xs">{{ a.progress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: a.progress + '%' }" />
            </div>
          </div>

          <div style="display:flex;gap:12px;">
            <div>
              <div class="mono text-xs text-muted">Hallazgos</div>
              <div class="mono" style="font-size:16px;font-weight:600;">{{ a.findings }}</div>
            </div>
            <div>
              <div class="mono text-xs text-muted">Documentos</div>
              <div class="mono" style="font-size:16px;font-weight:600;">{{ a.documents }}</div>
            </div>
          </div>

          <div style="display:flex;gap:4px;margin-top:12px;">
            <span v-for="fw in a.frameworks" :key="fw" class="ref-tag" :class="fw==='COBIT'?'ref-cobit':fw==='COSO'?'ref-coso':'ref-rgsi'">
              {{ fw }}
            </span>
          </div>
        </div>
      </div>

      <!-- List view -->
      <div v-else class="card">
        <div v-if="filtered.length === 0" class="empty-state">
          <h3>Sin resultados</h3>
          <p>No se encontraron auditorías con los filtros actuales.</p>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Entidad</th>
              <th>Tipo</th>
              <th>Ciudad</th>
              <th>Estado</th>
              <th>Progreso</th>
              <th>Hallazgos</th>
              <th>Docs</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in filtered" :key="a.id" @click="openAudit(a.id)">
              <td>
                <div style="display:flex;align-items:center;gap:4px;">
                  <div style="font-weight:500;">{{ a.entity }}</div>
                  <span v-if="a.maturity" class="mono" :style="{ color: maturityColor(a.maturity.level), border: `1px solid ${maturityColor(a.maturity.level)}`, borderRadius: '4px', padding: '1px 5px', fontSize: '9px', fontWeight: 'bold', display: 'inline-block', lineHeight: '1', background: 'rgba(255,255,255,0.02)' }">
                    M{{ a.maturity.level }}
                  </span>
                </div>
                <div class="mono text-xs text-muted">{{ a.period }}</div>
              </td>
              <td><span class="mono text-xs text-muted">{{ a.type }}</span></td>
              <td><span class="mono text-xs text-muted">{{ a.city }}</span></td>
              <td>
                <span class="pill" :class="STATUS_PILL_CLASS[a.status]">
                  <span class="status-dot" :style="{ background: statusDot(a.status) }" />
                  {{ a.status }}
                </span>
              </td>
              <td style="min-width:110px;">
                <div style="display:flex;align-items:center;gap:8px;">
                  <div class="progress-bar" style="flex:1;">
                    <div class="progress-fill" :style="{ width: a.progress + '%' }" />
                  </div>
                  <span class="mono text-xs text-muted">{{ a.progress }}%</span>
                </div>
              </td>
              <td><span class="mono text-sm">{{ a.findings }}</span></td>
              <td><span class="mono text-sm">{{ a.documents }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <NewAuditModal v-if="showNewAudit" @close="showNewAudit = false" />
  </AppShell>
</template>
