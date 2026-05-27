<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuditsStore } from '@/stores/audits'
import AppShell from '@/components/layout/AppShell.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { RISK_LEVELS } from '@/data/mock'

const route  = useRoute()
const router = useRouter()
const store  = useAuditsStore()

const auditId   = computed(() => route.params.auditId)
const findingId = computed(() => route.params.findingId)

const raw = computed(() => store.getFinding(auditId.value, findingId.value))
const audit = computed(() => store.audits.find(a => a.id === auditId.value))

// Local editable copy
const finding = ref(null)

onMounted(() => {
  if (raw.value) finding.value = JSON.parse(JSON.stringify(raw.value))
})

function save() {
  store.updateFinding(auditId.value, findingId.value, finding.value)
  feedback.value = { type: 'saved', msg: 'Cambios guardados.' }
  setTimeout(() => feedback.value = null, 2500)
}

function approve() {
  finding.value.status = 'Aprobado'
  store.updateFinding(auditId.value, findingId.value, { ...finding.value, status: 'Aprobado' })
  feedback.value = { type: 'approved', msg: 'Hallazgo aprobado.' }
  setTimeout(() => { feedback.value = null; router.push(`/workspace/${auditId.value}?tab=hallazgos`) }, 1500)
}

function reject() {
  finding.value.status = 'Rechazado'
  store.updateFinding(auditId.value, findingId.value, { ...finding.value, status: 'Rechazado' })
  feedback.value = { type: 'rejected', msg: 'Hallazgo rechazado.' }
  setTimeout(() => { feedback.value = null; router.push(`/workspace/${auditId.value}?tab=hallazgos`) }, 1500)
}

const feedback = ref(null)

function setRisk(r) { finding.value.risk = r }
function setImpact(v) { finding.value.impact = v }
function setProbability(v) { finding.value.probability = v }

function riskPillClass(r) {
  return { Extremo: 'pill-extreme', Alto: 'pill-high', Medio: 'pill-medium', Bajo: 'pill-low', Oportunidad: 'pill-opp' }[r] || ''
}

function riskBtnColor(r) {
  const map = { Extremo: 'var(--risk-x)', Alto: 'var(--risk-h)', Medio: 'var(--risk-m)', Bajo: 'var(--risk-l)', Oportunidad: 'var(--risk-o)' }
  return map[r] || 'var(--text-2)'
}

function confidClass(c) {
  return c >= 0.8 ? 'high' : ''
}

function onTitleBlur(e) { finding.value.title = e.target.innerText.trim() }
function onDescBlur(e) { finding.value.description = e.target.innerText.trim() }
function onRecBlur(e) { finding.value.recommendation = e.target.innerText.trim() }

// Related findings (same COBIT domain)
const relatedFindings = computed(() => {
  if (!finding.value?.cobitRef?.domain) return []
  return (store.findings[auditId.value] || [])
    .filter(f => f.id !== findingId.value && f.cobitRef?.domain === finding.value.cobitRef?.domain)
    .slice(0, 3)
})
</script>

<template>
  <AppShell>
    <!-- Topbar -->
    <div class="topbar">
      <button class="btn btn-ghost btn-icon btn-sm" @click="router.push(`/workspace/${auditId}?tab=hallazgos`)">
        <AppIcon name="arrow-left" :size="14" />
      </button>
      <span class="topbar-crumb mono text-xs">{{ audit?.entity }}</span>
      <AppIcon name="chevron-right" :size="11" style="color:var(--text-3)" />
      <span class="topbar-crumb mono text-xs">Hallazgos</span>
      <AppIcon name="chevron-right" :size="11" style="color:var(--text-3)" />
      <span class="topbar-title mono text-sm">{{ findingId }}</span>
    </div>

    <div v-if="!finding" class="empty-state">
      <h3>Hallazgo no encontrado</h3>
    </div>

    <div v-else class="finding-detail-layout">
      <!-- ── LEFT COLUMN ── -->
      <div class="finding-left">

        <!-- Related documents -->
        <div>
          <div class="section-label">Documentos relacionados</div>
          <div v-if="finding.evidence?.length">
            <div
              v-for="(ev, i) in finding.evidence"
              :key="i"
              class="card"
              style="padding:10px 12px;margin-bottom:6px;"
            >
              <div class="file-icon" style="display:inline-flex;margin-bottom:6px;" :class="ev.docName?.endsWith('.pdf')?'file-ext-pdf':ev.docName?.endsWith('.xlsx')?'file-ext-xlsx':'file-ext-docx'">
                {{ ev.docName?.split('.').pop() || 'doc' }}
              </div>
              <div style="font-size:12px;font-weight:500;margin-bottom:2px;">{{ ev.docName }}</div>
              <div class="mono text-xs text-muted">Pág. {{ ev.page }} · {{ ev.paragraph }}</div>
            </div>
          </div>
          <div v-else class="mono text-xs text-muted">Sin evidencia vinculada.</div>
        </div>

        <!-- AI Quote -->
        <div v-if="finding.quote">
          <div class="section-label">Cita extraída por IA</div>
          <blockquote class="evidence">{{ finding.quote }}</blockquote>
        </div>

        <!-- Related findings -->
        <div>
          <div class="section-label">Hallazgos relacionados</div>
          <div v-if="relatedFindings.length">
            <div
              v-for="rf in relatedFindings"
              :key="rf.id"
              class="card"
              style="padding:10px 12px;margin-bottom:6px;cursor:pointer;"
              @click="router.push(`/workspace/${auditId}/hallazgo/${rf.id}`)"
            >
              <div class="finding-id">{{ rf.id }}</div>
              <div style="font-size:12px;margin-bottom:4px;">{{ rf.title }}</div>
              <span class="pill" :class="riskPillClass(rf.risk)">{{ rf.risk }}</span>
            </div>
          </div>
          <div v-else class="mono text-xs text-muted">Sin hallazgos relacionados.</div>
        </div>
      </div>

      <!-- ── CENTER COLUMN ── -->
      <div class="finding-center">

        <!-- Header: ID + timestamp + confidence -->
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
          <span class="mono text-xs text-muted">{{ finding.id }}</span>
          <span class="mono text-xs text-muted">·</span>
          <span class="mono text-xs text-muted">{{ finding.createdAt }}</span>
          <span class="mono text-xs text-muted">·</span>
          <span class="confid-badge" :class="confidClass(finding.confidence)">
            <AppIcon name="cpu" :size="9" />
            IA {{ Math.round((finding.confidence || 0.8) * 100) }}%
          </span>
          <span class="pill" :class="riskPillClass(finding.risk)" style="margin-left:auto;">{{ finding.risk }}</span>
        </div>

        <!-- Title (editable) -->
        <div
          contenteditable
          class="finding-title-editable"
          :data-placeholder="finding.title"
          @blur="onTitleBlur"
          style="font-size:18px;font-weight:600;line-height:1.3;margin-bottom:20px;padding:4px 6px;border-radius:3px;"
        >{{ finding.title }}</div>

        <!-- Risk selector -->
        <div style="margin-bottom:20px;">
          <div class="form-label" style="margin-bottom:8px;">Nivel de riesgo</div>
          <div class="risk-pills">
            <button
              v-for="r in RISK_LEVELS"
              :key="r"
              class="risk-pill-btn"
              :class="{ selected: finding.risk === r }"
              :style="{
                color: riskBtnColor(r),
                background: finding.risk === r ? `color-mix(in srgb, ${riskBtnColor(r)} 10%, transparent)` : 'var(--surface-2)',
                borderColor: finding.risk === r ? riskBtnColor(r) : 'var(--border-2)'
              }"
              @click="setRisk(r)"
            >
              <span v-if="finding.risk === r" style="width:5px;height:5px;border-radius:50%;background:currentColor;display:inline-block;margin-right:3px;box-shadow:0 0 6px currentColor;" />
              {{ r }}
            </button>
          </div>
        </div>

        <!-- Impact / Probability -->
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
          <div>
            <div class="form-label" style="margin-bottom:8px;">
              Impacto
              <span class="mono" style="color:var(--text);margin-left:6px;">{{ finding.impact }}/5</span>
            </div>
            <div class="score-bars">
              <div
                v-for="v in 5"
                :key="v"
                class="score-bar"
                :class="{ active: v <= finding.impact }"
                @click="setImpact(v)"
              />
            </div>
          </div>
          <div>
            <div class="form-label" style="margin-bottom:8px;">
              Probabilidad
              <span class="mono" style="color:var(--text);margin-left:6px;">{{ finding.probability }}/5</span>
            </div>
            <div class="score-bars">
              <div
                v-for="v in 5"
                :key="v"
                class="score-bar"
                :class="{ active: v <= finding.probability }"
                @click="setProbability(v)"
              />
            </div>
          </div>
        </div>

        <div class="divider" />

        <!-- Description (editable) -->
        <div style="margin-bottom:20px;">
          <div class="form-label" style="margin-bottom:6px;">Descripción</div>
          <div
            contenteditable
            @blur="onDescBlur"
            style="font-size:13px;line-height:1.7;padding:8px 10px;border-radius:3px;color:var(--text);"
          >{{ finding.description }}</div>
        </div>

        <!-- Normative mapping -->
        <div style="margin-bottom:20px;">
          <div class="form-label" style="margin-bottom:8px;">Mapeo normativo cruzado</div>

          <div v-if="finding.cobitRef" class="norm-row">
            <div class="norm-framework norm-cobit">COBIT</div>
            <div class="norm-content">
              <div class="norm-code" style="color:#a78bfa;">{{ finding.cobitRef.code }}</div>
              <div class="norm-title">{{ finding.cobitRef.title }}</div>
              <div class="mono text-xs" style="color:#a78bfa;margin-top:2px;">Dominio {{ finding.cobitRef.domain }}</div>
            </div>
          </div>

          <div v-if="finding.cosoRef" class="norm-row">
            <div class="norm-framework norm-coso">COSO</div>
            <div class="norm-content">
              <div class="norm-code" style="color:#fb923c;">{{ finding.cosoRef.code }}</div>
              <div class="norm-title">{{ finding.cosoRef.title }}</div>
              <div class="mono text-xs" style="color:#fb923c;margin-top:2px;">{{ finding.cosoRef.component }}</div>
            </div>
          </div>

          <div v-if="finding.rgsiRef" class="norm-row">
            <div class="norm-framework norm-rgsi">RGSI</div>
            <div class="norm-content">
              <div class="norm-code" style="color:var(--accent);">{{ finding.rgsiRef.code }}</div>
              <div class="norm-title">{{ finding.rgsiRef.title }}</div>
              <div class="mono text-xs" style="color:var(--accent);margin-top:2px;">{{ finding.rgsiRef.section }}</div>
            </div>
          </div>
        </div>

        <div class="divider" />

        <!-- Recommendation (editable) -->
        <div style="margin-bottom:24px;">
          <div class="form-label" style="margin-bottom:6px;">Recomendación</div>
          <div
            contenteditable
            @blur="onRecBlur"
            style="font-size:13px;line-height:1.7;padding:8px 10px;border-radius:3px;color:var(--text);"
          >{{ finding.recommendation }}</div>
        </div>

        <!-- Feedback message -->
        <Transition name="fade">
          <div v-if="feedback" class="animate-in" style="display:flex;align-items:center;gap:8px;border-radius:3px;padding:10px 14px;margin-bottom:16px;font-size:12px;"
            :style="{
              background: feedback.type==='approved' ? 'rgba(34,197,94,0.08)' : feedback.type==='rejected' ? 'rgba(239,68,68,0.08)' : 'var(--accent-dim)',
              border: `1px solid ${feedback.type==='approved' ? 'rgba(34,197,94,0.2)' : feedback.type==='rejected' ? 'rgba(239,68,68,0.2)' : 'var(--border-accent)'}`,
              color: feedback.type==='approved' ? 'var(--risk-l)' : feedback.type==='rejected' ? 'var(--risk-x)' : 'var(--accent)'
            }"
          >
            <AppIcon :name="feedback.type==='rejected'?'x-circle':feedback.type==='approved'?'check-circle':'info'" :size="13" />
            {{ feedback.msg }}
          </div>
        </Transition>
      </div>
    </div>

    <!-- Action bar -->
    <div v-if="finding" class="action-bar">
      <div v-if="finding.status === 'Pendiente'" >
        <button class="btn btn-primary" @click="approve">
          <AppIcon name="check" :size="13" />
          Aprobar
        </button>
        <button class="btn btn-outline" @click="save">
          Guardar
        </button>
        <button class="btn btn-danger" @click="reject">
          <AppIcon name="x" :size="13" />
          Rechazar
        </button>
      </div>
      <div style="margin-left:auto;">
        <button class="btn btn-ghost">
          <AppIcon name="download" :size="13" />
          Exportar ficha
        </button>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.finding-title-editable:empty::before {
  content: attr(data-placeholder);
  color: var(--text-3);
}
</style>
