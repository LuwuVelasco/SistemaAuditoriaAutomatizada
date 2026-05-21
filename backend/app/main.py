"""
FastAPI Application — Sistema de Auditoría Automatizada RAG.
Expone endpoints REST y WebSocket para el frontend React.
"""

from __future__ import annotations
import asyncio
import shutil
from pathlib import Path
from typing import Any
import sys

# Forzar salida en UTF-8 para evitar crashes con acentos en la consola de Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .config import CORS_ORIGINS, UPLOADS_DIR, SALIDAS_DIR
from .models import (
    IniciarAuditoriaRequest,
    DocumentoInfo,
    ResultadoAuditoria,
    EstadoAuditoria,
)
from .websocket_manager import ws_manager
from .rag.auditor import auditor_rag


# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(
    title="Sistema de Auditoría Automatizada RAG",
    description="API para auditoría de sistemas con RAG, COBIT y COSO",
    version="1.0.0",
)

# CORS para React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global
_resultado_auditoria: ResultadoAuditoria | None = None
_auditoria_en_curso: bool = False


# ============================================================
# ENDPOINTS — DOCUMENTOS
# ============================================================

@app.post("/api/upload")
async def upload_documentos(files: list[UploadFile] = File(...)):
    """Subir uno o más documentos PDF/DOCX."""
    archivos_subidos: list[dict[str, Any]] = []

    for file in files:
        if not file.filename:
            continue

        # Validar extensión
        extension = Path(file.filename).suffix.lower()
        if extension not in {".pdf", ".docx", ".doc"}:
            continue

        # Guardar archivo
        ruta_destino = UPLOADS_DIR / file.filename
        with open(ruta_destino, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        archivos_subidos.append({
            "nombre": file.filename,
            "tamano": len(content),
            "tipo": extension.replace(".", ""),
            "ruta": str(ruta_destino),
        })

    return {
        "mensaje": f"{len(archivos_subidos)} archivo(s) subido(s) exitosamente",
        "archivos": archivos_subidos,
    }


@app.get("/api/documentos")
async def listar_documentos():
    """Lista todos los documentos subidos."""
    extensiones = {".pdf", ".docx", ".doc"}
    documentos: list[dict[str, Any]] = []

    if UPLOADS_DIR.exists():
        for f in sorted(UPLOADS_DIR.iterdir()):
            if f.is_file() and f.suffix.lower() in extensiones:
                documentos.append({
                    "nombre": f.name,
                    "tamano": f.stat().st_size,
                    "tipo": f.suffix.lower().replace(".", ""),
                    "ruta": str(f),
                })

    return {"documentos": documentos, "total": len(documentos)}


@app.delete("/api/documentos/{nombre}")
async def eliminar_documento(nombre: str):
    """Elimina un documento subido."""
    ruta = UPLOADS_DIR / nombre
    if ruta.exists():
        ruta.unlink()
        return {"mensaje": f"Documento '{nombre}' eliminado"}
    raise HTTPException(status_code=404, detail=f"Documento '{nombre}' no encontrado")


@app.delete("/api/documentos")
async def eliminar_todos_documentos():
    """Elimina todos los documentos subidos."""
    if UPLOADS_DIR.exists():
        for f in UPLOADS_DIR.iterdir():
            if f.is_file():
                f.unlink()
    return {"mensaje": "Todos los documentos eliminados"}


# ============================================================
# ENDPOINTS — AUDITORÍA
# ============================================================

@app.post("/api/auditoria/iniciar")
async def iniciar_auditoria(request: IniciarAuditoriaRequest | None = None):
    """Inicia el proceso de auditoría en background."""
    global _auditoria_en_curso, _resultado_auditoria

    if _auditoria_en_curso:
        raise HTTPException(
            status_code=409,
            detail="Ya hay una auditoría en curso. Espere a que termine."
        )

    # Verificar que hay documentos
    docs = list(UPLOADS_DIR.glob("*.pdf")) + list(UPLOADS_DIR.glob("*.docx"))
    if not docs:
        raise HTTPException(
            status_code=400,
            detail="No hay documentos subidos. Suba al menos un PDF o DOCX."
        )

    _auditoria_en_curso = True
    _resultado_auditoria = None

    # Limpiar salidas anteriores
    if SALIDAS_DIR.exists():
        for f in SALIDAS_DIR.iterdir():
            if f.is_file():
                f.unlink()

    # Ejecutar en background
    asyncio.create_task(
        _ejecutar_auditoria_background(
            nombre_grupo=request.nombre_grupo if request else None,
            integrantes=request.integrantes if request else None,
            alcance=request.alcance if request else None,
        )
    )

    return {
        "mensaje": "Auditoría iniciada",
        "estado": EstadoAuditoria.PROCESANDO_DOCUMENTOS.value,
    }


async def _ejecutar_auditoria_background(
    nombre_grupo: str | None = None,
    integrantes: list[str] | None = None,
    alcance: str | None = None,
):
    """Ejecuta la auditoría en una tarea background."""
    global _auditoria_en_curso, _resultado_auditoria

    try:
        _resultado_auditoria = await auditor_rag.ejecutar_auditoria_completa(
            nombre_grupo=nombre_grupo,
            integrantes=integrantes,
            alcance=alcance,
        )
    except Exception as e:
        print(f"❌ Error en auditoría: {e}")
        await ws_manager.send_error(str(e))
    finally:
        _auditoria_en_curso = False


@app.get("/api/auditoria/estado")
async def estado_auditoria():
    """Retorna el estado actual de la auditoría."""
    return {
        "en_curso": _auditoria_en_curso,
        "estado": auditor_rag.estado.value,
        "tiene_resultados": _resultado_auditoria is not None,
    }


@app.get("/api/auditoria/hallazgos")
async def obtener_hallazgos():
    """Retorna los hallazgos encontrados."""
    if _resultado_auditoria is None:
        return {"hallazgos": [], "total": 0}

    return {
        "hallazgos": [h.model_dump() for h in _resultado_auditoria.hallazgos],
        "total": len(_resultado_auditoria.hallazgos),
        "resumen_riesgos": _resultado_auditoria.resumen_riesgos,
    }


@app.get("/api/auditoria/contexto")
async def obtener_contexto():
    """Retorna el contexto de la entidad extraído."""
    if _resultado_auditoria is None:
        return {"contexto": None}

    return {"contexto": _resultado_auditoria.contexto.model_dump()}


@app.get("/api/auditoria/resultados")
async def obtener_resultados():
    """Retorna el resultado completo de la auditoría."""
    if _resultado_auditoria is None:
        raise HTTPException(
            status_code=404,
            detail="No hay resultados de auditoría disponibles"
        )

    return _resultado_auditoria.model_dump()


@app.get("/api/auditoria/coso")
async def obtener_coso():
    """Retorna la evaluación COSO."""
    if _resultado_auditoria is None:
        return {"componentes": []}

    return {
        "componentes": [c.model_dump() for c in _resultado_auditoria.componentes_coso]
    }


# ============================================================
# ENDPOINTS — EXPORTACIÓN / DESCARGA
# ============================================================

@app.get("/api/exportar/archivos")
async def listar_archivos_generados():
    """Lista los archivos generados disponibles para descarga."""
    archivos: list[dict[str, Any]] = []

    if SALIDAS_DIR.exists():
        for f in sorted(SALIDAS_DIR.iterdir()):
            if f.is_file():
                archivos.append({
                    "nombre": f.name,
                    "tamano": f.stat().st_size,
                    "tipo": f.suffix.lower().replace(".", ""),
                })

    return {"archivos": archivos}


@app.get("/api/exportar/{nombre_archivo}")
async def descargar_archivo(nombre_archivo: str):
    """Descarga un archivo generado."""
    ruta = SALIDAS_DIR / nombre_archivo

    if not ruta.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Archivo '{nombre_archivo}' no encontrado"
        )

    # Determinar content type
    content_types = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".json": "application/json",
    }
    content_type = content_types.get(ruta.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=str(ruta),
        filename=nombre_archivo,
        media_type=content_type,
    )


# ============================================================
# WEBSOCKET — PROGRESO EN TIEMPO REAL
# ============================================================

@app.websocket("/ws/progreso")
async def websocket_progreso(websocket: WebSocket):
    """WebSocket para recibir actualizaciones de progreso en tiempo real."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Mantener la conexión abierta esperando mensajes del cliente
            data = await websocket.receive_text()
            # El cliente puede enviar "ping" para mantener la conexión
            if data == "ping":
                await websocket.send_text('{"tipo": "pong"}')
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
async def health_check():
    """Health check del sistema."""
    return {
        "status": "ok",
        "gemini_disponible": True,
        "documentos_subidos": len(list(UPLOADS_DIR.glob("*"))) if UPLOADS_DIR.exists() else 0,
        "archivos_generados": len(list(SALIDAS_DIR.glob("*"))) if SALIDAS_DIR.exists() else 0,
    }
