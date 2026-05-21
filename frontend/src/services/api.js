/**
 * API Client — Comunicación con el backend FastAPI.
 */

const API_BASE = 'http://127.0.0.1:8000/api';
const WS_BASE = 'ws://127.0.0.1:8000/ws';

// ── Documentos ──────────────────────────────────────────

export async function uploadDocumentos(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error(`Error subiendo archivos: ${res.statusText}`);
  return res.json();
}

export async function listarDocumentos() {
  const res = await fetch(`${API_BASE}/documentos`);
  if (!res.ok) throw new Error('Error listando documentos');
  return res.json();
}

export async function eliminarDocumento(nombre) {
  const res = await fetch(`${API_BASE}/documentos/${encodeURIComponent(nombre)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Error eliminando documento');
  return res.json();
}

export async function eliminarTodosDocumentos() {
  const res = await fetch(`${API_BASE}/documentos`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Error eliminando documentos');
  return res.json();
}

// ── Auditoría ───────────────────────────────────────────

export async function iniciarAuditoria(config = {}) {
  const res = await fetch(`${API_BASE}/auditoria/iniciar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Error iniciando auditoría');
  }
  return res.json();
}

export async function estadoAuditoria() {
  const res = await fetch(`${API_BASE}/auditoria/estado`);
  if (!res.ok) throw new Error('Error obteniendo estado');
  return res.json();
}

export async function obtenerHallazgos() {
  const res = await fetch(`${API_BASE}/auditoria/hallazgos`);
  if (!res.ok) throw new Error('Error obteniendo hallazgos');
  return res.json();
}

export async function obtenerContexto() {
  const res = await fetch(`${API_BASE}/auditoria/contexto`);
  if (!res.ok) throw new Error('Error obteniendo contexto');
  return res.json();
}

export async function obtenerResultados() {
  const res = await fetch(`${API_BASE}/auditoria/resultados`);
  if (!res.ok) throw new Error('Error obteniendo resultados');
  return res.json();
}

export async function obtenerCoso() {
  const res = await fetch(`${API_BASE}/auditoria/coso`);
  if (!res.ok) throw new Error('Error obteniendo COSO');
  return res.json();
}

// ── Exportación ─────────────────────────────────────────

export async function listarArchivosGenerados() {
  const res = await fetch(`${API_BASE}/exportar/archivos`);
  if (!res.ok) throw new Error('Error listando archivos');
  return res.json();
}

export function getUrlDescarga(nombre) {
  return `${API_BASE}/exportar/${encodeURIComponent(nombre)}`;
}

// ── Health ──────────────────────────────────────────────

export async function healthCheck() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return { status: 'error', gemini_disponible: false };
    return res.json();
  } catch {
    return { status: 'error', gemini_disponible: false };
  }
}

// ── WebSocket URL ───────────────────────────────────────

export const WS_PROGRESO_URL = `${WS_BASE}/progreso`;
