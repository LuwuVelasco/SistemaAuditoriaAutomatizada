# Esquema Firestore — COSFI MVP

Diseño NO relacional. Regla central: **binarios siempre en Cloud Storage, Firestore solo metadatos**.

---

## Colecciones raíz

```
firestore/
├── users/{uid}
├── audits/{auditId}
│   ├── documents/{docId}       ← subcolección
│   ├── findings/{findingId}    ← subcolección
│   │   └── history/{eventId}   ← subcolección (write-only desde Cloud Functions)
│   └── reports/{reportId}      ← subcolección
└── frameworks/{cobit|coso|rgsi}
    └── controls/{controlId}    ← catálogo normativo
```

---

## Documentos por colección

### `users/{uid}`
```json
{
  "name":      "Ana Mamani",
  "email":     "ana@banco.bo",
  "createdAt": "2025-01-10",
  "stats": {
    "audits":           7,
    "approvedFindings": 34
  }
}
```
- Clave = Firebase Auth UID.
- Sin organización ni rol (cuenta personal).

---

### `audits/{auditId}`
```json
{
  "entity":    "Banco Unión S.A.",
  "type":      "Auditoría TI",
  "city":      "La Paz",
  "period":    "2025-Q1",
  "status":    "En revisión",
  "progress":  73,
  "frameworks": ["COBIT", "COSO", "RGSI"],
  "ownerId":   "uid-abc123",
  "createdAt": "2025-01-15T10:00:00Z"
}
```
- `status`: `Pendiente | Procesando | En revisión | Finalizada`

---

### `audits/{auditId}/documents/{docId}`
```json
{
  "name":        "Manual_Seguridad_TI.pdf",
  "type":        "pdf",
  "size":        "2.4 MB",
  "storagePath": "audits/aud-001/docs/Manual_Seguridad_TI.pdf",
  "status":      "ready",
  "chunks":      147,
  "sha256":      "a3f8b1c2d4e5...",
  "uploadedAt":  "2025-01-15T11:00:00Z"
}
```
- `status`: `queued | indexing | ready`
- Cloud Function `onCreate` → encola indexación, actualiza status.

---

### `audits/{auditId}/findings/{findingId}`
```json
{
  "title":          "Ausencia de controles de acceso privilegiado",
  "description":    "...",
  "recommendation": "...",
  "risk":           "Alto",
  "impact":         4,
  "probability":    3,
  "status":         "Pendiente",
  "confidence":     0.91,
  "cobitRef": { "code": "APO13.01", "title": "...", "domain": "APO" },
  "cosoRef":  { "code": "CC6.1",    "title": "...", "component": "Actividades de Control" },
  "rgsiRef":  { "code": "Art. 12",  "title": "...", "section": "Cap. III" },
  "evidence": [
    { "docId": "doc-001", "docName": "Manual.pdf", "page": 34, "paragraph": "Sección 4.2" }
  ],
  "quote":       "Cita textual del documento...",
  "detectedBy":  "COSFI-ENGINE-COBIT",
  "aiRunId":     "run-xyz",
  "createdAt":   "2025-01-20T14:00:00Z",
  "updatedAt":   "2025-01-21T09:00:00Z"
}
```
- `status`: `Pendiente | Aprobado | Rechazado`
- `onUpdate` Cloud Function → escribe en `history/` (inmutable).

---

### `audits/{auditId}/findings/{findingId}/history/{eventId}`
```json
{
  "field":     "status",
  "oldValue":  "Pendiente",
  "newValue":  "Aprobado",
  "changedBy": "uid-abc123",
  "changedAt": "2025-01-22T10:00:00Z"
}
```
- **Write-only desde Cloud Functions** — clientes no pueden escribir.
- Trazabilidad regulatoria requerida por RGSI.

---

### `audits/{auditId}/reports/{reportId}`
```json
{
  "kind":        "matriz-hallazgos",
  "format":      "xlsx",
  "storagePath": "audits/aud-001/reports/matriz_2025Q1.xlsx",
  "sha256":      "d7e2a9f1...",
  "generatedAt": "2025-01-25T16:00:00Z"
}
```

---

### `frameworks/{cobit|coso|rgsi}/controls/{controlId}`
```json
{
  "code":        "APO13.01",
  "title":       "Establecer y mantener el SGSI",
  "domain":      "APO",
  "description": "...",
  "keywords":    ["seguridad", "información", "sgsi", "política"],
  "embedding":   [0.12, -0.34, ...]
}
```
- Catálogo de referencia. Los embeddings se usan para matching semántico en el pipeline IA.
- Poblar una sola vez (seed) con los controles de COBIT 2019, COSO 2013, y artículos RGSI-ASFI.

---

## Reglas de seguridad (resumen)

```javascript
// firestore.rules (esquema)
rules_version = '2';
service cloud.firestore {
  match /databases/{db}/documents {

    // Usuario solo lee/escribe su propio perfil
    match /users/{uid} {
      allow read, write: if request.auth.uid == uid;
    }

    // Auditoría: solo el owner
    match /audits/{auditId} {
      allow read, write: if request.auth.uid == resource.data.ownerId;

      match /documents/{docId} {
        allow read, write: if request.auth.uid == get(/databases/$(db)/documents/audits/$(auditId)).data.ownerId;
      }

      match /findings/{findingId} {
        allow read, write: if request.auth.uid == get(/databases/$(db)/documents/audits/$(auditId)).data.ownerId;

        // history: solo lectura para el owner, escritura solo desde Cloud Functions
        match /history/{eventId} {
          allow read:  if request.auth.uid == get(/databases/$(db)/documents/audits/$(auditId)).data.ownerId;
          allow write: if false; // solo Cloud Functions con Admin SDK
        }
      }

      match /reports/{reportId} {
        allow read: if request.auth.uid == get(/databases/$(db)/documents/audits/$(auditId)).data.ownerId;
        allow write: if false; // solo Cloud Functions
      }
    }

    // Catálogo normativo: lectura pública autenticada
    match /frameworks/{framework}/controls/{controlId} {
      allow read: if request.auth != null;
      allow write: if false;
    }
  }
}
```

---

## Cloud Storage estructura

```
gs://cosfi-bucket/
├── audits/{auditId}/
│   ├── docs/{filename}        ← documentos subidos
│   └── reports/{filename}     ← reportes generados
└── frameworks/                ← recursos estáticos del catálogo
```

---

## Notas de diseño

- **Sin embeddings en cliente**: el matching semántico ocurre en Cloud Functions (Vertex AI Vector Search).
- **aiRuns no incluido** en este MVP — agregar cuando el pipeline IA sea real.
- **Timestamps**: usar `serverTimestamp()` en escrituras para consistencia.
- **Índices compuestos** que necesitarás: `audits` por `ownerId + createdAt`, `findings` por `auditId + risk + status`.
