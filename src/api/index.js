import { api, uploadFile } from './client'

// ── Audits ────────────────────────────────────────────────────────────────────
export const getAudits    = ()         => api.get('/audits')
export const createAudit  = (data)     => api.post('/audits', data)
export const updateAudit  = (id, data) => api.patch(`/audits/${id}`, data)
export const deleteAudit  = (id)       => api.delete(`/audits/${id}`)
export const analyzeAudit = (id)       => api.post(`/audits/${id}/analyze`)

// ── Documents ─────────────────────────────────────────────────────────────────
export const getDocuments   = (auditId)        => api.get(`/audits/${auditId}/documents`)
export const uploadDocument = (auditId, file)  => uploadFile(`/audits/${auditId}/documents`, file)
export const deleteDocument = (auditId, docId) => api.delete(`/audits/${auditId}/documents/${docId}`)

// ── Findings ──────────────────────────────────────────────────────────────────
export const getFindings   = (auditId)           => api.get(`/audits/${auditId}/findings`)
export const updateFinding = (auditId, id, data) => api.patch(`/audits/${auditId}/findings/${id}`, data)
export const deleteFinding = (auditId, id)       => api.delete(`/audits/${auditId}/findings/${id}`)

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getDashboard = () => api.get('/dashboard')
