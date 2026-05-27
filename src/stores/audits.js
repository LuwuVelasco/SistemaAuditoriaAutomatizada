import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { mockAudits, mockDocuments, mockFindings } from '../data/mock'
import * as remote from '../api/index'

const USE_API = !!import.meta.env.VITE_FIREBASE_API_KEY
  && import.meta.env.VITE_FIREBASE_API_KEY !== 'your_firebase_api_key'

export const useAuditsStore = defineStore('audits', () => {
  const audits    = ref(USE_API ? [] : JSON.parse(JSON.stringify(mockAudits)))
  const documents = ref(USE_API ? {} : JSON.parse(JSON.stringify(mockDocuments)))
  const findings  = ref(USE_API ? {} : JSON.parse(JSON.stringify(mockFindings)))
  const currentAuditId = ref(null)
  const loading = ref(false)

  const currentAudit     = computed(() => audits.value.find(a => a.id === currentAuditId.value) || null)
  const currentDocuments = computed(() => documents.value[currentAuditId.value] || [])
  const currentFindings  = computed(() => findings.value[currentAuditId.value] || [])

  // ── Carga desde backend ───────────────────────────────────────────────────────

  async function loadAudits() {
    if (!USE_API) return
    loading.value = true
    try {
      const data = await remote.getAudits()
      audits.value = (data || []).map(mapAudit)
    } catch (e) {
      console.error('Error cargando auditorías:', e)
    } finally {
      loading.value = false
    }
  }

  async function loadDocuments(auditId) {
    if (!USE_API) return
    try {
      const data = await remote.getDocuments(auditId)
      documents.value[auditId] = (data || []).map(mapDocument)
    } catch (e) {
      console.error('Error cargando documentos:', e)
    }
  }

  async function loadFindings(auditId) {
    if (!USE_API) return
    try {
      const data = await remote.getFindings(auditId)
      findings.value[auditId] = (data || []).map(mapFinding)
    } catch (e) {
      console.error('Error cargando hallazgos:', e)
    }
  }

  // ── Acciones del store ────────────────────────────────────────────────────────

  async function setCurrentAudit(id) {
    currentAuditId.value = id
    if (USE_API && id) {
      await Promise.all([loadDocuments(id), loadFindings(id)])
    }
  }

  async function createAudit(data) {
    if (!USE_API) {
      const id = 'aud-' + Date.now()
      const audit = {
        id, ...data,
        status: 'Pendiente', progress: 0,
        findings: 0, pendingFindings: 0, documents: 0,
        createdAt: new Date().toISOString().split('T')[0],
        ownerId: 'current-user',
      }
      audits.value.unshift(audit)
      documents.value[id] = []
      findings.value[id] = []
      return id
    }
    const created = await remote.createAudit(data)
    const audit = mapAudit(created)
    audits.value.unshift(audit)
    documents.value[audit.id] = []
    findings.value[audit.id] = []
    return audit.id
  }

  async function addDocument(auditId, file) {
    if (!USE_API) {
      const ext = file.name.split('.').pop().toLowerCase()
      const doc = {
        id: 'doc-' + Date.now(), name: file.name, type: ext,
        size: formatSize(file.size), status: 'queued',
        chunks: 0, sha256: null,
        uploadedAt: new Date().toISOString().split('T')[0],
      }
      if (!documents.value[auditId]) documents.value[auditId] = []
      documents.value[auditId].push(doc)
      const audit = audits.value.find(a => a.id === auditId)
      if (audit) audit.documents++
      setTimeout(() => {
        const d = documents.value[auditId]?.find(d => d.id === doc.id)
        if (d) d.status = 'indexing'
      }, 800)
      setTimeout(() => {
        const d = documents.value[auditId]?.find(d => d.id === doc.id)
        if (d) { d.status = 'ready'; d.chunks = Math.floor(Math.random() * 100) + 20 }
      }, 3000)
      return doc
    }

    // Optimista: mostrar inmediatamente con estado indexing
    const tempId = 'temp-' + Date.now()
    const tempDoc = {
      id: tempId, name: file.name,
      type: file.name.split('.').pop().toLowerCase(),
      size: formatSize(file.size), status: 'indexing',
      chunks: 0, sha256: null,
      uploadedAt: new Date().toISOString().split('T')[0],
    }
    if (!documents.value[auditId]) documents.value[auditId] = []
    documents.value[auditId].push(tempDoc)

    try {
      const uploaded = await remote.uploadDocument(auditId, file)
      const doc = mapDocument(uploaded)
      doc.status = 'ready'
      const idx = documents.value[auditId].findIndex(d => d.id === tempId)
      if (idx >= 0) documents.value[auditId][idx] = doc
      const audit = audits.value.find(a => a.id === auditId)
      if (audit) audit.documents++
      return doc
    } catch (e) {
      documents.value[auditId] = documents.value[auditId].filter(d => d.id !== tempId)
      console.error('Error subiendo documento:', e)
      throw e
    }
  }

  function addFindings(auditId, newFindings) {
    if (!findings.value[auditId]) findings.value[auditId] = []
    const existing = findings.value[auditId]
    const nextIdx = existing.length + 1
    newFindings.forEach((f, i) => {
      const id = `HLZ-${String(nextIdx + i).padStart(3, '0')}`
      existing.push({
        id, auditId, ...f,
        status: 'Pendiente', evidence: [],
        detectedBy: 'COSFI-AI',
        createdAt: new Date().toISOString().split('T')[0],
      })
    })
    const audit = audits.value.find(a => a.id === auditId)
    if (audit) {
      audit.findings = findings.value[auditId].length
      audit.pendingFindings = findings.value[auditId].filter(f => f.status === 'Pendiente').length
      audit.status = 'En revisión'
      audit.progress = 100
    }
  }

  async function updateFinding(auditId, findingId, data) {
    if (USE_API) {
      try { await remote.updateFinding(auditId, findingId, data) } catch (e) { console.error('Error actualizando hallazgo:', e) }
    }
    const list = findings.value[auditId]
    if (!list) return
    const idx = list.findIndex(f => f.id === findingId)
    if (idx >= 0) list[idx] = { ...list[idx], ...data }
    const audit = audits.value.find(a => a.id === auditId)
    if (audit) audit.pendingFindings = (findings.value[auditId] || []).filter(f => f.status === 'Pendiente').length
  }

  function getFinding(auditId, findingId) {
    return (findings.value[auditId] || []).find(f => f.id === findingId) || null
  }

  function setAuditProgress(auditId, progress, status) {
    const audit = audits.value.find(a => a.id === auditId)
    if (audit) { audit.progress = progress; if (status) audit.status = status }
  }

  return {
    audits, documents, findings, loading,
    currentAuditId, currentAudit, currentDocuments, currentFindings,
    setCurrentAudit, createAudit, addDocument, addFindings, updateFinding, getFinding, setAuditProgress,
    loadAudits,
  }
})

// ── Mappers frontend ↔ backend ────────────────────────────────────────────────

function mapAudit(a) {
  return {
    id:              a.id,
    entity:          a.entity,
    type:            a.type,
    city:            a.city,
    period:          a.period,
    status:          a.status,
    progress:        a.progress ?? 0,
    frameworks:      a.frameworks ?? [],
    findings:        a.findingsCount ?? 0,
    pendingFindings: a.pendingFindings ?? 0,
    documents:       a.documentsCount ?? 0,
    ownerId:         a.ownerId,
    createdAt:       (a.createdAt || '').split('T')[0],
  }
}

function mapDocument(d) {
  return {
    id:         d.id,
    name:       d.name,
    type:       d.type || (d.name || '').split('.').pop(),
    size:       d.size || formatSize(0),
    status:     d.status || 'ready',
    chunks:     d.chunks ?? 0,
    sha256:     d.sha256 || null,
    uploadedAt: (d.uploadedAt || '').split('T')[0],
  }
}

function mapFinding(f) {
  return {
    id:             f.id,
    auditId:        f.auditId,
    title:          f.title,
    description:    f.description,
    recommendation: f.recommendation,
    risk:           f.risk,
    impact:         f.impact,
    probability:    f.probability,
    status:         f.status,
    confidence:     f.confidence,
    cobitRefs:      Array.isArray(f.cobitRef) ? f.cobitRef : (f.cobitRef ? [f.cobitRef] : []),
    cosoRefs:       Array.isArray(f.cosoRef)  ? f.cosoRef  : (f.cosoRef  ? [f.cosoRef]  : []),
    rgsiRefs:       Array.isArray(f.rgsiRef)  ? f.rgsiRef  : (f.rgsiRef  ? [f.rgsiRef]  : []),
    cobitRef:       Array.isArray(f.cobitRef) ? (f.cobitRef[0] || null) : (f.cobitRef || null),
    cosoRef:        Array.isArray(f.cosoRef)  ? (f.cosoRef[0]  || null) : (f.cosoRef  || null),
    rgsiRef:        Array.isArray(f.rgsiRef)  ? (f.rgsiRef[0]  || null) : (f.rgsiRef  || null),
    evidence:       f.evidence || [],
    detectedBy:     f.detectedBy || 'COSFI-AI',
    createdAt:      (f.createdAt || '').split('T')[0],
  }
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
