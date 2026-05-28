<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuditsStore } from '@/stores/audits'
import AppShell from '@/components/layout/AppShell.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import ChatBot from '@/components/ChatBot.vue'
import TraceabilityGraph from '@/components/TraceabilityGraph.vue'
import { analyzeAudit, downloadReport, generateReports as remoteGenerateReports, getReports } from '@/api/index'
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
watch(activeTab, (tab) => {
  if (tab === 'reportes') loadReports()
})

// Reports selection
const selectedReports = ref(['matriz-hallazgos'])
const reportOptions = [
  { id: 'matriz-hallazgos', label: 'Matriz de hallazgos', desc: 'Consolidada COBIT × COSO × RGSI', icon: 'layers', format: 'xlsx' },
  { id: 'fichas-hallazgo',  label: 'Fichas de hallazgo',  desc: 'Una ficha por hallazgo aprobado', icon: 'file-text', format: 'docx' },
  { id: 'fichas-pruebas',   label: 'Fichas de pruebas',   desc: 'Pruebas sustentatorias',          icon: 'database', format: 'docx' },
  { id: 'matriz-coso',      label: 'Matriz COSO',          desc: 'Componentes × principios',       icon: 'grid', format: 'xlsx' },
  { id: 'informe-madurez',  label: 'Informe de Madurez',  desc: 'Autoevaluación de madurez documental', icon: 'shield', format: 'docx' }
]

const isTabLocked = computed(() => {
  if (!audit.value) return true
  return ['Pendiente', 'Procesando'].includes(audit.value.status)
})

onMounted(async () => {
  await store.setCurrentAudit(auditId.value)
  await loadReports()
})

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

function latestPerKind(rawList) {
  const byKind = {}
  for (const r of rawList) {
    const k = r.kind?.value ?? r.kind
    if (!byKind[k] || (r.generatedAt || '') > (byKind[k].generatedAt || '')) {
      byKind[k] = r
    }
  }
  return Object.values(byKind).map(mapReport)
}

async function loadReports() {
  try {
    const data = await getReports(auditId.value)
    generatedReports.value = latestPerKind(data || [])
  } catch (error) {
    console.error('Error cargando reportes:', error)
  }
}

async function generateReports() {
  generatingReports.value = true
  try {
    const created = []
    for (const id of selectedReports.value) {
      const option = reportOptions.find(o => o.id === id)
      if (!option) continue
      const reports = await remoteGenerateReports(auditId.value, [id], option.format)
      created.push(...(Array.isArray(reports) ? reports : [reports]))
    }
    // Reemplaza el slot de cada tipo generado, mantiene los demás
    const next = [...generatedReports.value]
    for (const r of created.map(mapReport)) {
      const idx = next.findIndex(c => (c.kind?.value ?? c.kind) === (r.kind?.value ?? r.kind))
      if (idx >= 0) next[idx] = r
      else next.push(r)
    }
    generatedReports.value = next
  } catch (error) {
    console.error('Error generando reportes:', error)
  } finally {
    generatingReports.value = false
  }
}

function formatBoliviaDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString('es-BO', {
      timeZone: 'America/La_Paz',
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

async function downloadGeneratedReport(report) {
  try {
    const { blob, filename } = await downloadReport(auditId.value, report.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename || `${report.label}.${report.format.toLowerCase()}`
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (error) {
    console.error('Error descargando reporte:', error)
  }
}

function mapReport(r) {
  const opt = reportOptions.find(o => o.id === r.kind || o.id === r.kind?.value)
  return {
    id: r.id,
    kind: r.kind,
    label: opt?.label || r.kind,
    format: (r.format || '').toUpperCase(),
    sha256: r.sha256,
    generatedAt: formatBoliviaDate(r.generatedAt),
    supabasePath: r.supabasePath,
  }
}

watch(auditId, () => {
  if (activeTab.value === 'reportes') loadReports()
})

// ─── Documentary Maturity ───────────────────────────────────────────────────
const localMaturity = ref(null)

const localLevel = computed(() => localMaturity.value?.level ?? 1)
const localScores = computed(() => localMaturity.value?.scores ?? { policies: 0, processes: 0, traceability: 0, culture: 0 })
const localChecklist = ref({
  l1_repositorios: true, l1_sin_politicas: true,
  l2_cuadro: false, l2_calendario: false, l2_desigual: true,
  l3_procesos: false, l3_roles: false, l3_trazabilidad: false,
  l4_riesgos: false, l4_activos: false, l4_coordinacion: false,
  l5_cultura: false, l5_mejora: false, l5_inspeccion: false
})
const localGapAnalysis = computed(() => localMaturity.value?.gapAnalysis ?? { strengths: [], weaknesses: [], roadmap: [] })

watch(
  () => audit.value,
  (newAudit) => {
    if (newAudit) {
      if (newAudit.maturity && Object.keys(newAudit.maturity).length > 0) {
        localMaturity.value = JSON.parse(JSON.stringify(newAudit.maturity))
        if (newAudit.maturity.checklist) {
          localChecklist.value = JSON.parse(JSON.stringify(newAudit.maturity.checklist))
        }
      } else {
        // Initialize default maturity structure
        const defaultChecklist = {
          l1_repositorios: true, l1_sin_politicas: true,
          l2_cuadro: false, l2_calendario: false, l2_desigual: true,
          l3_procesos: false, l3_roles: false, l3_trazabilidad: false,
          l4_riesgos: false, l4_activos: false, l4_coordinacion: false,
          l5_cultura: false, l5_mejora: false, l5_inspeccion: false
        }
        localMaturity.value = {
          level: 1,
          scores: { policies: 20, processes: 10, traceability: 15, culture: 5 },
          checklist: defaultChecklist,
          gapAnalysis: {
            strengths: ["Existen repositorios digitales para almacenamiento de archivos."],
            weaknesses: ["Ausencia de políticas documentales aprobadas formalmente.", "Falta de un cuadro de clasificación archivística."],
            roadmap: ["Diseñar y formalizar un Cuadro de Clasificación Documental básico.", "Definir responsables funcionales y técnicos de gestión de archivos."]
          }
        }
        localChecklist.value = defaultChecklist
      }
    }
  },
  { immediate: true, deep: true }
)

watch(
  localChecklist,
  (chk) => {
    if (!localMaturity.value) {
      localMaturity.value = {
        level: 1,
        scores: { policies: 0, processes: 0, traceability: 0, culture: 0 },
        checklist: {},
        gapAnalysis: { strengths: [], weaknesses: [], roadmap: [] }
      }
    }
    
    // Policies score
    let pol = 0
    if (!chk.l1_sin_politicas) pol += 25
    if (chk.l2_cuadro) pol += 35
    if (chk.l2_calendario) pol += 25
    if (!chk.l2_desigual) pol += 15
    
    // Processes score
    let prc = 0
    if (chk.l3_procesos) prc += 35
    if (chk.l3_roles) prc += 35
    if (chk.l4_coordinacion) prc += 30
    
    // Traceability score
    let trc = 0
    if (chk.l1_repositorios) trc += 25
    if (chk.l3_trazabilidad) trc += 45
    if (chk.l4_activos) trc += 30
    
    // Culture score
    let clt = 0
    if (chk.l4_riesgos) clt += 25
    if (chk.l5_cultura) clt += 25
    if (chk.l5_mejora) clt += 25
    if (chk.l5_inspeccion) clt += 25

    localMaturity.value.scores = {
      policies: Math.min(100, pol),
      processes: Math.min(100, prc),
      traceability: Math.min(100, trc),
      culture: Math.min(100, clt)
    }

    // Calculate level based on average score
    const avg = (pol + prc + trc + clt) / 4
    let lvl = 1
    if (avg > 85) lvl = 5
    else if (avg > 65) lvl = 4
    else if (avg > 40) lvl = 3
    else if (avg > 20) lvl = 2
    
    localMaturity.value.level = lvl

    // Auto-generate dynamic gapAnalysis values based on checklist state!
    const strengths = []
    const weaknesses = []
    const roadmap = []

    if (chk.l1_repositorios) strengths.push("Existen repositorios digitales para almacenamiento.")
    else weaknesses.push("No existen repositorios digitales para centralizar archivos.")

    if (chk.l2_cuadro && chk.l2_calendario) strengths.push("Cuadro de clasificación y calendarios de retención formalizados.")
    else {
      weaknesses.push("Falta aprobar o aplicar de forma uniforme las normas de retención y clasificación.")
      roadmap.push("Implementar y aprobar un Cuadro de Clasificación y Calendario de Conservación.")
    }

    if (chk.l3_procesos && chk.l3_roles) strengths.push("La gestión documental está integrada y existen roles definidos.")
    else {
      weaknesses.push("Brecha organizativa: falta de roles claros (IT, legal, áreas de negocio).")
      roadmap.push("Definir un comité multidisciplinario y asignar responsables de la gobernanza.")
    }

    if (chk.l4_riesgos && chk.l4_activos) strengths.push("Gobierno de la información activo; la dirección reconoce los riesgos documentales.")
    else {
      weaknesses.push("Baja participación directiva; los documentos no se gestionan como activos.")
      roadmap.push("Capacitar a la alta dirección en cumplimiento archivístico y gestión de riesgos.")
    }

    if (chk.l5_cultura && chk.l5_mejora) strengths.push("Cultura documental sólida con procesos de mejora continua activos.")
    else {
      if (lvl >= 4) {
        weaknesses.push("Falta de automatización para auditorías o litigios permanentes.")
        roadmap.push("Establecer revisiones de mejora continua semestrales para anticipar riesgos regulatorios de la ASFI.")
      }
    }

    // IA: Integrate findings-based alerts into gap analysis
    if (hasClassificationFinding.value) {
      weaknesses.push("⚠ IA: Se detectaron hallazgos relacionados con ausencia de políticas o clasificación documental.")
      roadmap.push("Revisar y formalizar las políticas documentales de acuerdo con los hallazgos de IA.")
    }
    if (hasAccessControlFinding.value) {
      weaknesses.push("⚠ IA: Hallazgos sobre control de acceso o cuentas privilegiadas sin gestión.")
      roadmap.push("Implementar controles de acceso y revisión periódica de cuentas según los hallazgos.")
    }
    if (hasBcpFinding.value) {
      weaknesses.push("⚠ IA: Pruebas de continuidad de negocio (BCP) inexistentes o insuficientes.")
      roadmap.push("Diseñar y ejecutar pruebas de BCP para asegurar la resiliencia documental.")
    }

    localMaturity.value.gapAnalysis = {
      strengths: strengths.slice(0, 5),
      weaknesses: weaknesses.slice(0, 5),
      roadmap: roadmap.slice(0, 5)
    }
  },
  { deep: true }
)

const isSaving = ref(false)
const hasChanges = computed(() => {
  if (!audit.value) return false
  // If the audit has no maturity yet, any change is new
  if (!audit.value.maturity || !audit.value.maturity.checklist) return true
  return JSON.stringify(localChecklist.value) !== JSON.stringify(audit.value.maturity.checklist)
})

async function saveMaturity() {
  if (!audit.value) return
  isSaving.value = true
  try {
    const updatedMaturity = {
      ...localMaturity.value,
      checklist: localChecklist.value
    }
    await store.updateAuditMaturity(auditId.value, updatedMaturity)
  } catch (error) {
    console.error("Error guardando madurez documental:", error)
  } finally {
    isSaving.value = false
  }
}

// ─── Radar Chart SVG ────────────────────────────────────────────────────────
const svgSize = 300
const center = svgSize / 2
const maxRadius = 85

function getPoint(index, value) {
  const percentage = value / 100
  const radius = maxRadius * percentage
  if (index === 0) return { x: center, y: center - radius }
  if (index === 1) return { x: center + radius, y: center }
  if (index === 2) return { x: center, y: center + radius }
  if (index === 3) return { x: center - radius, y: center }
  return { x: center, y: center }
}

const pointsPath = computed(() => {
  const p0 = getPoint(0, localScores.value.policies)
  const p1 = getPoint(1, localScores.value.processes)
  const p2 = getPoint(2, localScores.value.traceability)
  const p3 = getPoint(3, localScores.value.culture)
  return `M ${p0.x} ${p0.y} L ${p1.x} ${p1.y} L ${p2.x} ${p2.y} L ${p3.x} ${p3.y} Z`
})

// HSL level color
const levelColor = computed(() => {
  const colors = {
    1: 'hsl(354, 80%, 55%)',
    2: 'hsl(28, 85%, 55%)',
    3: 'hsl(200, 85%, 55%)',
    4: 'hsl(262, 80%, 60%)',
    5: 'hsl(142, 80%, 45%)'
  }
  return colors[localLevel.value] || 'hsl(200, 85%, 55%)'
})

const levelTextHeader = computed(() => {
  const titles = {
    1: 'Nivel 1: Acumulación Digital',
    2: 'Nivel 2: Normas Básicas',
    3: 'Nivel 3: Procesos Alineados',
    4: 'Nivel 4: Gobierno de la Info',
    5: 'Nivel 5: Cultura Documental'
  }
  return titles[localLevel.value] || ''
})

const levelDescription = computed(() => {
  const descs = {
    1: 'Existen repositorios electrónicos sin políticas ni responsabilidades definidas. Alto riesgo de cumplimiento y desorganización.',
    2: 'Hay cuadro de clasificación y calendarios de retención formalizados, pero su aplicación es desigual. Dependencia del área técnica.',
    3: 'La gestión documental está plenamente incorporada a los procedimientos clave con roles de control claros y trazabilidad real.',
    4: 'La dirección asume los riesgos documentales. La información y los registros se gestionan activamente como un activo de valor estratégico.',
    5: 'La mejora continua forma parte de la cultura organizacional. El sistema previene proactivamente los riesgos legales o regulatorios de la ASFI.'
  }
  return descs[localLevel.value] || ''
})

// Pre-fill / warnings based on findings
const hasAccessControlFinding = computed(() => findings.value.some(f => f.title.toLowerCase().includes('acceso') || f.description.toLowerCase().includes('acceso')))
const hasClassificationFinding = computed(() => findings.value.some(f => f.title.toLowerCase().includes('clasific') || f.description.toLowerCase().includes('clasific')))
const hasBcpFinding = computed(() => findings.value.some(f => f.title.toLowerCase().includes('continuidad') || f.description.toLowerCase().includes('bcp') || f.title.toLowerCase().includes('bcp')))
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
          :class="{ active: activeTab==='mapa', disabled: isTabLocked }"
          @click="!isTabLocked && (activeTab='mapa')"
        >
          <AppIcon name="git-branch" :size="13" />
          Mapa
        </div>
        <div
          class="tab"
          :class="{ active: activeTab==='madurez', disabled: isTabLocked }"
          @click="!isTabLocked && (activeTab='madurez')"
        >
          <AppIcon name="shield" :size="13" />
          Madurez
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
                <span v-for="ref in (f.cobitRefs || [])" :key="`cobit-${f.id}-${ref.code}`" class="ref-tag ref-cobit">{{ ref.code }}</span>
                <span v-for="ref in (f.cosoRefs || [])" :key="`coso-${f.id}-${ref.code}`" class="ref-tag ref-coso">{{ ref.code }}</span>
                <span v-for="ref in (f.rgsiRefs || [])" :key="`rgsi-${f.id}-${ref.code}`" class="ref-tag ref-rgsi">{{ ref.code }}</span>
              </div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px;flex-shrink:0;">
              <span class="pill" :class="riskPillClass(f.risk)">{{ f.risk }}</span>
              <span class="pill" :class="STATUS_PILL_CLASS[f.status]">{{ f.status }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- ── MAPA DE TRAZABILIDAD ── -->
      <template v-if="activeTab === 'mapa'">
        <div class="animate-in" style="height: calc(100vh - 220px); min-height: 540px;">
          <TraceabilityGraph :audit-id="auditId" />
        </div>
      </template>

      <!-- ── MADUREZ DOCUMENTAL ── -->
      <template v-if="activeTab === 'madurez'">
        <div class="animate-in" style="display:flex; flex-direction:column; gap:20px; margin-bottom: 30px;">
          <!-- Top Executive Dashboard -->
          <div class="maturity-dashboard-grid" style="display:grid; grid-template-columns: 1fr 340px; gap:20px;">
            <!-- Level Card -->
            <div class="card" style="padding: 24px; display: flex; flex-direction: column; justify-content: space-between; position: relative; overflow: hidden; background: linear-gradient(135deg, rgba(20, 24, 33, 0.6) 0%, rgba(13, 17, 23, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); backdrop-filter: blur(10px);">
              <!-- Glow background -->
              <div :style="{ background: `radial-gradient(circle, ${levelColor} 0%, transparent 70%)` }" style="position: absolute; top: -100px; right: -100px; width: 250px; height: 250px; opacity: 0.12; pointer-events: none; filter: blur(30px);" />
              
              <div>
                <div style="display:flex; align-items:center; gap:8px; margin-bottom: 8px;">
                  <AppIcon name="shield" :size="16" :style="{ color: levelColor }" />
                  <span class="mono text-xs text-muted" style="text-transform: uppercase; letter-spacing: 0.05em;">Evaluación Ejecutiva de Madurez</span>
                </div>
                <h2 style="font-size: 22px; font-weight: 700; margin-bottom: 12px; color: var(--text-1);">
                  {{ levelTextHeader }}
                </h2>
                <p style="font-size: 13px; line-height: 1.6; color: var(--text-2); margin-bottom: 20px; max-width: 90%;">
                  {{ levelDescription }}
                </p>
              </div>

              <!-- Metrics Summary inside the card -->
              <div style="display: flex; gap: 20px; align-items: center; border-top: 1px solid var(--border); padding-top: 18px; margin-top: auto;">
                <div style="flex: 1;">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span class="mono text-xs text-muted">Progreso General de Controles</span>
                    <span class="mono text-xs" :style="{ color: levelColor, fontWeight: 600 }">
                      {{ Math.round((localScores.policies + localScores.processes + localScores.traceability + localScores.culture) / 4) }}%
                    </span>
                  </div>
                  <div class="progress-bar" style="background: rgba(255, 255, 255, 0.05); height: 6px; border-radius: 4px;">
                    <div class="progress-fill" :style="{ width: Math.round((localScores.policies + localScores.processes + localScores.traceability + localScores.culture) / 4) + '%', background: levelColor }" style="transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), background 0.4s ease;" />
                  </div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0;">
                  <span class="mono text-2xl font-bold" :style="{ color: levelColor }">M{{ localLevel }}</span>
                  <span class="mono text-2xs text-muted" style="text-transform: uppercase;">PUNTAJE</span>
                </div>
              </div>
            </div>

            <!-- Radar Chart Card -->
            <div class="card" style="padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(13, 17, 23, 0.7); border: 1px solid var(--border); border-radius: 12px;">
              <span class="mono text-2xs text-muted" style="margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Perfil de Madurez Multidimensional</span>
              
              <div style="position: relative; width: 300px; height: 300px;">
                <svg width="300" height="300" :viewBox="`0 0 ${svgSize} ${svgSize}`" style="display: block; overflow: visible;">
                  <!-- 5 concentric diamond rings for levels 1-5 -->
                  <!-- Level 5 outermost ring highlighted in emerald with a separate styling -->
                  <polygon :points="`${center},${center - maxRadius} ${center + maxRadius},${center} ${center},${center + maxRadius} ${center - maxRadius},${center}`" fill="none" stroke="rgba(34, 197, 94, 0.45)" stroke-width="1.8" />
                  <polygon :points="`${center},${center - maxRadius * 0.8} ${center + maxRadius * 0.8},${center} ${center},${center + maxRadius * 0.8} ${center - maxRadius * 0.8},${center}`" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1" />
                  <polygon :points="`${center},${center - maxRadius * 0.6} ${center + maxRadius * 0.6},${center} ${center},${center + maxRadius * 0.6} ${center - maxRadius * 0.6},${center}`" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="1" stroke-dasharray="3,3" />
                  <polygon :points="`${center},${center - maxRadius * 0.4} ${center + maxRadius * 0.4},${center} ${center},${center + maxRadius * 0.4} ${center - maxRadius * 0.4},${center}`" fill="none" stroke="rgba(255,255,255,0.09)" stroke-width="1" />
                  <polygon :points="`${center},${center - maxRadius * 0.2} ${center + maxRadius * 0.2},${center} ${center},${center + maxRadius * 0.2} ${center - maxRadius * 0.2},${center}`" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="1" />

                  <!-- Cross Axes -->
                  <line :x1="center - maxRadius" :y1="center" :x2="center + maxRadius" :y2="center" stroke="rgba(255,255,255,0.08)" stroke-width="1" />
                  <line :x1="center" :y1="center - maxRadius" :x2="center" :y2="center + maxRadius" stroke="rgba(255,255,255,0.08)" stroke-width="1" />

                  <!-- Axis level indicator labels to explicitly separate and mark levels 1 to 5 -->
                  <text :x="center + 4" :y="center - maxRadius * 0.2 + 3" font-size="8" fill="rgba(255,255,255,0.3)" font-family="monospace">1</text>
                  <text :x="center + 4" :y="center - maxRadius * 0.4 + 3" font-size="8" fill="rgba(255,255,255,0.3)" font-family="monospace">2</text>
                  <text :x="center + 4" :y="center - maxRadius * 0.6 + 3" font-size="8" fill="rgba(255,255,255,0.3)" font-family="monospace">3</text>
                  <text :x="center + 4" :y="center - maxRadius * 0.8 + 3" font-size="8" fill="rgba(255,255,255,0.3)" font-family="monospace">4</text>
                  <text :x="center + 4" :y="center - maxRadius + 3" font-size="8.5" fill="rgba(34, 197, 94, 0.75)" font-family="monospace" font-weight="bold">5</text>

                  <!-- Center glow dot -->
                  <circle :cx="center" :cy="center" r="3" fill="var(--border)" opacity="0.3" />

                  <!-- Value polygon filled with gradient -->
                  <polygon
                    :points="`${getPoint(0, localScores.policies).x},${getPoint(0, localScores.policies).y} ${getPoint(1, localScores.processes).x},${getPoint(1, localScores.processes).y} ${getPoint(2, localScores.traceability).x},${getPoint(2, localScores.traceability).y} ${getPoint(3, localScores.culture).x},${getPoint(3, localScores.culture).y}`"
                    fill="url(#radarGradient)"
                    :stroke="levelColor"
                    stroke-width="1.8"
                    stroke-linejoin="round"
                    style="transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);"
                  />

                  <!-- Vertex dots -->
                  <circle :cx="getPoint(0, localScores.policies).x" :cy="getPoint(0, localScores.policies).y" r="4" :fill="levelColor" style="transition: all 0.3s;" />
                  <circle :cx="getPoint(1, localScores.processes).x" :cy="getPoint(1, localScores.processes).y" r="4" :fill="levelColor" style="transition: all 0.3s;" />
                  <circle :cx="getPoint(2, localScores.traceability).x" :cy="getPoint(2, localScores.traceability).y" r="4" :fill="levelColor" style="transition: all 0.3s;" />
                  <circle :cx="getPoint(3, localScores.culture).x" :cy="getPoint(3, localScores.culture).y" r="4" :fill="levelColor" style="transition: all 0.3s;" />

                  <!-- Text Labels (positioned with generous padding to avoid clipping) -->
                  <text :x="center" :y="center - maxRadius - 12" text-anchor="middle" font-size="10" font-weight="600" fill="var(--text-2)" font-family="monospace" letter-spacing="0.05em">POLÍTICAS</text>
                  <text :x="center + maxRadius + 10" :y="center + 4" text-anchor="start" font-size="10" font-weight="600" fill="var(--text-2)" font-family="monospace" letter-spacing="0.05em">PROCESOS</text>
                  <text :x="center" :y="center + maxRadius + 18" text-anchor="middle" font-size="10" font-weight="600" fill="var(--text-2)" font-family="monospace" letter-spacing="0.05em">TRAZABILIDAD</text>
                  <text :x="center - maxRadius - 10" :y="center + 4" text-anchor="end" font-size="10" font-weight="600" fill="var(--text-2)" font-family="monospace" letter-spacing="0.05em">CULTURA</text>

                  <defs>
                    <radialGradient id="radarGradient" cx="50%" cy="50%" r="50%">
                      <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.05" />
                      <stop offset="100%" :stop-color="levelColor" stop-opacity="0.25" />
                    </radialGradient>
                  </defs>
                </svg>
              </div>
            </div>
          </div>

          <!-- Bottom Grid: Checklist (Left) & Gap Analysis (Right) -->
          <div style="display:grid; grid-template-columns: 1fr 340px; gap:20px;">
            <!-- Checklist Card -->
            <div class="card" style="padding: 20px; display: flex; flex-direction: column; background: rgba(13, 17, 23, 0.6); border: 1px solid var(--border); border-radius: 12px;">
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 20px; flex-wrap: wrap; gap:10px;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <AppIcon name="list" :size="13" style="color:var(--text-2)" />
                  <span style="font-size:12px; font-weight:600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-2);">Checklist de Controles de Madurez</span>
                </div>
                <button 
                  class="btn btn-primary btn-xs" 
                  :disabled="!hasChanges || isSaving" 
                  @click="saveMaturity"
                  style="padding: 6px 12px; font-size:11px;"
                >
                  <div v-if="isSaving" class="spinner" style="width:10px; height:10px; margin-right: 5px;" />
                  <AppIcon v-else name="check" :size="10" style="margin-right: 5px;" />
                  {{ isSaving ? 'Guardando...' : (hasChanges ? 'Guardar evaluación' : 'Evaluación guardada') }}
                </button>
              </div>

              <!-- Grouped list of toggles -->
              <div style="display:flex; flex-direction:column; gap:22px;">
                
                <!-- Nivel 1 -->
                <div>
                  <div style="display:flex; align-items:center; gap:8px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 6px; margin-bottom: 10px;">
                    <span class="pill pill-pending" style="font-size: 10px; font-weight:600; padding: 2px 6px;">L1</span>
                    <span style="font-size: 12px; font-weight:600; color: var(--text-1);">Nivel Inicial: Acumulación Digital</span>
                  </div>
                  <div style="display:flex; flex-direction:column; gap:8px;">
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Repositorios Digitales</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Existen repositorios o directorios para guardar documentos.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l1_repositorios" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="display:flex; align-items:center; gap:6px;">
                          <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Ausencia de Políticas (Riesgo)</div>
                          <span class="pill pill-extreme" style="font-size:8px; padding: 1px 4px; font-weight:600;">RIESGO</span>
                        </div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">La organización opera sin políticas documentales claras.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l1_sin_politicas" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                  </div>
                </div>

                <!-- Nivel 2 -->
                <div>
                  <div style="display:flex; align-items:center; gap:8px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 6px; margin-bottom: 10px;">
                    <span class="pill pill-processing" style="font-size: 10px; font-weight:600; padding: 2px 6px;">L2</span>
                    <span style="font-size: 12px; font-weight:600; color: var(--text-1);">Nivel Controlado: Normas Básicas</span>
                  </div>
                  <div style="display:flex; flex-direction:column; gap:8px;">
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Cuadro de Clasificación Aprobado</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Existe una codificación para clasificar la información corporativa.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l2_cuadro" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Calendarios de Conservación</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Plazos y criterios archivísticos de retención vigentes.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l2_calendario" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="display:flex; align-items:center; gap:6px;">
                          <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Aplicación Desigual (Riesgo)</div>
                          <span class="pill pill-extreme" style="font-size:8px; padding: 1px 4px; font-weight:600;">RIESGO</span>
                        </div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Las normas se aplican de forma dispar según cada unidad o área.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l2_desigual" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                  </div>
                </div>

                <!-- Nivel 3 -->
                <div>
                  <div style="display:flex; align-items:center; gap:8px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 6px; margin-bottom: 10px;">
                    <span class="pill pill-review" style="font-size: 10px; font-weight:600; padding: 2px 6px; background: #3b82f6 !important; color:#fff;">L3</span>
                    <span style="font-size: 12px; font-weight:600; color: var(--text-1);">Nivel Integrado: Procesos Alineados</span>
                  </div>
                  <div style="display:flex; flex-direction:column; gap:8px;">
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Procesos Integrados</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Gestión de información corporativa incorporada en la operativa formal.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l3_procesos" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Roles Multidisciplinarios Claros</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Responsables funcionales, técnicos e informáticos designados formalmente.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l3_roles" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Trazabilidad Real y Ciclo de Vida</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Control total sobre la creación, modificación, y borrado de documentos.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l3_trazabilidad" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                  </div>
                </div>

                <!-- Nivel 4: Gobierno de la Información -->
                <div>
                  <div style="display:flex; align-items:center; gap:8px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 6px; margin-bottom: 10px;">
                    <span class="pill" style="font-size: 10px; font-weight:600; padding: 2px 6px; background: #a855f7; color:#fff; border:none;">L4</span>
                    <span style="font-size: 12px; font-weight:600; color: var(--text-1);">Nivel Estratégico: Gobierno de la Información</span>
                  </div>
                  <div style="display:flex; flex-direction:column; gap:8px;">
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Gobernanza de Información Activa</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">La dirección gestiona la información como activo de valor estratégico y conoce los riesgos.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l4_riesgos" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Gestión de Activos Documentales</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Inventario y valoración de los documentos como activos organizacionales protegidos.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l4_activos" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Coordinación Interdepartamental</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Coordinación formal y regular entre IT, área Jurídica, Compliance y Negocio.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l4_coordinacion" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                  </div>
                </div>

                <!-- Nivel 5: Cultura Documental y Mejora Continua -->
                <div>
                  <div style="display:flex; align-items:center; gap:8px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 6px; margin-bottom: 10px;">
                    <span class="pill" style="font-size: 10px; font-weight:600; padding: 2px 6px; background: hsl(142, 80%, 45%); color:#fff; border:none;">L5</span>
                    <span style="font-size: 12px; font-weight:600; color: var(--text-1);">Nivel Optimizado: Cultura Documental</span>
                  </div>
                  <div style="display:flex; flex-direction:column; gap:8px;">
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Cultura Documental Impregnada</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">La buena gestión documental es parte innata de las tareas de cada empleado.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l5_cultura" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Mejora Continua y ASFI Ready</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">La organización anticipa litigios, auditorías del regulador, y riesgos normativos.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l5_mejora" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                    <label class="maturity-toggle-row" style="display:flex; align-items:flex-start; justify-content:space-between; gap:15px; padding: 6px 8px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
                      <div style="flex:1;">
                        <div style="font-size: 12px; font-weight:500; color: var(--text-1);">Inspección y Anticipación Regulatoria</div>
                        <div style="font-size: 10.5px; color: var(--text-3); margin-top:2px;">Procesos proactivos de revisión que previenen incidentes antes de inspecciones.</div>
                      </div>
                      <input type="checkbox" v-model="localChecklist.l5_inspeccion" class="form-checkbox" style="margin-top:3px;" />
                    </label>
                  </div>
                </div>

              </div>
            </div>

            <!-- Gap Analysis -->
            <div style="display:flex; flex-direction:column; gap:16px;">
              
              <!-- Puntos fuertes -->
              <div class="card" style="padding: 16px; background: rgba(34, 197, 94, 0.03); border: 1px solid rgba(34, 197, 94, 0.15); border-radius: 12px;">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom: 10px;">
                  <AppIcon name="check-circle" :size="13" style="color:#22c55e" />
                  <span style="font-size:11px; font-weight:600; text-transform: uppercase; color:#22c55e;">Puntos Fuertes</span>
                </div>
                <div v-if="localGapAnalysis.strengths.length === 0" class="mono text-2xs text-muted">
                  No se han identificado puntos fuertes significativos todavía.
                </div>
                <ul v-else style="margin:0; padding-left:14px; display:flex; flex-direction:column; gap:8px;">
                  <li v-for="s in localGapAnalysis.strengths" :key="s" style="font-size:11px; line-height:1.5; color: var(--text-2);">
                    {{ s }}
                  </li>
                </ul>
              </div>

              <!-- Debilidades / Brechas -->
              <div class="card" style="padding: 16px; background: rgba(239, 68, 68, 0.03); border: 1px solid rgba(239, 68, 68, 0.15); border-radius: 12px;">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom: 10px;">
                  <AppIcon name="alert-triangle" :size="13" style="color:#ef4444" />
                  <span style="font-size:11px; font-weight:600; text-transform: uppercase; color:#ef4444;">Brechas Clave</span>
                </div>
                <div v-if="localGapAnalysis.weaknesses.length === 0" class="mono text-2xs" style="color: #22c55e;">
                  ¡Sin brechas pendientes detectadas! Máxima madurez asegurada.
                </div>
                <ul v-else style="margin:0; padding-left:14px; display:flex; flex-direction:column; gap:8px;">
                  <li v-for="w in localGapAnalysis.weaknesses" :key="w" style="font-size:11px; line-height:1.5; color: var(--text-2);">
                    {{ w }}
                  </li>
                </ul>
              </div>

              <!-- Plan de Acción -->
              <div class="card" style="padding: 16px; background: rgba(59, 130, 246, 0.03); border: 1px solid rgba(59, 130, 246, 0.15); border-radius: 12px;">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom: 10px;">
                  <AppIcon name="zap" :size="13" style="color:#3b82f6" />
                  <span style="font-size:11px; font-weight:600; text-transform: uppercase; color:#3b82f6;">Plan de Acción (Roadmap)</span>
                </div>
                <div v-if="localGapAnalysis.roadmap.length === 0" class="mono text-2xs text-muted">
                  Organización optimizada; no se requiere plan de acción adicional inmediato.
                </div>
                <ul v-else style="margin:0; padding-left:14px; display:flex; flex-direction:column; gap:8px;">
                  <li v-for="r in localGapAnalysis.roadmap" :key="r" style="font-size:11px; line-height:1.5; color: var(--text-2); font-weight:500;">
                    {{ r }}
                  </li>
                </ul>
              </div>

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
                <span class="pill pill-pending">{{ r.format.toUpperCase() }}</span>
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
              <button class="btn btn-ghost btn-sm" style="margin-top:8px;" @click="downloadGeneratedReport(r)">
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
    <ChatBot :audit-id="auditId" />
  </AppShell>
</template>
