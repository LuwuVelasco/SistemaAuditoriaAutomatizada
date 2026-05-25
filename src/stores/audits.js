import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { mockAudits, mockDocuments, mockFindings, RISK_LEVELS } from '../data/mock'

// MVP: datos en memoria. Reemplazar con Firestore en producción.
export const useAuditsStore = defineStore('audits', () => {
  const audits = ref(JSON.parse(JSON.stringify(mockAudits)))
  const documents = ref(JSON.parse(JSON.stringify(mockDocuments)))
  const findings = ref(JSON.parse(JSON.stringify(mockFindings)))
  const currentAuditId = ref(null)

  const currentAudit = computed(() => audits.value.find(a => a.id === currentAuditId.value) || null)
  const currentDocuments = computed(() => documents.value[currentAuditId.value] || [])
  const currentFindings = computed(() => findings.value[currentAuditId.value] || [])

  function setCurrentAudit(id) { currentAuditId.value = id }

  function createAudit(data) {
    const id = 'aud-' + Date.now()
    const audit = {
      id,
      ...data,
      status: 'Pendiente',
      progress: 0,
      findings: 0,
      pendingFindings: 0,
      documents: 0,
      createdAt: new Date().toISOString().split('T')[0],
      ownerId: 'current-user'
    }
    audits.value.unshift(audit)
    documents.value[id] = []
    findings.value[id] = []
    return id
  }

  function addDocument(auditId, file) {
    const ext = file.name.split('.').pop().toLowerCase()
    const doc = {
      id: 'doc-' + Date.now(),
      name: file.name,
      type: ext,
      size: formatSize(file.size),
      status: 'queued',
      chunks: 0,
      sha256: null,
      uploadedAt: new Date().toISOString().split('T')[0],
      _file: file
    }
    if (!documents.value[auditId]) documents.value[auditId] = []
    documents.value[auditId].push(doc)
    const audit = audits.value.find(a => a.id === auditId)
    if (audit) audit.documents++
    // Simular indexación
    setTimeout(() => {
      const d = documents.value[auditId]?.find(d => d.id === doc.id)
      if (d) { d.status = 'indexing' }
    }, 800)
    setTimeout(() => {
      const d = documents.value[auditId]?.find(d => d.id === doc.id)
      if (d) { d.status = 'ready'; d.chunks = Math.floor(Math.random() * 100) + 20 }
    }, 3000)
    return doc
  }

  function addFindings(auditId, newFindings) {
    if (!findings.value[auditId]) findings.value[auditId] = []
    const existing = findings.value[auditId]
    const nextIdx = existing.length + 1
    newFindings.forEach((f, i) => {
      const id = `HLZ-${String(nextIdx + i).padStart(3, '0')}`
      existing.push({
        id,
        auditId,
        ...f,
        status: 'Pendiente',
        evidence: [],
        detectedBy: 'COSFI-AI',
        createdAt: new Date().toISOString().split('T')[0]
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

  function updateFinding(auditId, findingId, data) {
    const list = findings.value[auditId]
    if (!list) return
    const idx = list.findIndex(f => f.id === findingId)
    if (idx >= 0) list[idx] = { ...list[idx], ...data }
    // Actualizar contadores
    const audit = audits.value.find(a => a.id === auditId)
    if (audit) {
      audit.pendingFindings = (findings.value[auditId] || []).filter(f => f.status === 'Pendiente').length
    }
  }

  function getFinding(auditId, findingId) {
    return (findings.value[auditId] || []).find(f => f.id === findingId) || null
  }

  function setAuditProgress(auditId, progress, status) {
    const audit = audits.value.find(a => a.id === auditId)
    if (audit) { audit.progress = progress; if (status) audit.status = status }
  }

  return {
    audits, documents, findings,
    currentAuditId, currentAudit, currentDocuments, currentFindings,
    setCurrentAudit, createAudit, addDocument, addFindings, updateFinding, getFinding, setAuditProgress
  }
})

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
