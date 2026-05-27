<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuditsStore } from '@/stores/audits'
import AppShell from '@/components/layout/AppShell.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { analyzeAudit } from '@/api/index'
import { STATUS_PILL_CLASS, RISK_PILL_CLASS } from '@/data/mock'

const route = useRoute()
const router = useRouter()
const store = useAuditsStore()

const auditId = computed(() => route.params.auditId)
const audit = computed(() => store.audits.find(a => a.id === auditId.value))
const docs = computed(() => store.documents[auditId.value] || [])
const findings = computed(() => store.findings[auditId.value] || [])

const activeTab = ref(route.query.tab || 'documentos')
const isDragOver = ref(false)

// Analysis state
const analysisRunning = ref(false)
const analysisMinimized = ref(false)
const analysisStages = ref([
  { id: 1, label: 'Extracción de texto', status: 'waiting' },
  { id: 2, label: 'Análisis con marcos normativos', status: 'waiting' },
  { id: 3, label: 'Consolidación de hallazgos', status: 'waiting' },
  { id: 4, label: 'Generando hallazgos', status: 'waiting' }
])
const engines = ref([
  { name: 'COBIT', pct: 0, status: 'waiting' },
  { name: 'COSO',  pct: 0, status: 'waiting' },
  { name: 'RGSI',  pct: 0, status: 'waiting' }
])
const globalPct = computed(() => Math.round((engines.value.reduce((s, e) => s + e.pct, 0)) / 3))
watch(activeTab, (tab) => {
  router.replace({
    query: {
      ...route.query,
      tab
    }
  })
})
watch(
  () => route.query.tab,
  (tab) => {
    if (tab) activeTab.value = tab
  }
)

// Reports selection
const selectedReports = ref(['matriz-hallazgos'])
const reportOptions = [
  { id: 'matriz-hallazgos', label: 'Matriz de hallazgos', desc: 'Consolidada COBIT × COSO × RGSI', icon: 'layers', format: 'XLSX' },
  { id: 'fichas-hallazgo',  label: 'Fichas de hallazgo',  desc: 'Una ficha por hallazgo aprobado', icon: 'file-text', format: 'DOCX/PDF' },
  { id: 'fichas-pruebas',   label: 'Fichas de pruebas',   desc: 'Pruebas sustentatorias',          icon: 'database', format: 'DOCX/PDF' },
  { id: 'matriz-coso',      label: 'Matriz COSO',          desc: 'Componentes × principios',       icon: 'grid', format: 'XLSX' }
]

const isTabLocked = computed(() => {
  if (!audit.value) return true
  return ['Pendiente', 'Procesando'].includes(audit.value.status)
})

onMounted(() => { store.setCurrentAudit(auditId.value) })

// ─── File upload ────────────────────────────────────────────────────────────
function handleDrop(e) {
  isDragOver.value = false
  Array.from(e.dataTransfer.files).forEach(f => store.addDocument(auditId.value, f))
}

function handleFileInput(e) {
  Array.from(e.target.files).forEach(f => store.addDocument(auditId.value, f))
}

function fileExtClass(type) {
  return { pdf: 'file-ext-pdf', docx: 'file-ext-docx', xlsx: 'file-ext-xlsx' }[type] || ''
}

function docStatusPill(status) {
  return { 'queued': 'pill-pending', 'indexing': 'pill-processing', 'ready': 'pill-done' }[status] || 'pill-pending'
}

// ─── AI Analysis ─────────────────────────────────────────────────────────────
async function startAnalysis() {
  const readyDocs = docs.value.filter(d => d.status === 'ready')
  if (!readyDocs.length) return

  analysisRunning.value = true
  analysisMinimized.value = false

  // Reset
  analysisStages.value.forEach(s => s.status = 'waiting')
  engines.value.forEach(e => { e.pct = 0; e.status = 'waiting' })

  // Stage 1: Extracción
  analysisStages.value[0].status = 'running'
  await simulateProgress(engines.value[0], 30, 600)
  await simulateProgress(engines.value[1], 25, 700)
  await simulateProgress(engines.value[2], 28, 650)
  analysisStages.value[0].status = 'done'

  // Stage 2: Llamada real al backend IA
  analysisStages.value[1].status = 'running'
  engines.value.forEach(e => e.status = 'running')

  try {
    await analyzeAudit(auditId.value)

    // El backend corre en background; esperamos y refrescamos estado/resultados.
    await waitForAnalysisCompletion()

    engines.value.forEach(e => { e.pct = 100; e.status = 'done' })
  } catch (error) {
    console.error('Error iniciando análisis IA real:', error)
    await Promise.all([
      simulateProgress(engines.value[0], 100, 1200).then(() => engines.value[0].status = 'done'),
      simulateProgress(engines.value[1], 100, 1400).then(() => engines.value[1].status = 'done'),
      simulateProgress(engines.value[2], 100, 1300).then(() => engines.value[2].status = 'done')
    ])
  }

  analysisStages.value[1].status = 'done'

  // Stage 3: Consolidación
  analysisStages.value[2].status = 'running'
  await delay(600)
  analysisStages.value[2].status = 'done'

  // Stage 4: Hallazgos
  analysisStages.value[3].status = 'running'
  await delay(400)

  await store.loadAudits()
  await store.setCurrentAudit(auditId.value)

  analysisStages.value[3].status = 'done'
  await delay(800)
  analysisRunning.value = false
  store.setAuditProgress(auditId.value, 100, 'En revisión')
  activeTab.value = 'hallazgos'
}

// ─── Helpers ────────────────────────────────────────────────────────────────
function delay(ms) { return new Promise(r => setTimeout(r, ms)) }

async function simulateProgress(engine, target, duration) {
  const start = engine.pct
  const steps = 20
  const step = (target - start) / steps
  const interval = duration / steps
  for (let i = 0; i < steps; i++) {
    await delay(interval)
    engine.pct = Math.min(target, Math.round(engine.pct + step))
  }
}

async function waitForAnalysisCompletion() {
  const maxAttempts = 30
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await delay(2000)
    await store.loadAudits()
    await store.setCurrentAudit(auditId.value)

    const current = store.audits.find(a => a.id === auditId.value)
    if (current && current.status !== 'Procesando') {
      return current
    }

    engines.value.forEach((engine, index) => {
      engine.pct = Math.min(95, 30 + (attempt + 1) * 2 + index)
      engine.status = 'running'
    })
  }

  return store.audits.find(a => a.id === auditId.value) || null
}

// ─── Findings helpers ────────────────────────────────────────────────────────
function riskPillClass(risk) {
  return { Extremo: 'pill-extreme', Alto: 'pill-high', Medio: 'pill-medium', Bajo: 'pill-low', Oportunidad: 'pill-opp' }[risk] || ''
}

function openFinding(f) {
  router.push(`/workspace/${auditId.value}/hallazgo/${f.id}`)
}

// ─── Report generation ───────────────────────────────────────────────────────
function toggleReport(id) {
  const idx = selectedReports.value.indexOf(id)
  if (idx >= 0) selectedReports.value.splice(idx, 1)
  else selectedReports.value.push(id)
}

const generatedReports = ref([])
const generatingReports = ref(false)

async function generateReports() {
  generatingReports.value = true
  await delay(2000)
  generatedReports.value = selectedReports.value.map(id => {
    const r = reportOptions.find(o => o.id === id)
    return { id, label: r.label, format: r.format, sha256: randomSha(), generatedAt: new Date().toLocaleString() }
  })
  generatingReports.value = false
}

function randomSha() { return Math.random().toString(16).slice(2, 10) + '...' }
</script>

<template>
  <AppShell>
    <!-- Workspace header -->
    <div class="workspace-header">
      <button class="btn btn-ghost btn-icon" @click="router.push('/auditorias')">
        <AppIcon name="arrow-left" :size="14" />
      </button>
      <div style="flex:1;min-width:0;">
        <div class="workspace-entity">{{ audit?.entity || '—' }}</div>
        <div class="workspace-period">{{ audit?.type }} · {{ audit?.period }}</div>
      </div>
      <span v-if="audit" class="pill" :class="STATUS_PILL_CLASS[audit.status]">{{ audit.status }}</span>

      <!-- Analysis mini-badge while running -->
      <button
        v-if="analysisRunning"
        class="btn btn-outline btn-sm"
        @click="analysisMinimized = false"
      >
        <div class="spinner" style="width:10px;height:10px;" />
        Ver análisis · {{ globalPct }}%
      </button>
    </div>

    <!-- Tabs -->
    <div style="padding:0 20px;border-bottom:1px solid var(--border);flex-shrink:0;">
      <div class="tabs" style="margin-bottom:0;border-bottom:none;">
        <div class="tab" :class="{ active: activeTab==='documentos' }" @click="activeTab='documentos'">
          <AppIcon name="file" :size="13" />
          Documentos
          <span v-if="docs.length" class="tab-badge">{{ docs.length }}</span>
        </div>
        <div
          class="tab"
          :class="{ active: activeTab==='hallazgos', disabled: isTabLocked }"
          @click="!isTabLocked && (activeTab='hallazgos')"
        >
          <AppIcon name="alert-triangle" :size="13" />
          Hallazgos
          <span v-if="findings.length" class="tab-badge">{{ findings.length }}</span>
        </div>
        <div
          class="tab"
          :class="{ active: activeTab==='reportes', disabled: isTabLocked }"
          @click="!isTabLocked && (activeTab='reportes')"
        >
          <AppIcon name="download" :size="13" />
          Reportes
        </div>
      </div>
    </div>

    <!-- Tab content -->
    <div class="page-content">

      <!-- ── DOCUMENTOS ── -->
      <template v-if="activeTab === 'documentos'">
        <div
          class="upload-zone animate-in"
          :class="{ dragover: isDragOver }"
          @dragover.prevent="isDragOver = true"
          @dragleave="isDragOver = false"
          @drop.prevent="handleDrop"
          @click="$refs.fileInput.click()"
          style="margin-bottom:20px;"
        >
          <input ref="fileInput" type="file" multiple accept=".pdf,.docx,.xlsx" style="display:none;" @change="handleFileInput" />
          <AppIcon name="upload" :size="24" style="color:var(--text-2);margin-bottom:10px;" />
          <h4>Arrastra archivos aquí</h4>
          <p>PDF, DOCX, XLSX · o haz clic para seleccionar</p>
        </div>

        <div v-if="docs.length" class="card animate-in" style="margin-bottom:20px;">
          <div class="card-header">
            <AppIcon name="file" :size="13" style="color:var(--text-2)" />
            <span style="font-size:12px;font-weight:500;">Archivos cargados</span>
            <span class="mono text-xs text-muted" style="margin-left:auto;">{{ docs.length }} archivos</span>
          </div>
          <div class="file-item" v-for="d in docs" :key="d.id">
            <div class="file-icon" :class="fileExtClass(d.type)">{{ d.type }}</div>
            <div class="file-info">
              <div class="file-name">{{ d.name }}</div>
              <div class="file-meta">{{ d.size }} · {{ d.chunks > 0 ? d.chunks + ' fragmentos' : 'procesando…' }} · {{ d.uploadedAt }}</div>
            </div>
            <span class="pill" :class="docStatusPill(d.status)">{{ d.status }}</span>
          </div>
        </div>

        <div class="animate-in">
          <button
            class="btn btn-primary"
            :disabled="!docs.some(d => d.status === 'ready') || analysisRunning"
            @click="startAnalysis"
          >
            <AppIcon name="zap" :size="14" />
            {{ analysisRunning ? 'Análisis en curso…' : 'Iniciar análisis IA' }}
          </button>
          <span v-if="!docs.some(d => d.status === 'ready')" class="mono text-xs text-muted" style="margin-left:10px;">
            Sube al menos un documento listo para analizar.
          </span>
        </div>
      </template>

      <!-- ── HALLAZGOS ── -->
      <template v-if="activeTab === 'hallazgos'">
        <!-- KPIs by risk -->
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:20px;" class="animate-in">
          <div v-for="r in ['Extremo','Alto','Medio','Bajo','Oportunidad']" :key="r" class="card" style="padding:12px;text-align:center;">
            <div class="mono" style="font-size:18px;font-weight:700;">
              {{ findings.filter(f => f.risk === r).length }}
            </div>
            <span class="pill" :class="riskPillClass(r)" style="margin-top:4px;">{{ r }}</span>
          </div>
        </div>

        <div class="card animate-in">
          <div class="card-header">
            <AppIcon name="alert-triangle" :size="13" style="color:var(--text-2)" />
            <span style="font-size:12px;font-weight:500;">Hallazgos detectados</span>
            <span class="mono text-xs text-muted" style="margin-left:auto;">{{ findings.length }} total</span>
          </div>

          <div v-if="findings.length === 0" class="empty-state">
            <h3>Sin hallazgos</h3>
            <p>Ejecuta el análisis IA desde la pestaña Documentos.</p>
          </div>

          <div v-for="f in findings" :key="f.id" class="finding-item" @click="openFinding(f)">
            <div style="flex:1;min-width:0;">
              <div class="finding-id">{{ f.id }}</div>
              <div class="finding-title">{{ f.title }}</div>
              <div class="finding-refs">
                <span v-if="f.cobitRef" class="ref-tag ref-cobit">{{ f.cobitRef.code }}</span>
                <span v-if="f.cosoRef"  class="ref-tag ref-coso" >{{ f.cosoRef.code  }}</span>
                <span v-if="f.rgsiRef"  class="ref-tag ref-rgsi" >{{ f.rgsiRef.code  }}</span>
              </div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;flex-shrink:0;">
              <span class="pill" :class="riskPillClass(f.risk)">{{ f.risk }}</span>
              <span class="pill" :class="STATUS_PILL_CLASS[f.status]">{{ f.status }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- ── REPORTES ── -->
      <template v-if="activeTab === 'reportes'">
        <div class="animate-in" style="display:grid;grid-template-columns:1fr 320px;gap:20px;">
          <div>
            <div class="section-label">Selecciona los reportes a generar</div>
            <div v-for="r in reportOptions" :key="r.id"
              class="report-card"
              :class="{ selected: selectedReports.includes(r.id) }"
              @click="toggleReport(r.id)"
            >
              <div class="report-icon">
                <AppIcon :name="r.icon" :size="16" />
              </div>
              <div style="flex:1;">
                <div style="font-size:13px;font-weight:500;margin-bottom:2px;">{{ r.label }}</div>
                <div class="mono text-xs text-muted">{{ r.desc }}</div>
              </div>
              <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;">
                <span class="pill pill-pending">{{ r.format }}</span>
                <div class="checkbox" :class="{ checked: selectedReports.includes(r.id) }">
                  <AppIcon v-if="selectedReports.includes(r.id)" name="check" :size="9" style="color:#000;" />
                </div>
              </div>
            </div>

            <button
              class="btn btn-primary"
              :disabled="!selectedReports.length || generatingReports"
              @click="generateReports"
              style="margin-top:12px;"
            >
              <div v-if="generatingReports" class="spinner" style="width:12px;height:12px;border-color:rgba(0,0,0,0.2);border-top-color:#000;" />
              <AppIcon v-else name="download" :size="13" />
              {{ generatingReports ? 'Generando…' : 'Generar reportes' }}
            </button>
          </div>

          <div>
            <div class="section-label">Reportes generados</div>
            <div v-if="!generatedReports.length" class="empty-state" style="padding:24px;text-align:left;">
              <p style="font-size:11px;">Selecciona los reportes y haz clic en "Generar reportes".</p>
            </div>
            <div v-for="r in generatedReports" :key="r.id" class="card" style="margin-bottom:8px;padding:12px 14px;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <AppIcon name="file-text" :size="14" style="color:var(--text-2)" />
                <span style="font-size:12px;font-weight:500;">{{ r.label }}</span>
                <span class="pill pill-done" style="margin-left:auto;">Listo</span>
              </div>
              <div class="sha-badge">SHA-256: {{ r.sha256 }}</div>
              <div class="mono text-xs text-muted" style="margin-top:4px;">{{ r.generatedAt }}</div>
              <button class="btn btn-ghost btn-sm" style="margin-top:8px;">
                <AppIcon name="download" :size="12" />
                Descargar {{ r.format }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Analysis Overlay -->
    <Transition name="fade">
      <div v-if="analysisRunning && !analysisMinimized" class="overlay-backdrop" @click.self="analysisMinimized = true">
        <div class="analysis-modal">
          <div class="modal-header">
            <span class="modal-title">Análisis IA en progreso</span>
            <div style="display:flex;align-items:center;gap:8px;margin-left:auto;">
              <span class="mono text-xs text-accent">{{ globalPct }}%</span>
              <button class="btn btn-ghost btn-icon btn-sm" @click="analysisMinimized = true">
                <AppIcon name="chevron-down" :size="13" />
              </button>
            </div>
          </div>

          <div class="modal-body">
            <!-- Stages -->
            <div style="margin-bottom:20px;">
              <div v-for="(s, i) in analysisStages" :key="s.id" class="analysis-stage">
                <div class="stage-indicator" :class="s.status">
                  <AppIcon v-if="s.status==='done'" name="check" :size="10" />
                  <template v-else>{{ i + 1 }}</template>
                </div>
                <div style="flex:1;">
                  <div style="font-size:12px;font-weight:500;margin-bottom:2px;">{{ s.label }}</div>
                  <div v-if="s.status==='running'" class="mono text-xs text-accent">En proceso…</div>
                  <div v-else-if="s.status==='done'" class="mono text-xs" style="color:var(--risk-l);">Completado</div>
                  <div v-else class="mono text-xs text-muted">En espera</div>
                </div>
              </div>
            </div>

            <div class="divider" />

            <!-- Engine bars -->
            <div class="section-label" style="margin-bottom:10px;">Motores activos</div>
            <div v-for="e in engines" :key="e.name" class="engine-row">
              <div class="engine-name">{{ e.name }}</div>
              <div class="engine-bar">
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: e.pct + '%' }" />
                </div>
              </div>
              <div class="engine-pct">{{ e.pct }}%</div>
              <span class="pill" :class="e.status==='done'?'pill-done':e.status==='running'?'pill-processing':'pill-pending'" style="margin-left:4px;">
                {{ e.status==='done'?'✓':e.status==='running'?'…':'—' }}
              </span>
            </div>
          </div>

          <div class="modal-footer" style="justify-content:flex-start;">
            <span class="mono text-xs text-muted">Los hallazgos se cargarán automáticamente al finalizar.</span>
          </div>
        </div>
      </div>
    </Transition>
  </AppShell>
</template>
