# SAAM Backend — Sistema de Auditoría Automatizada Multimarco

API REST construida con **FastAPI** que orquesta el pipeline IA de COSFI:
documentos PDF → extracción de texto → motores COSO / COBIT / RGSI → hallazgos en Firestore.

---

## Requisitos

- Python 3.11+
- Cuenta Firebase (Firestore + Authentication)
- Cuenta Supabase (Storage: buckets `pdfs` y `xlsx`)
- 3 API Keys de Google Gemini (una por motor IA)

---

## Instalación

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

---

## Configuración

Copia `.env.example` a `.env` y rellena todas las variables:

```bash
copy .env.example .env
```

Variables obligatorias:

| Variable | Descripción |
|---|---|
| `FIREBASE_PROJECT_ID` | ID del proyecto Firebase |
| `FIREBASE_CLIENT_EMAIL` | Email de la service account |
| `FIREBASE_PRIVATE_KEY` | Clave privada (o usa `FIREBASE_CREDENTIALS_PATH`) |
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_KEY` | Anon/service key de Supabase |
| `GEMINI_COSO_API_KEY` | API key para el motor COSO |
| `GEMINI_COBIT_API_KEY` | API key para el motor COBIT |
| `GEMINI_RGSI_API_KEY` | API key para el motor RGSI |

---

## Ejecución

```bash
# Desarrollo con hot-reload
python run.py

# Puerto y host personalizados
python run.py --host 127.0.0.1 --port 8080

# Producción (4 workers, sin reload)
python run.py --env production
```

Documentación interactiva disponible en: `http://localhost:8000/docs`

---

## Arquitectura

```
backend/
├── app/
│   ├── main.py              # FastAPI app + middleware + exception handlers
│   ├── api/
│   │   ├── deps.py          # Inyección de dependencias
│   │   └── routes/
│   │       ├── auth.py      # GET /me, PUT /profile
│   │       ├── audits.py    # CRUD + POST /analyze (BackgroundTask)
│   │       ├── documents.py # Upload + CRUD de documentos
│   │       ├── findings.py  # CRUD + historial de hallazgos
│   │       ├── reports.py   # Generación de reportes XLSX/DOCX
│   │       ├── dashboard.py # Métricas ejecutivas
│   │       └── frameworks.py# Catálogos normativos (read-only)
│   ├── ai/
│   │   ├── orchestrator.py       # Secuencia COSO → COBIT → RGSI
│   │   ├── coso_engine.py        # Motor COSO (Gemini)
│   │   ├── cobit_engine.py       # Motor COBIT (Gemini)
│   │   ├── rgsi_engine.py        # Motor RGSI (Gemini)
│   │   ├── extraction_pipeline.py# Descarga + extracción de texto
│   │   ├── finding_merger.py     # Consolidación y deduplicación
│   │   └── prompt_builder.py     # Construcción de prompts por framework
│   ├── services/            # Lógica de negocio
│   ├── repositories/        # Acceso a Firestore
│   ├── models/              # Modelos de dominio (Pydantic)
│   ├── schemas/             # Schemas de entrada/salida HTTP
│   ├── core/                # Config, Firebase, Supabase, excepciones
│   └── utils/               # Enums, helpers, timestamps, risk matrix
├── tests/
│   └── conftest.py          # Fixtures con mocks de Firebase/Supabase
├── run.py                   # Punto de entrada uvicorn
├── requirements.txt
└── .env.example
```

---

## Pipeline IA

```
POST /api/v1/audits/{id}/analyze
        │
        ▼  (BackgroundTask — no bloquea el request)
  AIService.run_analysis()
        │
        ├─ ExtractionPipeline → descarga PDFs de Supabase → extrae texto (pypdf)
        │
        ├─ COSOEngine   → analiza texto con Gemini → RawFindings
        ├─ COBITEngine  → analiza texto + hallazgos COSO → RawFindings
        ├─ RGSIEngine   → analiza texto + hallazgos COSO+COBIT → RawFindings
        │
        ├─ FindingMerger → consolida y deduplica (similitud Jaccard)
        │
        └─ FindingRepository.create_batch() → persiste en Firestore
```

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/v1/auth/me` | Perfil del usuario |
| GET | `/api/v1/audits` | Listar auditorías del usuario |
| POST | `/api/v1/audits` | Crear auditoría |
| POST | `/api/v1/audits/{id}/analyze` | Iniciar pipeline IA (async) |
| POST | `/api/v1/audits/{id}/documents` | Subir PDF |
| GET | `/api/v1/audits/{id}/findings` | Listar hallazgos |
| PATCH | `/api/v1/audits/{id}/findings/{fid}` | Actualizar hallazgo |
| GET | `/api/v1/audits/{id}/findings/{fid}/history` | Historial de cambios |
| POST | `/api/v1/audits/{id}/reports` | Generar reporte XLSX/DOCX |
| GET | `/api/v1/dashboard/summary` | Métricas del dashboard |

---

## Tests

```bash
pytest tests/ -v
```
