"""Modelo de dominio: Usuario."""

from pydantic import BaseModel, Field


class UserStats(BaseModel):
    audits: int = 0
    approved_findings: int = Field(default=0, alias="approvedFindings")
    model_config = {"populate_by_name": True}


class User(BaseModel):
    """Representa users/{uid} en Firestore."""

    uid: str
    name: str
    email: str
    created_at: str = Field(alias="createdAt")
    stats: UserStats = Field(default_factory=UserStats)

    model_config = {"populate_by_name": True}

    def to_firestore(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "createdAt": self.created_at,
            "stats": {
                "audits": self.stats.audits,
                "approvedFindings": self.stats.approved_findings,
            },
        }

    @classmethod
    def from_firestore(cls, uid: str, data: dict) -> "User":
        stats_raw = data.get("stats", {})
        return cls(
            uid=uid,
            name=data.get("name", ""),
            email=data.get("email", ""),
            createdAt=data.get("createdAt", ""),
            stats=UserStats(
                audits=stats_raw.get("audits", 0),
                approvedFindings=stats_raw.get("approvedFindings", 0),
            ),
        )
