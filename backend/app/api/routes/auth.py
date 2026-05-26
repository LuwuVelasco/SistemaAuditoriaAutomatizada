"""
Rutas de autenticación y perfil de usuario.
"""

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import CurrentUID, CurrentUser, DB
from app.core.config import settings
from app.core.responses import ok
from app.models.user import User
from app.utils.timestamps import utcnow_iso

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(body: LoginRequest):
    """
    Autentica con email + password usando Firebase Auth REST API.
    Retorna el idToken para usar como Bearer en el resto de endpoints.
    """
    if not settings.FIREBASE_WEB_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FIREBASE_WEB_API_KEY no configurada en el servidor.",
        )

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_WEB_API_KEY}"

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={
            "email": body.email,
            "password": body.password,
            "returnSecureToken": True,
        })

    if resp.status_code != 200:
        error = resp.json().get("error", {}).get("message", "Credenciales inválidas")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)

    data = resp.json()
    return ok({
        "idToken": data["idToken"],
        "email": data["email"],
        "uid": data["localId"],
        "expiresIn": data.get("expiresIn", "3600"),
        "hint": "Usa idToken como: Bearer <idToken> en el header Authorization",
    })


@router.get("/me")
async def get_me(user: CurrentUser):
    """Retorna el perfil completo del usuario autenticado."""
    return ok(user.model_dump(by_alias=True))


@router.put("/profile")
async def update_profile(
    payload: dict,
    uid: CurrentUID,
    db: DB,
):
    """Actualiza campos editables del perfil: displayName, photoURL, role."""
    ALLOWED = {"displayName", "photoURL", "role"}
    update_data = {k: v for k, v in payload.items() if k in ALLOWED}
    update_data["updatedAt"] = utcnow_iso()

    ref = db.collection("users").document(uid)
    doc = await ref.get()
    if not doc.exists:
        update_data.setdefault("createdAt", utcnow_iso())
        await ref.set(update_data, merge=True)
    else:
        await ref.update(update_data)

    updated = await ref.get()
    user = User.from_firestore(uid, updated.to_dict())
    return ok(user.model_dump(by_alias=True))
