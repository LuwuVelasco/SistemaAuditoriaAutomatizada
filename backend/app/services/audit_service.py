"""Servicio de lógica de negocio para auditorías."""

from typing import List, Optional

from loguru import logger

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.audit import Audit
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditCreate, AuditUpdate
from app.utils.enums import AuditStatus
from app.utils.helpers import generate_id
from app.utils.timestamps import utcnow_iso


class AuditService:
    def __init__(self, repo: AuditRepository):
        self._repo = repo

    async def create(self, data: AuditCreate, owner_id: str) -> Audit:
        audit_id = generate_id("aud-")
        audit = Audit(
            id=audit_id,
            entity=data.entity,
            type=data.type,
            city=data.city,
            period=data.period,
            alcance=data.alcance,
            frameworks=[f for f in data.frameworks],
            ownerId=owner_id,
            createdAt=utcnow_iso(),
        )
        result = await self._repo.create(audit)
        logger.info(f"Auditoría creada: {audit_id} ({data.entity}) por {owner_id}")
        return result

    async def get_by_id(self, audit_id: str, owner_id: str) -> Audit:
        audit = await self._repo.get_by_id(audit_id)
        if audit is None:
            raise NotFoundError("Auditoría", audit_id)
        if audit.owner_id != owner_id:
            raise ForbiddenError("Acceso denegado.")
        return audit

    async def list_by_owner(self, owner_id: str) -> List[Audit]:
        return await self._repo.list_by_owner(owner_id)

    async def update(self, audit_id: str, data: AuditUpdate, owner_id: str) -> Audit:
        await self.get_by_id(audit_id, owner_id)   # verifica owner

        update_fields: dict = {}
        if data.entity is not None:
            update_fields["entity"] = data.entity
        if data.type is not None:
            update_fields["type"] = data.type
        if data.city is not None:
            update_fields["city"] = data.city
        if data.period is not None:
            update_fields["period"] = data.period
        if data.status is not None:
            update_fields["status"] = data.status.value
        if data.progress is not None:
            update_fields["progress"] = data.progress
        if data.frameworks is not None:
            update_fields["frameworks"] = [f.value for f in data.frameworks]
        if data.alcance is not None:
            update_fields["alcance"] = data.alcance
        if data.maturity is not None:
            update_fields["maturity"] = data.maturity

        updated = await self._repo.update(audit_id, update_fields)
        logger.info(f"Auditoría actualizada: {audit_id}")
        return updated

    async def delete(self, audit_id: str, owner_id: str) -> None:
        await self.get_by_id(audit_id, owner_id)
        await self._repo.delete(audit_id)
        logger.info(f"Auditoría eliminada: {audit_id}")

    async def set_status(self, audit_id: str, status: AuditStatus, progress: int) -> None:
        """Actualiza estado y progreso sin verificar owner (uso interno)."""
        await self._repo.update(audit_id, {
            "status": status.value,
            "progress": progress,
        })
