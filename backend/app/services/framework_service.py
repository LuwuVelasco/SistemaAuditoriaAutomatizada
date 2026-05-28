"""Servicio de catálogos normativos (read-only)."""

from typing import List

from app.models.framework import FrameworkControl
from app.repositories.framework_repository import FrameworkRepository


class FrameworkService:
    VALID_FRAMEWORKS = {"cobit", "coso", "rgsi"}

    def __init__(self, repo: FrameworkRepository):
        self._repo = repo

    def _validate(self, framework: str) -> str:
        fw = framework.lower()
        if fw not in self.VALID_FRAMEWORKS:
            raise ValueError(f"Framework '{framework}' no soportado. Use: cobit, coso, rgsi.")
        return fw

    async def list_controls(self, framework: str) -> List[FrameworkControl]:
        return await self._repo.list_controls(self._validate(framework))

    async def get_control(self, framework: str, control_id: str) -> FrameworkControl | None:
        return await self._repo.get_control(self._validate(framework), control_id)

    async def search(self, framework: str, keyword: str) -> List[FrameworkControl]:
        return await self._repo.search_by_keyword(self._validate(framework), keyword.lower())
