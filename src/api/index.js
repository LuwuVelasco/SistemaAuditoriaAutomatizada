import { api, uploadFile, downloadFile } from './client'

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

// ── Graph ─────────────────────────────────────────────────────────────────────
export const getGraph = (auditId) => api.get(`/audits/${auditId}/graph`)


// ── Reports ───────────────────────────────────────────────────────────────────
export const getReports = (auditId) => api.get(`/audits/${auditId}/reports`)
export const generateReports = (auditId, kinds, format) => api.post(`/audits/${auditId}/reports`, { kinds, format })
export const downloadReport = (auditId, reportId) => downloadFile(`/audits/${auditId}/reports/${reportId}/download`)
export const emailReports   = (auditId, reportIds, recipientEmail) =>
  api.post(`/audits/${auditId}/reports/email`, { report_ids: reportIds, recipient_email: recipientEmail })

// ── Chat ──────────────────────────────────────────────────────────────────────
export const sendChatMessage = (auditId, question, history) =>
  api.post(`/audits/${auditId}/chat`, { question, history })

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getDashboard = () => api.get('/dashboard')
