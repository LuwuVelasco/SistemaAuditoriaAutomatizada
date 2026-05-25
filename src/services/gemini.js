import { GoogleGenerativeAI } from '@google/generative-ai'

const genAI = new GoogleGenerativeAI(import.meta.env.VITE_GEMINI_API_KEY)

// Los 3 motores usan el mismo modelo pero prompts distintos.
// En producción esto pasaría a Cloud Functions para no exponer la API key.
const model = () => genAI.getGenerativeModel({ model: 'gemini-2.0-flash' })

// ─── Engine 1: COBIT 2019 ───────────────────────────────────────────────────
export async function analyzeWithCOBIT(documentText) {
  const prompt = `Eres un auditor experto en COBIT 2019. Analiza el siguiente texto de documentos organizacionales de una entidad financiera boliviana y detecta hallazgos de auditoría de TI.

Para cada hallazgo encontrado devuelve un JSON array con este formato exacto:
[{
  "title": "Título conciso del hallazgo",
  "description": "Descripción detallada del problema identificado",
  "recommendation": "Recomendación específica y accionable",
  "risk": "Alto|Extremo|Medio|Bajo",
  "impact": 1-5,
  "probability": 1-5,
  "cobitRef": { "code": "XXX.XX", "title": "Título del objetivo COBIT", "domain": "APO|BAI|DSS|EDM|MEA" },
  "quote": "Cita textual del documento que evidencia el hallazgo"
}]

Si no encuentras hallazgos claros devuelve [].

TEXTO A ANALIZAR:
${documentText.slice(0, 8000)}`

  const result = await model().generateContent(prompt)
  const text = result.response.text()
  const match = text.match(/\[[\s\S]*\]/)
  if (!match) return []
  try { return JSON.parse(match[0]) } catch { return [] }
}

// ─── Engine 2: COSO 2013 ────────────────────────────────────────────────────
export async function analyzeWithCOSO(documentText) {
  const prompt = `Eres un auditor experto en COSO 2013 (Control Interno). Analiza el siguiente texto de documentos organizacionales de una entidad financiera boliviana.

Para cada debilidad de control interno encontrada devuelve un JSON array:
[{
  "title": "Título del hallazgo",
  "description": "Descripción del control interno deficiente",
  "recommendation": "Recomendación para fortalecer el control",
  "risk": "Alto|Extremo|Medio|Bajo",
  "impact": 1-5,
  "probability": 1-5,
  "cosoRef": { "code": "CC|OV|AL|RE|MO + número", "title": "Principio COSO", "component": "Entorno de Control|Evaluación de Riesgos|Actividades de Control|Información y Comunicación|Actividades de Monitoreo" },
  "quote": "Cita textual del documento"
}]

Si no encuentras hallazgos claros devuelve [].

TEXTO:
${documentText.slice(0, 8000)}`

  const result = await model().generateContent(prompt)
  const text = result.response.text()
  const match = text.match(/\[[\s\S]*\]/)
  if (!match) return []
  try { return JSON.parse(match[0]) } catch { return [] }
}

// ─── Engine 3: RGSI/ASFI ────────────────────────────────────────────────────
export async function analyzeWithRGSI(documentText) {
  const prompt = `Eres un auditor experto en el RGSI (Reglamento de Gestión de Seguridad de la Información) emitido por la ASFI (Autoridad de Supervisión del Sistema Financiero) de Bolivia.

Analiza el siguiente texto de documentos organizacionales de una entidad financiera y detecta incumplimientos o debilidades respecto al RGSI.

Para cada hallazgo devuelve un JSON array:
[{
  "title": "Título del hallazgo",
  "description": "Descripción del incumplimiento o debilidad",
  "recommendation": "Recomendación para cumplir con el RGSI",
  "risk": "Alto|Extremo|Medio|Bajo",
  "impact": 1-5,
  "probability": 1-5,
  "rgsiRef": { "code": "Art. XX", "title": "Título del artículo", "section": "Capítulo correspondiente" },
  "quote": "Cita textual del documento"
}]

Si no encuentras hallazgos claros devuelve [].

TEXTO:
${documentText.slice(0, 8000)}`

  const result = await model().generateContent(prompt)
  const text = result.response.text()
  const match = text.match(/\[[\s\S]*\]/)
  if (!match) return []
  try { return JSON.parse(match[0]) } catch { return [] }
}

// ─── Consolidador ───────────────────────────────────────────────────────────
export async function consolidateFindings(cobitFindings, cosoFindings, rgsiFindings) {
  if (!cobitFindings.length && !cosoFindings.length && !rgsiFindings.length) return []

  const prompt = `Eres un auditor de TI que consolida hallazgos de tres motores de análisis (COBIT, COSO, RGSI).

Tu tarea es fusionar hallazgos que traten el mismo tema y enriquecer cada hallazgo con referencias de los tres marcos.

Hallazgos COBIT:
${JSON.stringify(cobitFindings, null, 2)}

Hallazgos COSO:
${JSON.stringify(cosoFindings, null, 2)}

Hallazgos RGSI:
${JSON.stringify(rgsiFindings, null, 2)}

Devuelve un JSON array con los hallazgos consolidados, donde cada uno tiene:
{
  "title": "Título",
  "description": "Descripción consolidada",
  "recommendation": "Recomendación",
  "risk": "Extremo|Alto|Medio|Bajo|Oportunidad",
  "impact": 1-5,
  "probability": 1-5,
  "cobitRef": { "code": "...", "title": "...", "domain": "..." } o null,
  "cosoRef": { "code": "...", "title": "...", "component": "..." } o null,
  "rgsiRef": { "code": "...", "title": "...", "section": "..." } o null,
  "quote": "cita principal",
  "confidence": 0.0-1.0
}`

  const result = await model().generateContent(prompt)
  const text = result.response.text()
  const match = text.match(/\[[\s\S]*\]/)
  if (!match) return []
  try { return JSON.parse(match[0]) } catch { return [] }
}
