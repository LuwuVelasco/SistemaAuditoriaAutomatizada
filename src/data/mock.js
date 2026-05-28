// Mock data — reemplazar con queries Firestore en producción

export const mockUser = {
  uid: 'user-001',
  name: 'Josue Nisthaus',
  email: 'joshnisth@gmail.com',
  createdAt: '2025-01-10',
  stats: { audits: 7, approvedFindings: 34 }
}

export const mockAudits = [
  {
    id: 'aud-001',
    entity: 'Banco Unión S.A.',
    type: 'Auditoría TI',
    city: 'La Paz',
    period: '2025-Q1',
    status: 'En revisión',
    progress: 73,
    findings: 12,
    pendingFindings: 5,
    frameworks: ['COBIT', 'COSO', 'RGSI'],
    documents: 8,
    createdAt: '2025-01-15',
    ownerId: 'user-001',
    maturity: {
      level: 3,
      scores: { policies: 70, processes: 65, traceability: 80, culture: 55 },
      checklist: {
        l1_repositorios: true, l1_sin_politicas: true,
        l2_cuadro: true, l2_calendario: true, l2_desigual: true,
        l3_procesos: true, l3_roles: true, l3_trazabilidad: true,
        l4_riesgos: false, l4_activos: false, l4_coordinacion: false,
        l5_cultura: false, l5_mejora: false, l5_inspeccion: false
      },
      gapAnalysis: {
        strengths: ["Trazabilidad documental real implementada.", "Roles funcionales y técnicos definidos."],
        weaknesses: ["Falta de gobernanza activa por parte de la alta dirección.", "Aplicación irregular en el área técnica."],
        roadmap: ["Establecer comité de gobierno de información entre IT y Cumplimiento.", "Aprobar y socializar políticas a nivel directivo."]
      }
    }
  },
  {
    id: 'aud-002',
    entity: 'Cooperativa San Martín de Porres',
    type: 'Auditoría Seguridad',
    city: 'Cochabamba',
    period: '2025-Q1',
    status: 'Finalizada',
    progress: 100,
    findings: 19,
    pendingFindings: 0,
    frameworks: ['COBIT', 'COSO', 'RGSI'],
    documents: 12,
    createdAt: '2025-01-08',
    ownerId: 'user-001',
    maturity: {
      level: 5,
      scores: { policies: 100, processes: 95, traceability: 95, culture: 90 },
      checklist: {
        l1_repositorios: true, l1_sin_politicas: false,
        l2_cuadro: true, l2_calendario: true, l2_desigual: false,
        l3_procesos: true, l3_roles: true, l3_trazabilidad: true,
        l4_riesgos: true, l4_activos: true, l4_coordinacion: true,
        l5_cultura: true, l5_mejora: true, l5_inspeccion: true
      },
      gapAnalysis: {
        strengths: ["Cultura documental arraigada en todas las áreas de la cooperativa.", "Cumplimiento regulatorio proactivo ante la ASFI."],
        weaknesses: ["Pequeñas dependencias de mantenimiento en el software archivístico."],
        roadmap: ["Continuar con las auditorías de mejora continua semestrales.", "Automatizar el archivado histórico de registros antiguos."]
      }
    }
  },
  {
    id: 'aud-003',
    entity: 'Financiera Fassil S.A.',
    type: 'Auditoría Cumplimiento',
    city: 'Santa Cruz',
    period: '2025-Q1',
    status: 'Procesando',
    progress: 38,
    findings: 0,
    pendingFindings: 0,
    frameworks: ['COBIT', 'RGSI'],
    documents: 5,
    createdAt: '2025-01-22',
    ownerId: 'user-001',
    maturity: {
      level: 2,
      scores: { policies: 45, processes: 30, traceability: 25, culture: 15 },
      checklist: {
        l1_repositorios: true, l1_sin_politicas: true,
        l2_cuadro: true, l2_calendario: true, l2_desigual: true,
        l3_procesos: false, l3_roles: false, l3_trazabilidad: false,
        l4_riesgos: false, l4_activos: false, l4_coordinacion: false,
        l5_cultura: false, l5_mejora: false, l5_inspeccion: false
      },
      gapAnalysis: {
        strengths: ["Existen repositorios y un cuadro de clasificación aprobado."],
        weaknesses: ["Brecha severa entre la norma aprobada y la práctica real diaria.", "Dependencia absoluta del área técnica."],
        roadmap: ["Integrar la gestión documental en los procesos de negocio claves.", "Definir responsables en las áreas funcionales."]
      }
    }
  },
  {
    id: 'aud-004',
    entity: 'Banco Nacional de Bolivia S.A.',
    type: 'Auditoría TI',
    city: 'La Paz',
    period: '2024-Q4',
    status: 'Pendiente',
    progress: 0,
    findings: 0,
    pendingFindings: 0,
    frameworks: ['COBIT', 'COSO', 'RGSI'],
    documents: 0,
    createdAt: '2025-01-25',
    ownerId: 'user-001',
    maturity: {
      level: 1,
      scores: { policies: 15, processes: 10, traceability: 5, culture: 5 },
      checklist: {
        l1_repositorios: true, l1_sin_politicas: true,
        l2_cuadro: false, l2_calendario: false, l2_desigual: true,
        l3_procesos: false, l3_roles: false, l3_trazabilidad: false,
        l4_riesgos: false, l4_activos: false, l4_coordinacion: false,
        l5_cultura: false, l5_mejora: false, l5_inspeccion: false
      },
      gapAnalysis: {
        strengths: ["Repositorios digitales existentes para almacenamiento."],
        weaknesses: ["No existen políticas aprobadas ni cuadro de clasificación.", "Acumulación digital desordenada e irregular."],
        roadmap: ["Iniciar el desarrollo de políticas documentales básicas.", "Definir el cuadro de clasificación y conservación archivística."]
      }
    }
  }
]

export const mockDocuments = {
  'aud-001': [
    { id: 'doc-001', name: 'Manual_Seguridad_TI_2024.pdf', type: 'pdf', size: '2.4 MB', status: 'ready', chunks: 147, sha256: 'a3f8b1c2...', uploadedAt: '2025-01-15' },
    { id: 'doc-002', name: 'PNP_Gestion_Accesos.docx', type: 'docx', size: '856 KB', status: 'ready', chunks: 62, sha256: 'd7e2a9f1...', uploadedAt: '2025-01-15' },
    { id: 'doc-003', name: 'Inventario_Activos_TI.xlsx', type: 'xlsx', size: '1.1 MB', status: 'ready', chunks: 88, sha256: 'c1b5d3e8...', uploadedAt: '2025-01-16' },
    { id: 'doc-004', name: 'Politica_Copias_Seguridad.pdf', type: 'pdf', size: '420 KB', status: 'ready', chunks: 29, sha256: 'f4a7c2b9...', uploadedAt: '2025-01-16' },
    { id: 'doc-005', name: 'PNP_Continuidad_Negocio.pdf', type: 'pdf', size: '1.8 MB', status: 'indexing', chunks: 0, sha256: null, uploadedAt: '2025-01-17' },
  ],
  'aud-002': [
    { id: 'doc-006', name: 'Reglamento_Interno_SI.pdf', type: 'pdf', size: '1.2 MB', status: 'ready', chunks: 94, sha256: 'b2e5f9a1...', uploadedAt: '2025-01-08' },
    { id: 'doc-007', name: 'Mapa_Procesos_TI.docx', type: 'docx', size: '670 KB', status: 'ready', chunks: 48, sha256: 'e8c3d7b4...', uploadedAt: '2025-01-08' },
  ],
  'aud-003': [
    { id: 'doc-008', name: 'Manual_Control_Interno.pdf', type: 'pdf', size: '3.1 MB', status: 'indexing', chunks: 0, sha256: null, uploadedAt: '2025-01-22' },
  ]
}

export const mockFindings = {
  'aud-001': [
    {
      id: 'HLZ-001',
      auditId: 'aud-001',
      title: 'Ausencia de controles de acceso privilegiado documentados',
      description: 'No se identificaron políticas formales ni procedimientos documentados para la gestión de cuentas con privilegios administrativos en los sistemas críticos de la institución.',
      recommendation: 'Implementar una política formal de gestión de accesos privilegiados (PAM) que incluya criterios de otorgamiento, revisión periódica y revocación inmediata ante desvinculación. Considerar herramientas de gestión centralizada como CyberArk o BeyondTrust.',
      risk: 'Alto',
      impact: 4,
      probability: 3,
      status: 'Pendiente',
      confidence: 0.91,
      cobitRef: { code: 'APO13.01', title: 'Establecer y mantener el SGSI', domain: 'APO' },
      cosoRef:  { code: 'CC6.1', title: 'Control de Acceso Lógico', component: 'Actividades de Control' },
      rgsiRef:  { code: 'Art. 12', title: 'Gestión de Accesos y Autenticación', section: 'Cap. III' },
      evidence: [
        { docId: 'doc-001', docName: 'Manual_Seguridad_TI_2024.pdf', page: 34, paragraph: 'Sección 4.2 — Gestión de Identidades' },
        { docId: 'doc-002', docName: 'PNP_Gestion_Accesos.docx', page: 8, paragraph: 'Punto 3.1 — Roles y Privilegios' }
      ],
      quote: '"Los accesos a sistemas críticos son otorgados por el área de TI sin un proceso de aprobación formal documentado ni revisión periódica de permisos vigentes."',
      detectedBy: 'COSFI-ENGINE-COBIT',
      createdAt: '2025-01-20'
    },
    {
      id: 'HLZ-002',
      auditId: 'aud-001',
      title: 'Plan de continuidad de negocio sin pruebas actualizadas',
      description: 'El Plan de Continuidad del Negocio (BCP) existente no ha sido sometido a pruebas ni simulacros en los últimos 24 meses, superando el período máximo establecido por el RGSI.',
      recommendation: 'Ejecutar ejercicios de continuidad (tabletop exercises y simulacros técnicos) al menos una vez al año. Actualizar el BCP para reflejar los cambios en la infraestructura de TI y designar un responsable de continuidad.',
      risk: 'Extremo',
      impact: 5,
      probability: 4,
      status: 'Aprobado',
      confidence: 0.95,
      cobitRef: { code: 'DSS04.03', title: 'Desarrollar e implementar respuesta ante continuidad', domain: 'DSS' },
      cosoRef:  { code: 'OV2.1', title: 'Identificación de Riesgos Operacionales', component: 'Evaluación de Riesgos' },
      rgsiRef:  { code: 'Art. 28', title: 'Plan de Continuidad Operativa', section: 'Cap. VI' },
      evidence: [
        { docId: 'doc-004', docName: 'Politica_Copias_Seguridad.pdf', page: 12, paragraph: 'Sección 7 — Pruebas de Recuperación' }
      ],
      quote: '"La última prueba del plan de continuidad se realizó en febrero de 2022, no existiendo evidencia de pruebas posteriores a dicha fecha."',
      detectedBy: 'COSFI-ENGINE-RGSI',
      createdAt: '2025-01-20'
    },
    {
      id: 'HLZ-003',
      auditId: 'aud-001',
      title: 'Inventario de activos de TI desactualizado',
      description: 'El inventario de activos tecnológicos presenta inconsistencias con el entorno productivo real, incluyendo equipos dados de baja aún registrados como activos y ausencia de nuevos dispositivos incorporados en 2024.',
      recommendation: 'Establecer un proceso automatizado de descubrimiento de activos con herramientas como Lansweeper o ServiceNow CMDB. Definir responsables de actualización y frecuencia mínima trimestral.',
      risk: 'Medio',
      impact: 3,
      probability: 3,
      status: 'Pendiente',
      confidence: 0.84,
      cobitRef: { code: 'BAI09.01', title: 'Identificar y registrar activos actuales', domain: 'BAI' },
      cosoRef:  { code: 'CC4.2', title: 'Supervisión de Controles', component: 'Actividades de Monitoreo' },
      rgsiRef:  { code: 'Art. 8', title: 'Clasificación de Activos de Información', section: 'Cap. II' },
      evidence: [
        { docId: 'doc-003', docName: 'Inventario_Activos_TI.xlsx', page: 1, paragraph: 'Hoja: Activos Vigentes — Col. F' }
      ],
      quote: '"Se identificaron 23 equipos registrados como activos en el inventario que corresponden a bajas efectuadas durante el ejercicio 2023, sin la respectiva actualización en el sistema."',
      detectedBy: 'COSFI-ENGINE-COBIT',
      createdAt: '2025-01-21'
    }
  ],
  'aud-002': [
    {
      id: 'HLZ-A01',
      auditId: 'aud-002',
      title: 'Ausencia de política de clasificación de información',
      description: 'La cooperativa no cuenta con una política formal de clasificación de información que establezca niveles de confidencialidad y controles asociados.',
      recommendation: 'Desarrollar e implementar una política de clasificación de información con al menos 3 niveles (público, interno, confidencial) y controles de manejo diferenciados.',
      risk: 'Alto',
      impact: 4,
      probability: 4,
      status: 'Aprobado',
      confidence: 0.89,
      cobitRef: { code: 'APO13.02', title: 'Definir y gestionar un plan de tratamiento', domain: 'APO' },
      cosoRef:  { code: 'CC2.1', title: 'Comunicación Interna de Información', component: 'Información y Comunicación' },
      rgsiRef:  { code: 'Art. 9', title: 'Clasificación y Etiquetado', section: 'Cap. II' },
      evidence: [],
      quote: '"No se encontró evidencia de un esquema de clasificación de información formalmente aprobado por la alta dirección."',
      detectedBy: 'COSFI-ENGINE-COSO',
      createdAt: '2025-01-12'
    }
  ]
}

export const RISK_LEVELS = ['Extremo', 'Alto', 'Medio', 'Bajo', 'Oportunidad']
export const RISK_PILL_CLASS = {
  'Extremo': 'pill-extreme',
  'Alto': 'pill-high',
  'Medio': 'pill-medium',
  'Bajo': 'pill-low',
  'Oportunidad': 'pill-opp'
}

export const STATUS_PILL_CLASS = {
  'Pendiente': 'pill-pending',
  'Procesando': 'pill-processing',
  'En revisión': 'pill-review',
  'Finalizada': 'pill-done',
  'Aprobado': 'pill-approved',
  'Rechazado': 'pill-rejected'
}
