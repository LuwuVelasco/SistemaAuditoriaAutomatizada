/**
 * Seed inicial de Firestore para COSFI MVP
 * Ejecutar UNA SOLA VEZ después de crear el proyecto Firebase.
 *
 * Uso:
 *   node scripts/seed.js
 *
 * Requiere: GOOGLE_APPLICATION_CREDENTIALS apuntando al service account JSON
 * O bien: `firebase login` y luego `firebase use <project-id>`
 */

import { initializeApp, cert } from 'firebase-admin/app'
import { getFirestore }         from 'firebase-admin/firestore'
import { readFileSync }         from 'fs'

// ── Configuración ──────────────────────────────────────────────────────────
// Descarga tu service account desde Firebase Console →
// Proyecto → Configuración → Cuentas de servicio → Generar nueva clave privada
const serviceAccount = JSON.parse(readFileSync('./serviceAccountKey.json', 'utf8'))

initializeApp({ credential: cert(serviceAccount) })
const db = getFirestore()

// ── Datos de ejemplo (igual que mock.js) ──────────────────────────────────
const NOW = new Date().toISOString()

// Reemplaza este UID con el uid real del usuario creado en Firebase Auth
const OWNER_UID = 'REEMPLAZA_CON_UID_REAL'

const audits = [
  {
    id: 'aud-001',
    entity: 'Banco Unión S.A.',
    type: 'Auditoría TI',
    city: 'La Paz',
    period: '2025-Q1',
    status: 'En revisión',
    progress: 73,
    findingsCount: 2,
    pendingFindings: 1,
    documentsCount: 3,
    frameworks: ['COBIT', 'COSO', 'RGSI'],
    ownerId: OWNER_UID,
    createdAt: NOW
  },
  {
    id: 'aud-002',
    entity: 'Cooperativa San Martín de Porres',
    type: 'Auditoría Seguridad',
    city: 'Cochabamba',
    period: '2025-Q1',
    status: 'Finalizada',
    progress: 100,
    findingsCount: 1,
    pendingFindings: 0,
    documentsCount: 2,
    frameworks: ['COBIT', 'COSO', 'RGSI'],
    ownerId: OWNER_UID,
    createdAt: NOW
  },
  {
    id: 'aud-003',
    entity: 'Financiera Fassil S.A.',
    type: 'Auditoría Cumplimiento',
    city: 'Santa Cruz',
    period: '2025-Q1',
    status: 'Pendiente',
    progress: 0,
    findingsCount: 0,
    pendingFindings: 0,
    documentsCount: 0,
    frameworks: ['COBIT', 'RGSI'],
    ownerId: OWNER_UID,
    createdAt: NOW
  }
]

// Hallazgos de ejemplo para aud-001
const findings_aud001 = [
  {
    id: 'HLZ-001',
    title: 'Ausencia de controles de acceso privilegiado documentados',
    description: 'No se identificaron políticas formales para la gestión de cuentas con privilegios administrativos en los sistemas críticos.',
    recommendation: 'Implementar política PAM con revisión periódica y herramientas de control centralizado.',
    risk: 'Alto',
    impact: 4,
    probability: 3,
    status: 'Pendiente',
    confidence: 0.91,
    cobitRef: { code: 'APO13.01', title: 'Establecer y mantener el SGSI', domain: 'APO' },
    cosoRef:  { code: 'CC6.1',    title: 'Control de Acceso Lógico',     component: 'Actividades de Control' },
    rgsiRef:  { code: 'Art. 12',  title: 'Gestión de Accesos',           section: 'Cap. III' },
    quote: '"Los accesos a sistemas críticos son otorgados sin proceso de aprobación formal."',
    evidence: [],
    detectedBy: 'COSFI-ENGINE-COBIT',
    createdAt: NOW
  },
  {
    id: 'HLZ-002',
    title: 'Plan de continuidad sin pruebas actualizadas',
    description: 'El BCP no ha sido probado en los últimos 24 meses, superando el período máximo del RGSI.',
    recommendation: 'Ejecutar simulacros al menos una vez al año y actualizar el BCP.',
    risk: 'Extremo',
    impact: 5,
    probability: 4,
    status: 'Aprobado',
    confidence: 0.95,
    cobitRef: { code: 'DSS04.03', title: 'Respuesta ante continuidad', domain: 'DSS' },
    cosoRef:  { code: 'OV2.1',   title: 'Identificación de Riesgos',  component: 'Evaluación de Riesgos' },
    rgsiRef:  { code: 'Art. 28', title: 'Plan de Continuidad',        section: 'Cap. VI' },
    quote: '"La última prueba del BCP se realizó en febrero de 2022."',
    evidence: [],
    detectedBy: 'COSFI-ENGINE-RGSI',
    createdAt: NOW
  }
]

// Hallazgo de ejemplo para aud-002
const findings_aud002 = [
  {
    id: 'HLZ-A01',
    title: 'Ausencia de política de clasificación de información',
    description: 'La cooperativa no cuenta con una política formal de clasificación de información.',
    recommendation: 'Desarrollar política con niveles público/interno/confidencial y controles diferenciados.',
    risk: 'Alto',
    impact: 4,
    probability: 4,
    status: 'Aprobado',
    confidence: 0.89,
    cobitRef: { code: 'APO13.02', title: 'Plan de tratamiento SGSI', domain: 'APO' },
    cosoRef:  { code: 'CC2.1',   title: 'Comunicación Interna',     component: 'Información y Comunicación' },
    rgsiRef:  { code: 'Art. 9',  title: 'Clasificación y Etiquetado', section: 'Cap. II' },
    quote: '"No se encontró evidencia de esquema de clasificación formalmente aprobado."',
    evidence: [],
    detectedBy: 'COSFI-ENGINE-COSO',
    createdAt: NOW
  }
]

// ── Escritura en Firestore ─────────────────────────────────────────────────
async function seed() {
  console.log('Iniciando seed de Firestore...\n')
  const batch = db.batch()

  // Perfil del usuario
  batch.set(db.collection('users').doc(OWNER_UID), {
    name: 'Josue Nisthaus',
    email: 'joshnisth@gmail.com',
    createdAt: NOW,
    stats: { audits: 3, approvedFindings: 2 }
  })

  // Auditorías
  for (const audit of audits) {
    const { id, ...data } = audit
    batch.set(db.collection('audits').doc(id), data)
  }

  await batch.commit()
  console.log('✓ Auditorías y usuario creados')

  // Hallazgos (subcolecciones — lote separado)
  const batch2 = db.batch()
  for (const f of findings_aud001) {
    const { id, ...data } = f
    batch2.set(db.collection('audits').doc('aud-001').collection('findings').doc(id), data)
  }
  for (const f of findings_aud002) {
    const { id, ...data } = f
    batch2.set(db.collection('audits').doc('aud-002').collection('findings').doc(id), data)
  }

  await batch2.commit()
  console.log('✓ Hallazgos creados')

  console.log('\n✓ Seed completo. Ya puedes usar la app.')
}

seed().catch(console.error)
