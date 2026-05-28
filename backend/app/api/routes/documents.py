"""
Rutas para documentos asociados a una auditoría.
POST /api/v1/audits/{id}/documents — sube PDF (multipart/form-data)
"""

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import CurrentUID, get_document_service
from app.core.responses import created, ok
from app.schemas.document import DocumentOut
from app.services.document_service import DocumentService

router = APIRouter(prefix="/audits/{audit_id}/documents", tags=["documents"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    audit_id: str,
    uid: CurrentUID,
    file: UploadFile = File(...),
    svc: DocumentService = Depends(get_document_service),
):
    content = await file.read()
    doc = await svc.upload(
        audit_id=audit_id,
        owner_id=uid,
        filename=file.filename or "document.pdf",
        content=content,
        content_type=file.content_type or "application/pdf",
    )
    return created(_doc_out(doc))


@router.get("")
async def list_documents(
    audit_id: str,
    uid: CurrentUID,
    svc: DocumentService = Depends(get_document_service),
):
    docs = await svc.list_by_audit(audit_id, uid)
    return ok([_doc_out(d) for d in docs])


@router.get("/{doc_id}")
async def get_document(
    audit_id: str,
    doc_id: str,
    uid: CurrentUID,
    svc: DocumentService = Depends(get_document_service),
):
    doc = await svc.get_by_id(audit_id, doc_id, uid)
    return ok(_doc_out(doc))


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    audit_id: str,
    doc_id: str,
    uid: CurrentUID,
    svc: DocumentService = Depends(get_document_service),
):
    await svc.delete(audit_id, doc_id, uid)


def _doc_out(doc) -> dict:
    return DocumentOut.model_validate(
        doc.to_firestore() | {"id": doc.id}
    ).model_dump(by_alias=True)
