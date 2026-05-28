import { auth } from '../firebase'

const BASE = import.meta.env.VITE_API_URL || ''

async function getToken() {
  const user = auth.currentUser
  if (!user) return null
  return user.getIdToken()
}

async function request(method, path, body) {
  const token = await getToken()
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}/api/v1${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (res.status === 204) return null
  const json = await res.json()
  if (!res.ok) {
    // FastAPI validation errors usan json.detail
    const detail = json.detail ?? json.error ?? `Error ${res.status}`
    const msg = Array.isArray(detail)
      ? detail.map(e => `${e.loc?.slice(-1)[0]}: ${e.msg}`).join(', ')
      : String(detail)
    throw new Error(msg)
  }
  return json.data ?? json
}

async function requestBlob(method, path) {
  const token = await getToken()
  const headers = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE}/api/v1${path}`, {
    method,
    headers,
  })

  if (!res.ok) {
    let detail = `Error ${res.status}`
    try {
      const json = await res.json()
      detail = json.detail ?? json.error ?? detail
    } catch {
      const text = await res.text()
      if (text) detail = text
    }
    throw new Error(String(detail))
  }

  const blob = await res.blob()
  const disposition = res.headers.get('Content-Disposition') || ''
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/i)
  return { blob, filename: filenameMatch?.[1] || null, contentType: res.headers.get('Content-Type') || '' }
}

export const api = {
  get:    (path)       => request('GET',    path),
  post:   (path, body) => request('POST',   path, body),
  patch:  (path, body) => request('PATCH',  path, body),
  delete: (path)       => request('DELETE', path),
}

export async function uploadFile(path, file) {
  const token = await getToken()
  const form = new FormData()
  form.append('file', file)
  const headers = token ? { Authorization: `Bearer ${token}` } : {}

  const res = await fetch(`${BASE}/api/v1${path}`, {
    method: 'POST',
    headers,
    body: form,
  })

  const json = await res.json()
  if (!res.ok) throw new Error(json.error || 'Error al subir archivo')
  return json.data ?? json
}

export async function downloadFile(path) {
  return requestBlob('GET', path)
}
