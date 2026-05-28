"""
Ruta de chat con documentos de auditoría.
POST /api/v1/audits/{audit_id}/chat
"""

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUID, get_chat_service
from app.core.responses import ok
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/audits/{audit_id}/chat", tags=["chat"])


@router.post("")
async def chat(
    audit_id: str,
    body: ChatRequest,
    uid: CurrentUID,
    svc: ChatService = Depends(get_chat_service),
):
    answer = await svc.chat(
        audit_id=audit_id,
        owner_id=uid,
        question=body.question,
        history=body.history,
    )
    return ok(ChatResponse(answer=answer).model_dump())
